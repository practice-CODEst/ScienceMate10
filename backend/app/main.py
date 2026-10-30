import os
import sqlite3
from pathlib import Path

from app.rag import retrieve_text
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from pydantic import BaseModel, Field

from app.database import create_db, DB_PATH

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

app = FastAPI(title="ScienceMate AI API")
create_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "ScienceMate AI API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


class Progress(BaseModel):
    subject: str
    lesson: str
    completed: bool = False
    quiz_score: int = Field(default=0, ge=0)


@app.post("/progress")
def save_progress(progress: Progress):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """INSERT INTO learning_progress
            (subject, lesson, completed, quiz_score, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (
                progress.subject,
                progress.lesson,
                int(progress.completed),
                progress.quiz_score,
            ),
        )
    return {"message": "Progress saved successfully"}


@app.get("/progress")
def get_progress():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT subject, lesson, completed, quiz_score, updated_at
            FROM learning_progress
            ORDER BY updated_at DESC"""
        ).fetchall()

    return [dict(row) for row in rows]




class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    subject: str = "Science"
    lesson: str | None = None


@app.post("/ask")
def ask_ai(request: AskRequest):
    if client is None:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key is not configured",
        )

    try:
        sources = retrieve_text(
            request.question,
            request.subject,
            limit=4,
            lesson=request.lesson,
    )

    except Exception as exc:
        print("Retrieval error:", type(exc).__name__, str(exc))
        raise HTTPException(
            status_code=404,
            detail="Textbook index unavailable. Index this subject first.",
        )

    if not sources:
        raise HTTPException(
            status_code=404,
            detail="No relevant textbook content found.",
        )

    context = "\n\n".join(
    f"[{item['chapter']} | Textbook page "
    f"{item['textbook_page']} | PDF page {item['page']}]\n"
    f"{item['text']}"
    for item in sources
        )

    prompt = f"""
You are ScienceMate AI, a Class 10 Tamil Nadu State Board Science tutor.
Answer the student's question using ONLY the textbook context below.
Explain clearly in English, using simple words.
If the context does not contain the answer, say so honestly.
Do not invent textbook facts or page references.

TEXTBOOK CONTEXT:
{context}

STUDENT QUESTION:
{request.question}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
        )

        if not response.text:
            raise HTTPException(
                status_code=502,
                detail="Gemini returned an empty answer",
            )

        references = [
    {
        "chapter": item["chapter"],
        "textbook_page": item["textbook_page"],
        "pdf_page": item["page"],
        "source": item["source"],
    }
    for item in sources
               ]

        return {
            "answer": response.text,
            "subject": request.subject,
            "sources": references,
        }

    except HTTPException:
        raise
    except Exception as exc:
        print("Gemini error:", type(exc).__name__, str(exc))
        raise HTTPException(
            status_code=502,
            detail="Gemini request failed. Check backend terminal.",
        )


import json

quizzes = {}


class QuizRequest(BaseModel):
    lesson: str = Field(min_length=1, max_length=150)
    subject: str = "Science"
    count: int = Field(default=5, ge=3, le=10)


class QuizSubmit(BaseModel):
    quiz_id: str
    answers: dict[str, str]


@app.post("/quiz")
def generate_quiz(request: QuizRequest):
    if client is None:
        raise HTTPException(500, "Gemini API key is missing")

    try:
        sources = retrieve_text(
    request.lesson,
    request.subject,
    limit=4,
    lesson=request.lesson,
)
        if not sources:
            raise HTTPException(404, "No textbook content found")

        context = "\n".join(
            item["text"] for item in sources
        )
        prompt = f"""
Create {request.count} Class 10 MCQs using ONLY this textbook.
Lesson: {request.lesson}
Return JSON only in this format:
{{"questions":[{{"question":"...","options":{{"A":"...","B":"...","C":"...","D":"..."}}, "answer":"A","explanation":"..."}}]}}
Each answer must be A, B, C or D.
TEXTBOOK:
{context}
"""
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        data = json.loads(response.text)
        questions = data["questions"][:request.count]

        if len(questions) < 3:
            raise ValueError("Not enough questions generated")

        quiz_id = str(len(quizzes) + 1) + "-" + str(id(data))
        quizzes[quiz_id] = {
            "lesson": request.lesson,
            "subject": request.subject,
            "questions": questions,
        }

        return {
            "quiz_id": quiz_id,
            "lesson": request.lesson,
            "questions": [
                {"question": q["question"], "options": q["options"]}
                for q in questions
            ],
        }
    except HTTPException:
        raise
    except Exception as exc:
        print("Quiz error:", type(exc).__name__, str(exc))
        raise HTTPException(502, "Quiz generation failed")


@app.post("/quiz/submit")
def submit_quiz(submission: QuizSubmit):
    quiz = quizzes.get(submission.quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz expired; generate a new quiz")

    questions = quiz["questions"]
    correct = sum(
        submission.answers.get(str(i), "").upper()
        == q["answer"].upper()
        for i, q in enumerate(questions)
    )
    score = round(correct * 100 / len(questions))
    passed = score >= 70

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """INSERT INTO learning_progress
            (subject, lesson, completed, quiz_score)
            VALUES (?, ?, ?, ?)""",
            (quiz["subject"], quiz["lesson"], int(passed), score),
        )

    result = {
        "score": score,
        "correct": correct,
        "total": len(questions),
        "passed": passed,
        "message": "Passed!" if passed else "Keep practising!",
        "feedback": [
            {
                "question": q["question"],
                "correct_answer": q["answer"],
                "explanation": q.get("explanation", ""),
                "your_answer": submission.answers.get(str(i), ""),
            }
            for i, q in enumerate(questions)
        ],
    }
    del quizzes[submission.quiz_id]
    return result
