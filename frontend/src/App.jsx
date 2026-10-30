
import { useEffect, useState } from 'react'
import api from './api'
import Quiz from './components/Quiz'
import './App.css'

const chapters = [
  'Laws of Motion','Optics','Thermal Physics','Electricity','Acoustics',
  'Nuclear Physics','Atoms and Molecules','Periodic Classification of Elements',
  'Solutions','Types of Chemical Reactions','Carbon and its Compounds',
  'Plant Anatomy and Plant Physiology','Structural Organisation of Animals',
  'Transportation in Plants and Circulation in Animals','Nervous System',
  'Plant and Animal Hormones','Reproduction in Plants and Animals','Genetics',
  'Origin and Evolution of Life','Breeding and Biotechnology',
  'Health and Diseases','Environmental Management','Visual Communication'
]

export default function App() {
  const subject = 'Science'
  const [lesson, setLesson] = useState(chapters[0])
  const [view, setView] = useState('Dashboard')
  const [askQuestion, setAskQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState([])
  const [asking, setAsking] = useState(false)
  const [question, setQuestion] = useState('')
  const [message, setMessage] = useState('')
  const [apiStatus, setApiStatus] = useState('Checking backend...')
  const [history, setHistory] = useState([])

  useEffect(() => {
    api.get('/health').then(() => setApiStatus('Backend connected'))
      .catch(() => setApiStatus('Backend offline'))
  }, [])

  async function askTutor() {
    setAsking(true)
    setAnswer('')
    setSources([])
    try {
      const { data } = await api.post('/ask', {
        question: askQuestion.trim(), subject, lesson
      })
      setAnswer(data.answer)
      setSources(data.sources || [])
    } catch (e) {
      setAnswer(e.response?.data?.detail || 'Could not get an answer.')
    } finally {
      setAsking(false)
    }
  }

  async function saveProgress() {
    setMessage('Saving progress...')
    try {
      await api.post('/progress', {
        subject, lesson: question.trim() || lesson,
        completed: false, quiz_score: 0
      })
      setMessage('Progress saved successfully!')
      const { data } = await api.get('/progress')
      setHistory(data)
    } catch {
      setMessage('Could not save progress. Check backend.')
    }
  }

  const tutor = (
    <section className="panel">
      <h4>Ask your AI tutor</h4>
      <p className="muted">Answers are grounded in your selected textbook chapter.</p>
      <textarea className="form-control mb-3" rows="3" value={askQuestion}
        onChange={e => setAskQuestion(e.target.value)}
        placeholder="Example: What is inertia?" />
      <button className="btn btn-primary" disabled={!askQuestion.trim() || asking}
        onClick={askTutor}>{asking ? 'Finding answer...' : 'Ask ScienceMate AI'}</button>
      {answer && <div className="mt-4">
        <h5>Answer</h5><p className="answer">{answer}</p>
        <h6>Textbook references</h6>
        <ul className="source-list">{sources.filter((s, i, a) =>
          a.findIndex(x => x.source === s.source && x.pdf_page === s.pdf_page) === i
        ).map((s, i) => <li key={i}>{s.chapter} — Textbook page {s.textbook_page} (PDF page {s.pdf_page})</li>)}</ul>
      </div>}
    </section>
  )

  const progress = (
    <section className="panel">
      <h4>Track your learning</h4>
      <p className="muted">Selected chapter: {lesson}</p>
      <textarea className="form-control mb-3" rows="2" value={question}
        onChange={e => setQuestion(e.target.value)}
        placeholder="Optional: enter a progress note" />
      <button className="btn btn-primary" disabled={message === 'Saving progress...'}
        onClick={saveProgress}>Save learning progress</button>
      {message && <p className="mt-3 mb-0">{message}</p>}

      <h5 className="mt-4">Saved Learning History</h5>
      {history.length === 0 ? <p>No history loaded yet.</p> : (
        <ul>
          {history.map((item, i) => (
            <li key={i}>
              <strong>{item.lesson}</strong> — {item.quiz_score}% —
              {item.completed ? ' Completed' : ' In progress'}
              <small className="d-block text-muted">{item.updated_at}</small>
            </li>
          ))}
        </ul>
      )}

    </section>
  )

  return <div className="app container-fluid"><div className="row">
    <aside className="sidebar col-md-3 col-lg-2">
      <div className="brand">ScienceMate AI</div>
      <p>TN State Board · Class 10</p>
      {['Dashboard','AI Tutor','Practice Quiz','Progress'].map(item =>
        <button key={item} className={`nav-link ${view === item ? 'active' : ''}`}
          onClick={() => setView(item)}>{item}</button>)}
      <hr />
      <p className="status">{apiStatus}</p>
    </aside>

    <main className="main-content col-md-9 col-lg-10">
      <h1 className="page-title">{view}</h1>
      <p className="muted mb-4">Your textbook-based Science learning companion.</p>

      <section className="panel">
        <h4>Choose a chapter</h4>
        <select className="form-select" value={lesson} onChange={e => {
          setLesson(e.target.value); setAnswer(''); setSources([])
        }}>
          {chapters.map(c => <option key={c}>{c}</option>)}
        </select>
        <p className="muted mt-2 mb-0">Selected: {lesson}</p>
      </section>

      {view === 'Dashboard' && <>
        <section className="panel"><h4>Welcome back!</h4>
          <p className="muted mb-0">Learn one chapter at a time with textbook-grounded answers and practice quizzes.</p>
        </section>
        {tutor}
        <Quiz subject={subject} lesson={lesson} />
        {progress}
      </>}
      {view === 'AI Tutor' && tutor}
      {view === 'Practice Quiz' && <Quiz subject={subject} lesson={lesson} />}
      {view === 'Progress' && progress}
    </main>
  </div></div>
}
