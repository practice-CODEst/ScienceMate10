
import { useEffect, useState } from 'react'
import api from '../api'

export default function Quiz({ subject = 'Science', lesson: selectedLesson }) {
  const [lesson, setLesson] = useState(selectedLesson || 'Laws of Motion')
  const [quiz, setQuiz] = useState(null)
  const [answers, setAnswers] = useState({})
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setLesson(selectedLesson || 'Laws of Motion')
    setQuiz(null)
    setResult(null)
    setAnswers({})
    setError('')
  }, [selectedLesson])

  async function generateQuiz() {
    setLoading(true)
    setError('')
    setQuiz(null)
    setResult(null)
    setAnswers({})

    try {
      const response = await api.post('/quiz', {
        lesson: lesson.trim(),
        subject,
        count: 5,
      })
      setQuiz(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Quiz generation failed.')
    } finally {
      setLoading(false)
    }
  }

  async function submitQuiz() {
    setLoading(true)
    setError('')

    try {
      const response = await api.post('/quiz/submit', {
        quiz_id: quiz.quiz_id,
        answers,
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Quiz submission failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="card border-0 shadow-sm rounded-4 p-4 mb-4">
      <h4 className="fw-bold">Practice Quiz</h4>
      <p className="text-secondary">
        Generate five MCQs from {lesson}.
      </p>

      <p className="fw-semibold">Chapter: {lesson}</p>

      <button
        className="btn btn-primary mb-3"
        disabled={loading}
        onClick={generateQuiz}
      >
        {loading ? 'Please wait...' : 'Generate Quiz'}
      </button>

      {error && <p className="text-danger">{error}</p>}

      {quiz && !result && (
        <>
          {quiz.questions.map((q, i) => (
            <div className="border rounded-3 p-3 mb-3" key={i}>
              <p className="fw-semibold">{i + 1}. {q.question}</p>
              {Object.entries(q.options).map(([key, value]) => (
                <label className="d-block mb-2" key={key}>
                  <input
                    className="form-check-input me-2"
                    type="radio"
                    name={`question-${i}`}
                    checked={answers[String(i)] === key}
                    onChange={() =>
                      setAnswers(prev => ({ ...prev, [String(i)]: key }))
                    }
                  />
                  {key}. {value}
                </label>
              ))}
            </div>
          ))}

          <button
            className="btn btn-success"
            disabled={
              loading ||
              Object.keys(answers).length !== quiz.questions.length
            }
            onClick={submitQuiz}
          >
            Submit Quiz
          </button>
        </>
      )}

      {result && (
        <div className="mt-3">
          <h5 className="fw-bold">
            Score: {result.score}% ({result.correct}/{result.total})
          </h5>
          <p className={result.passed ? 'text-success' : 'text-danger'}>
            {result.message}
          </p>
          {result.feedback.map((item, i) => (
            <div className="border-bottom py-3" key={i}>
              <p className="fw-semibold">{item.question}</p>
              <p className="mb-1">Correct answer: {item.correct_answer}</p>
              <p className="text-secondary mb-0">{item.explanation}</p>
            </div>
          ))}
          <button
            className="btn btn-outline-primary mt-3"
            disabled={loading}
            onClick={generateQuiz}
          >
            Try Again
          </button>
        </div>
      )}
    </section>
  )
}
