import { useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  History,
  LayoutDashboard,
  Loader2,
  LogOut,
  Rocket,
  ShieldAlert,
  ShieldCheck,
} from 'lucide-react'
import { apiUrl } from './api'

const AUTH_KEY = 'claimguard_session'
const DEMO_EMAIL = 'demo@college.edu'
const DEMO_PASS = 'demo123'

const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'verify', label: 'Verify Claims', icon: ShieldCheck },
  { id: 'history', label: 'History', icon: History },
  { id: 'upcoming', label: 'Upcoming', icon: Rocket },
]

const UPCOMING = [
  {
    title: 'Black-box detector baselines',
    detail: 'Compare SelfCheckGPT-style consistency, NLI entailment, and LLM-as-judge against this span detector (Topic 2 goal 2).',
  },
  {
    title: 'RAGTruth fine-tuning + F1',
    detail: 'Train DeBERTa/ModernBERT on RAGTruth span labels and report precision/recall/F1 and AUROC (Topic 2 goal 3).',
  },
  {
    title: 'Benchmark failure-mode analysis',
    detail: 'Evaluate on HaluEval / FaithBench / HalluLens and break errors by contradicted vs baseless.',
  },
  {
    title: 'Abstain / regenerate mitigation',
    detail: 'When hallucination rate is high, abstain or regenerate and measure faithfulness gain (Topic 2 goal 4).',
  },
]

const SAMPLE_QUERY = `What were the Q3 financial highlights?`

const SAMPLE_SOURCE = `Q3 revenue grew 12% year-over-year to $4.2 billion. Operating margin expanded to 18.5%. The board approved a $500 million share repurchase program. No material litigation was disclosed in the period.`

const SAMPLE_GEN = `Q3 revenue declined 12% year-over-year to $4.2 billion. Operating margin expanded to 18.5%. Management also announced a new AI product line launching next month. The board approved a $500 million share repurchase program.`

function loadSession() {
  try {
    return JSON.parse(localStorage.getItem(AUTH_KEY) || 'null')
  } catch {
    return null
  }
}

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState(DEMO_EMAIL)
  const [password, setPassword] = useState(DEMO_PASS)
  const [err, setErr] = useState('')

  function submit(e) {
    e.preventDefault()
    if (!email.trim() || !password.trim()) {
      setErr('Enter email and password.')
      return
    }
    const session = { email: email.trim(), at: Date.now() }
    localStorage.setItem(AUTH_KEY, JSON.stringify(session))
    onLogin(session)
  }

  return (
    <div className="min-h-full flex items-center justify-center p-6">
      <form onSubmit={submit} className="risk-tile warn w-full max-w-md p-7 slide-up">
        <div className="flex items-center gap-2 text-[var(--accent-2)] mono text-xs tracking-widest uppercase">
          <ShieldAlert size={16} /> Risk console
        </div>
        <h1 className="display text-3xl mt-3">ClaimGuard</h1>
        <p className="text-[var(--muted)] mt-2 text-sm">
          Authenticate to run span-level hallucination checks on your text.
        </p>
        <label className="block text-xs text-[var(--muted)] mt-6 mono">EMAIL</label>
        <input
          className="mt-1 w-full rounded-sm bg-black/40 border border-[var(--line)] px-3 py-2.5 text-sm"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          type="email"
        />
        <label className="block text-xs text-[var(--muted)] mt-4 mono">PASSWORD</label>
        <input
          className="mt-1 w-full rounded-sm bg-black/40 border border-[var(--line)] px-3 py-2.5 text-sm"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          type="password"
        />
        {err && <p className="mt-3 text-sm text-[var(--danger)]">{err}</p>}
        <button type="submit" className="mt-6 w-full bg-[var(--accent)] text-white py-2.5 text-sm font-semibold rounded-sm">
          Access console
        </button>
        <p className="mt-4 text-xs text-[var(--muted)] mono">
          {DEMO_EMAIL} / {DEMO_PASS}
        </p>
      </form>
    </div>
  )
}

function Shell({ page, setPage, children, badge, user, onLogout }) {
  return (
    <div className="min-h-full flex">
      <aside className="w-16 shrink-0 border-r border-[var(--line)] bg-[#080d16] flex flex-col items-center py-4 gap-2">
        <div className="mb-4 text-[var(--accent-2)]" title="ClaimGuard">
          <ShieldAlert size={22} />
        </div>
        {NAV.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            title={label}
            onClick={() => setPage(id)}
            className={`rail-btn w-11 h-11 rounded-sm flex items-center justify-center text-[var(--muted)] ${
              page === id ? 'active' : ''
            }`}
          >
            <Icon size={18} />
          </button>
        ))}
        <button
          title="Logout"
          onClick={onLogout}
          className="rail-btn mt-auto w-11 h-11 rounded-sm flex items-center justify-center text-[var(--muted)]"
        >
          <LogOut size={18} />
        </button>
      </aside>
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-12 border-b border-[var(--line)] bg-[#0d1422] px-5 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <h1 className="display text-sm tracking-wide">CLAIMGUARD</h1>
            <span className="text-[var(--muted)] text-xs truncate hidden sm:inline">
              {NAV.find((n) => n.id === page)?.label}
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs mono text-[var(--muted)]">
            <span className="text-[var(--accent-2)]">{badge}</span>
            <span className="hidden md:inline">{user?.email}</span>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-4 md:p-6">{children}</main>
      </div>
    </div>
  )
}

function Kpi({ label, value, tone }) {
  return (
    <div className={`risk-tile ${tone || ''} p-4`}>
      <p className="mono text-[10px] uppercase tracking-wider text-[var(--muted)]">{label}</p>
      <p className="display text-2xl mt-1 tabular-nums">{value}</p>
    </div>
  )
}

function spanClass(label) {
  if (label === 'SUPPORTED') return 'span-supported'
  if (label === 'CONTRADICTED') return 'span-contradicted'
  return 'span-baseless'
}

export default function App() {
  const [session, setSession] = useState(() => loadSession())
  const [page, setPage] = useState('dashboard')
  const [stats, setStats] = useState(null)
  const [history, setHistory] = useState([])
  const [query, setQuery] = useState('')
  const [source, setSource] = useState('')
  const [generated, setGenerated] = useState('')
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const badge = useMemo(() => {
    if (!stats) return 'OFFLINE'
    return stats.demo_mode ? 'DEMO HEURISTICS' : 'LIVE NLI'
  }, [stats])

  function loadSample() {
    setQuery(SAMPLE_QUERY)
    setSource(SAMPLE_SOURCE)
    setGenerated(SAMPLE_GEN)
    setResult(null)
    setError('')
  }

  function clearInputs() {
    setQuery('')
    setSource('')
    setGenerated('')
    setResult(null)
    setError('')
  }

  async function loadFileInto(setter) {
    return (e) => {
      const file = e.target.files?.[0]
      if (!file) return
      const reader = new FileReader()
      reader.onload = () => {
        setter(String(reader.result || ''))
        setResult(null)
      }
      reader.readAsText(file)
      e.target.value = ''
    }
  }

  async function refresh() {
    try {
      const [s, h] = await Promise.all([
        fetch(apiUrl('/api/stats')).then((r) => r.json()),
        fetch(apiUrl('/api/history')).then((r) => r.json()),
      ])
      setStats(s)
      setHistory(h)
      setError('')
    } catch {
      setError('Backend unreachable. Start API on port 8002 with DEMO_MODE=1.')
    }
  }

  useEffect(() => {
    if (session) refresh()
  }, [session])

  function logout() {
    localStorage.removeItem(AUTH_KEY)
    setSession(null)
    setPage('dashboard')
  }

  async function onVerify(e) {
    e.preventDefault()
    if (!source.trim() || !generated.trim()) {
      setError('Paste your retrieved context and generated answer (or load a sample).')
      return
    }
    setBusy(true)
    setError('')
    try {
      const res = await fetch(apiUrl('/api/verify'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query.trim(),
          source_text: source,
          generated_text: generated,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Verification failed')
      setResult(data)
      await refresh()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (!session) return <LoginPage onLogin={setSession} />

  return (
    <Shell page={page} setPage={setPage} badge={badge} user={session} onLogout={logout}>
      {error && (
        <div className="mb-4 rounded-sm border border-[var(--danger)]/50 bg-[var(--danger)]/10 px-3 py-2 text-sm">
          {error}
        </div>
      )}

      {page === 'dashboard' && (
        <div className="space-y-4 slide-up">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="display text-xl">Risk posture</h2>
              <p className="text-xs text-[var(--muted)] mt-1">
                Status only — paste and verify on the Verifier screen.
              </p>
            </div>
            <button
              onClick={() => setPage('verify')}
              className="inline-flex items-center gap-2 bg-[var(--accent-2)] text-black px-3 py-2 text-xs font-bold rounded-sm uppercase tracking-wide"
            >
              <ShieldCheck size={14} /> Open Verifier
            </button>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <Kpi label="Verifications" value={stats?.verifications ?? '—'} />
            <Kpi
              label="Avg hallucination"
              value={stats ? `${Math.round((stats.avg_hallucination_rate || 0) * 100)}%` : '—'}
              tone="warn"
            />
            <Kpi
              label="Avg support"
              value={stats ? `${Math.round((stats.avg_overall_score || 0) * 100)}%` : '—'}
            />
            <Kpi label="Flagged spans" value={stats?.flagged_spans_total ?? '—'} tone="danger" />
          </div>
          <section className="risk-tile p-4">
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-xs mono uppercase tracking-wider text-[var(--muted)]">Recent verdicts</h3>
              <AlertTriangle size={14} className="text-[var(--accent-2)]" />
            </div>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="text-[var(--muted)] text-left">
                  <tr>
                    <th className="pb-2 font-medium">Verdict</th>
                    <th className="pb-2 font-medium">Rate</th>
                    <th className="pb-2 font-medium">Flags</th>
                    <th className="pb-2 font-medium">When</th>
                  </tr>
                </thead>
                <tbody>
                  {(stats?.recent || []).length === 0 && (
                    <tr>
                      <td colSpan={4} className="py-3 text-[var(--muted)]">
                        No runs yet.
                      </td>
                    </tr>
                  )}
                  {(stats?.recent || []).map((r) => (
                    <tr key={r.id} className="border-t border-[var(--line)]">
                      <td className="py-2 pr-3 max-w-md">{r.verdict}</td>
                      <td className="py-2 mono text-[var(--accent-2)]">
                        {Math.round((r.hallucination_rate || 0) * 100)}%
                      </td>
                      <td className="py-2">{r.flagged_count}</td>
                      <td className="py-2 text-[var(--muted)]">
                        {r.created_at ? new Date(r.created_at).toLocaleString() : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}

      {page === 'verify' && (
        <div className="space-y-4 slide-up">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="display text-xl">Verify claims</h2>
              <p className="text-xs text-[var(--muted)] mt-1 max-w-2xl">
                Enter your own RAG triple: <strong>query</strong>, <strong>retrieved context</strong>, and{' '}
                <strong>generated answer</strong>. Fields start empty — nothing is hardcoded.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={loadSample}
                className="border border-[var(--line)] px-3 py-2 text-[10px] mono uppercase rounded-sm text-[var(--muted)] hover:text-white"
              >
                Load sample
              </button>
              <button
                type="button"
                onClick={clearInputs}
                className="border border-[var(--line)] px-3 py-2 text-[10px] mono uppercase rounded-sm text-[var(--muted)] hover:text-white"
              >
                Clear
              </button>
            </div>
          </div>

          <form onSubmit={onVerify} className="space-y-3">
            <div className="risk-tile p-4 space-y-2">
              <div className="flex items-center justify-between gap-2">
                <label className="mono text-[10px] uppercase text-[var(--muted)]">
                  Query (user question)
                </label>
                <label className="mono text-[10px] uppercase text-[var(--accent)] cursor-pointer">
                  Load .txt
                  <input type="file" accept=".txt,.md,.csv" className="hidden" onChange={loadFileInto(setQuery)} />
                </label>
              </div>
              <input
                className="w-full rounded-sm bg-black/35 border border-[var(--line)] px-3 py-2 text-sm"
                placeholder="e.g. What was Q3 revenue growth?"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>

            <div className="grid lg:grid-cols-2 gap-3">
              <div className="risk-tile p-4 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <label className="mono text-[10px] uppercase text-[var(--muted)]">
                    Retrieved context / source evidence
                  </label>
                  <label className="mono text-[10px] uppercase text-[var(--accent)] cursor-pointer">
                    Load .txt
                    <input type="file" accept=".txt,.md,.csv" className="hidden" onChange={loadFileInto(setSource)} />
                  </label>
                </div>
                <textarea
                  className="w-full min-h-52 rounded-sm bg-black/35 border border-[var(--line)] px-3 py-2 text-sm leading-relaxed"
                  placeholder="Paste retrieved passages or source document text here…"
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                />
              </div>
              <div className="risk-tile warn p-4 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <label className="mono text-[10px] uppercase text-[var(--muted)]">
                    Generated / RAG answer
                  </label>
                  <label className="mono text-[10px] uppercase text-[var(--accent)] cursor-pointer">
                    Load .txt
                    <input
                      type="file"
                      accept=".txt,.md,.csv"
                      className="hidden"
                      onChange={loadFileInto(setGenerated)}
                    />
                  </label>
                </div>
                <textarea
                  className="w-full min-h-52 rounded-sm bg-black/35 border border-[var(--line)] px-3 py-2 text-sm leading-relaxed"
                  placeholder="Paste the model-generated answer to check for hallucinations…"
                  value={generated}
                  onChange={(e) => setGenerated(e.target.value)}
                />
                <button
                  type="submit"
                  disabled={busy}
                  className="inline-flex items-center gap-2 bg-[var(--accent)] text-white px-3 py-2 text-xs font-bold rounded-sm uppercase tracking-wide disabled:opacity-60"
                >
                  {busy ? <Loader2 className="animate-spin" size={14} /> : <AlertTriangle size={14} />}
                  Detect hallucinations
                </button>
              </div>
            </div>
          </form>

          {result && (
            <section className="risk-tile danger p-4 space-y-3">
              <div className="flex flex-wrap gap-2 text-[10px] mono">
                {result.query ? (
                  <span className="border border-[var(--line)] px-2 py-1 max-w-full truncate">
                    QUERY {result.query}
                  </span>
                ) : null}
                <span className="border border-[var(--line)] px-2 py-1">
                  SCORE {Math.round(result.overall_score * 100)}%
                </span>
                <span className="border border-[var(--accent-2)]/50 text-[var(--accent-2)] px-2 py-1">
                  HALLUC {Math.round(result.hallucination_rate * 100)}%
                </span>
                <span className="border border-[var(--line)] px-2 py-1">
                  {result.flagged_spans}/{result.total_spans} FLAGGED
                </span>
                <span className="border border-[var(--line)] px-2 py-1">MODE {result.mode}</span>
              </div>
              <p className="text-sm font-semibold">{result.verdict}</p>
              <div className="text-sm leading-8">
                {(result.spans || []).map((s, i) => (
                  <span key={i} className={`${spanClass(s.label)} rounded-sm px-1 mr-1`} title={s.explanation}>
                    {s.text}
                  </span>
                ))}
              </div>
              <div className="grid md:grid-cols-3 gap-2">
                {(result.spans || []).map((s, i) => (
                  <div key={i} className="rounded-sm border border-[var(--line)] p-2 text-xs bg-black/20">
                    <div className="font-semibold mono">
                      {s.label} · {Math.round(s.confidence * 100)}%
                    </div>
                    <p className="mt-1 text-[var(--muted)]">{s.explanation}</p>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      )}

      {page === 'history' && (
        <div className="space-y-4 slide-up">
          <h2 className="display text-xl">Verification history</h2>
          <div className="risk-tile overflow-hidden">
            <table className="w-full text-xs">
              <thead className="text-left text-[var(--muted)] border-b border-[var(--line)] bg-black/25">
                <tr>
                  <th className="p-3 font-medium">Verdict</th>
                  <th className="p-3 font-medium">Rate</th>
                  <th className="p-3 font-medium">Flagged</th>
                  <th className="p-3 font-medium">When</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h) => (
                  <tr key={h.id} className="border-b border-[var(--line)]">
                    <td className="p-3 max-w-lg">{h.verdict}</td>
                    <td className="p-3 mono text-[var(--accent-2)]">
                      {Math.round((h.hallucination_rate || 0) * 100)}%
                    </td>
                    <td className="p-3">
                      {h.flagged_count}/{h.span_count}
                    </td>
                    <td className="p-3 text-[var(--muted)]">
                      {h.created_at ? new Date(h.created_at).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
                {history.length === 0 && (
                  <tr>
                    <td colSpan={4} className="p-5 text-[var(--muted)]">
                      No history yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {page === 'upcoming' && (
        <div className="space-y-4 slide-up">
          <h2 className="display text-xl">Upcoming features</h2>
          <p className="text-xs text-[var(--muted)]">Planned — not in this release.</p>
          <div className="grid md:grid-cols-2 gap-3">
            {UPCOMING.map((item, i) => (
              <article key={item.title} className={`risk-tile ${i % 2 ? 'warn' : ''} p-4`}>
                <p className="mono text-[10px] text-[var(--accent-2)] uppercase">Not implemented</p>
                <h3 className="display text-base mt-2">{item.title}</h3>
                <p className="text-xs text-[var(--muted)] mt-2 leading-relaxed">{item.detail}</p>
              </article>
            ))}
          </div>
        </div>
      )}
    </Shell>
  )
}
