# ScienceMate10 – AI-Powered Science Learning Assistant

ScienceMate10 is a full-stack AI-powered learning application designed for Tamil Nadu State Board Class 10 Science students. It enables students to ask textbook-related questions, practice AI-generated quizzes, and monitor their learning progress.

## Features

- **AI Tutor:** Ask Science-related questions and receive AI-generated responses.
- **Textbook-Based Question Answering:** Retrieve relevant textbook content using Retrieval-Augmented Generation (RAG).
- **Vector Search:** Use ChromaDB and Sentence Transformers to find relevant textbook content.
- **Source References:** Display available textbook source and page information with answers.
- **AI-Generated Quizzes:** Generate multiple-choice questions using retrieved textbook context.
- **Quiz Scoring:** Calculate quiz scores and determine pass or fail using a 70% pass threshold.
- **Progress Tracking:** Store learning progress and quiz results using SQLite.

## Tech Stack

| Component | Technologies |
|---|---|
| Frontend | React, Vite, Bootstrap 5, Axios |
| Backend | Python, FastAPI |
| AI Integration | Google Gemini API |
| RAG | ChromaDB, Sentence Transformers, PyMuPDF |
| Database | SQLite |

## Project Structure

```text
ScienceMate10/
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- database.py
|   |   `-- rag.py
|   `-- requirements.txt
|-- frontend/
|   |-- src/
|   |-- package.json
|   `-- package-lock.json
|-- textbooks/       (local textbook files)
|-- data/            (local database and vector index)
|-- .gitignore
`-- README.md
```

## Run Locally

### 1. Backend Setup

From the project root:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a `.env` file inside the `backend` directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Replace the example value with your own Gemini API key. Never commit your `.env` file to GitHub.

Start the backend:

```powershell
uvicorn app.main:app --reload
```

### 2. Local API Endpoints

When the backend is running:

- Backend: http://127.0.0.1:8000
- API Documentation: http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/health

### 3. Frontend Setup

Open a second terminal from the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL displayed by Vite in your browser.

## Textbook Retrieval

The current textbook retrieval workflow is configured for Tamil Nadu State Board Class 10 Science.

Textbook-based answers and quizzes depend on:
- A valid Science textbook index being available in ChromaDB.
- The Google Gemini API key being configured correctly.
- Relevant textbook content being retrieved for the question.

The textbook PDF and generated vector database files are excluded from this Git repository.

## Security

- Store API keys and sensitive configuration in environment variables.
- Do not commit `.env` files, virtual environments, local databases, generated vector indexes, or textbook PDFs.
- Use textbook files that you have permission to process and distribute.

## Project Scope

ScienceMate10 currently focuses on Tamil Nadu State Board Class 10 Science. The application includes AI-powered question answering, quiz generation, quiz evaluation, and learning progress tracking. Textbook-based functionality requires a valid local ChromaDB index.
