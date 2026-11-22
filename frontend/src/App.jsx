import { useEffect, useMemo, useState } from 'react'
import {
  Bar, BarChart, CartesianGrid, Legend, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import './App.css'

const CITIES = [
  { name: 'Mumbai', field: 'Mumbai %', old: 'Mumbai %_Old', newer: 'Mumbai %_New', change: 'Mumbai Change', trend: 'Mumbai Trend' },
  { name: 'Pune', field: 'Pune %', old: 'Pune %_Old', newer: 'Pune %_New', change: 'Pune Change', trend: 'Pune Trend' },
  { name: 'Bengaluru', field: 'Bengaluru %', old: 'Bengaluru %_Old', newer: 'Bengaluru %_New', change: 'Bengaluru Change', trend: 'Bengaluru Trend' },
]

const num = (value) => Number.isFinite(Number(value)) ? Number(value) : 0
const pct = (value) => `${num(value).toFixed(1)}%`
const pp = (value) => `${num(value) > 0 ? '+' : ''}${num(value).toFixed(1)} pp`
const pretty = (value) => String(value || '').replace(/\b\w/g, (letter) => letter.toUpperCase())
const dateLabel = (value) => {
  if (!value) return '—'
  const [year, month, day] = value.split('-').map(Number)
  return new Date(Date.UTC(year, month - 1, day)).toLocaleDateString('en-GB', {
    timeZone: 'UTC', day: 'numeric', month: 'short', year: 'numeric',
  })
}

function StatusPill({ trend }) {
  const key = String(trend || 'STABLE').toUpperCase()
  return <span className={`trend trend-${key.toLowerCase()}`}>{pretty(key.toLowerCase())}</span>
}

function Stat({ label, value, detail }) {
  return <div className="stat-card"><div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-detail">{detail}</div></div>
}

export default function App() {
  const [payload, setPayload] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedCity, setSelectedCity] = useState('Mumbai')
  const [selectedDate, setSelectedDate] = useState('')
  const [selectedSkill, setSelectedSkill] = useState('sql')

  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      try {
        const [snapshotResponse, driftResponse] = await Promise.all([
          fetch('/api/snapshots', { signal: controller.signal }),
          fetch('/api/skill-drift', { signal: controller.signal }),
        ])
        if (!snapshotResponse.ok || !driftResponse.ok) {
          throw new Error(`API returned HTTP ${snapshotResponse.status} / ${driftResponse.status}.`)
        }
        const [snapshots, drift] = await Promise.all([snapshotResponse.json(), driftResponse.json()])
        if (!Array.isArray(snapshots.snapshots) || !Array.isArray(drift.rows)) {
          throw new Error('API response shape differs from the expected SkillDrift contract.')
        }
        setPayload({ snapshots: snapshots.snapshots, drift: drift.rows })
        setError('')
      } catch (err) {
        if (err.name !== 'AbortError') setError(`${err.message} Check that FastAPI is running on port 8000 and the Vite proxy is configured.`)
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }
    load()
    return () => controller.abort()
  }, [])

  const city = CITIES.find((entry) => entry.name === selectedCity) || CITIES[0]
  const snapshots = payload?.snapshots || []
  const dates = useMemo(() => [...snapshots.map((entry) => entry.date)].sort(), [snapshots])
  const activeDate = dates.includes(selectedDate) ? selectedDate : dates[dates.length - 1] || ''
  const latestSnapshot = snapshots.find((entry) => entry.date === activeDate)
  const driftRows = payload?.drift || []
  const skills = useMemo(() => [...new Set(driftRows.map((row) => row.Skill))].sort(), [driftRows])
  const activeSkill = skills.includes(selectedSkill) ? selectedSkill : skills[0] || ''

  const demandRows = useMemo(() => (latestSnapshot?.rows || [])
    .map((row) => ({ skill: pretty(row.Skill), demand: num(row[city.field]) }))
    .sort((a, b) => b.demand - a.demand), [latestSnapshot, city])

  const comparisonRows = useMemo(() => driftRows.map((row) => ({
    skill: String(row.Skill || ''),
    old: num(row[city.old]),
    newer: num(row[city.newer]),
    change: num(row[city.change]),
    trend: row[city.trend] || 'STABLE',
  })).sort((a, b) => Math.abs(b.change) - Math.abs(a.change)), [driftRows, city])

  const selectedSkillRow = driftRows.find((row) => row.Skill === activeSkill)
  const cityComparison = selectedSkillRow ? CITIES.map((entry) => ({
    city: entry.name,
    '15 Oct': num(selectedSkillRow[entry.old]),
    '22 Nov': num(selectedSkillRow[entry.newer]),
  })) : []

  const biggest = comparisonRows[0]
  const yearDates = dates.length ? `${dateLabel(dates[0])} → ${dateLabel(dates[dates.length - 1])}` : '—'

  return (
    <div className="dashboard">
      <header className="header">
        <div className="brand"><div className="brand-symbol" aria-hidden="true">S<span>↗</span></div>
          <div><div className="brand-title">SkillDrift</div><div className="brand-subtitle">Curriculum × Industry Signals</div></div>
        </div>
        <div className="header-tag"><span className="pulse" /> CS699 · IIT Bombay · Prototype</div>
      </header>

      <main>
        <section className="hero">
          <div><p className="eyebrow">LIVE DATA EXPLORER</p><h1>How are skill signals changing?</h1>
            <p className="hero-copy">Explore the observed Data Engineering job samples from Mumbai, Pune and Bengaluru across two collection dates.</p></div>
          <div className="hero-aside"><span>OBSERVATION WINDOW</span><strong>{yearDates}</strong><small>Sample comparison · Not a population estimate</small></div>
        </section>

        {loading && <div className="message" role="status">Loading skill snapshots and drift data…</div>}
        {error && <div className="message error" role="alert"><strong>Unable to load dashboard.</strong><br />{error}</div>}

        {!loading && !error && payload && <>
          <section className="filters" aria-label="Dashboard filters">
            <label>City<select value={selectedCity} onChange={(event) => setSelectedCity(event.target.value)}>{CITIES.map((entry) => <option key={entry.name} value={entry.name}>{entry.name}</option>)}</select></label>
            <label>Snapshot date<select value={activeDate} onChange={(event) => setSelectedDate(event.target.value)}>{dates.map((date) => <option key={date} value={date}>{dateLabel(date)}</option>)}</select></label>
            <label>Skill spotlight<select value={activeSkill} onChange={(event) => setSelectedSkill(event.target.value)}>{skills.map((skill) => <option key={skill} value={skill}>{pretty(skill)}</option>)}</select></label>
          </section>

          <section className="stats" aria-label="Overview">
            <Stat label="Snapshot dates" value={snapshots.length} detail={yearDates} />
            <Stat label="Tracked skills" value={skills.length} detail="From existing project snapshots" />
            <Stat label="Cities analyzed" value={CITIES.length} detail="Mumbai · Pune · Bengaluru" />
            <Stat label={`Largest change · ${selectedCity}`} value={biggest ? pp(biggest.change) : '—'} detail={biggest ? pretty(biggest.skill) : 'Not available'} />
          </section>

          <div className="content-grid">
            <section className="panel panel-wide" aria-labelledby="demand-heading">
              <div className="panel-head"><div><p className="eyebrow small">DEMAND SNAPSHOT</p><h2 id="demand-heading">Top skills in {selectedCity}</h2><p>Share of sampled job results mentioning each skill · {dateLabel(activeDate)}</p></div><span className="unit">% of job results</span></div>
              {demandRows.length ? <div className="chart-box tall"><ResponsiveContainer width="100%" height="100%"><BarChart data={demandRows} layout="vertical" margin={{ top: 6, right: 20, left: 8, bottom: 6 }} barCategoryGap="26%">
                <CartesianGrid strokeDasharray="4 5" horizontal={false} stroke="#e6ebf1" />
                <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11, fill: '#637185' }} axisLine={false} tickLine={false} />
                <YAxis dataKey="skill" type="category" width={118} tick={{ fontSize: 12, fill: '#344154' }} axisLine={false} tickLine={false} />
                <Tooltip formatter={(v) => [pct(v), 'Observed skill mentions']} cursor={{ fill: '#f4f7fb' }} />
                <Bar dataKey="demand" fill="#3e73d7" radius={[0, 5, 5, 0]} maxBarSize={24} />
              </BarChart></ResponsiveContainer></div> : <div className="message">No demand rows available.</div>}
            </section>

            <section className="panel" aria-labelledby="spotlight-heading">
              <div className="panel-head"><div><p className="eyebrow small">CITY COMPARISON</p><h2 id="spotlight-heading">{pretty(activeSkill)} across cities</h2><p>How the selected skill changed between snapshots</p></div></div>
              {cityComparison.length ? <div className="chart-box compact"><ResponsiveContainer width="100%" height="100%"><BarChart data={cityComparison} margin={{ top: 14, right: 10, left: -20, bottom: 10 }} barGap={5}>
                <CartesianGrid strokeDasharray="4 5" vertical={false} stroke="#e6ebf1" />
                <XAxis dataKey="city" tick={{ fontSize: 12, fill: '#637185' }} axisLine={false} tickLine={false} />
                <YAxis tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11, fill: '#637185' }} axisLine={false} tickLine={false} />
                <Tooltip formatter={(v) => pct(v)} />
                <Legend verticalAlign="bottom" wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="15 Oct" fill="#a9b9d4" radius={[4, 4, 0, 0]} maxBarSize={48} />
                <Bar dataKey="22 Nov" fill="#3e73d7" radius={[4, 4, 0, 0]} maxBarSize={48} />
              </BarChart></ResponsiveContainer></div> : <div className="message">No comparison rows available.</div>}
              <div className="callout"><span className="callout-icon">i</span><span><strong>Interpretation note</strong><br />Differences reflect small observed samples. The ±5 percentage-point trend cutoff is a prototype rule, not a statistical significance test.</span></div>
            </section>
          </div>

          <section className="panel table-panel" aria-labelledby="movement-heading">
            <div className="panel-head"><div><p className="eyebrow small">TEMPORAL MOVEMENT</p><h2 id="movement-heading">Skill change breakdown · {selectedCity}</h2><p>All tracked skills, ranked by absolute change between the two snapshots.</p></div><span className="unit">Change in percentage points</span></div>
            <div className="table-scroll"><table><thead><tr><th scope="col">Skill</th><th scope="col">15 Oct</th><th scope="col">22 Nov</th><th scope="col">Change</th><th scope="col">Classification</th></tr></thead>
              <tbody>{comparisonRows.map((row) => <tr key={row.skill}><th scope="row">{pretty(row.skill)}</th><td>{pct(row.old)}</td><td>{pct(row.newer)}</td><td className={row.change > 0 ? 'positive' : row.change < 0 ? 'negative' : ''}>{pp(row.change)}</td><td><StatusPill trend={row.trend} /></td></tr>)}</tbody></table></div>
          </section>
        </>}
      </main>
      <footer><strong>SkillDrift</strong> · IIT Bombay CS699 · Team KernelX <span>Research prototype — not representative of the complete job market or curriculum.</span></footer>
    </div>
  )
}
