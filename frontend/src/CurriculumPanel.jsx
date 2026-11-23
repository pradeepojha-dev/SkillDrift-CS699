import { useEffect, useMemo, useState } from 'react'
import './CurriculumPanel.css'

// API contract verified against SkillDrift FastAPI endpoints.
// Research data is provisional: UNKNOWN is not equivalent to a missing skill.
const CITY_FIELDS = {
  Mumbai: 'Mumbai %',
  Pune: 'Pune %',
  Bengaluru: 'Bengaluru %',
}

const humanize = (value) => String(value ?? '')
  .replace(/_/g, ' ')
  .toLowerCase()
  .replace(/\b[a-z]/g, (match) => match.toUpperCase())

const safePercent = (value) => {
  if (value === '' || value === null || value === undefined) {
    return 'Not available'
  }

  const number = Number(value)

  return Number.isFinite(number)
    ? `${number.toFixed(1)}%`
    : 'Not available'
}

const safeHttpUrl = (url) => {
  try {
    const parsed = new URL(url)

    return ['https:', 'http:'].includes(parsed.protocol)
      ? parsed.href
      : null
  } catch {
    return null
  }
}

async function getJson(path, signal) {
  const response = await fetch(path, { signal })

  if (!response.ok) {
    throw new Error(`${path}: HTTP ${response.status}`)
  }

  return response.json()
}

function ErrorNotice({ message }) {
  return (
    <p className="curriculum-error" role="alert">
      Could not load this section: {message}
    </p>
  )
}

function SourceLink({ record }) {
  const href = safeHttpUrl(record.source_url)

  if (!href) {
    return <span>Source unavailable</span>
  }

  return (
    <a href={href} target="_blank" rel="noreferrer">
      Official source ↗️
    </a>
  )
}

export default function CurriculumPanel({
  city = 'Mumbai',
  spotlightSkill = '',
}) {
  const [data, setData] = useState({
    curriculum: null,
    gaps: null,
    evaluation: null,
  })

  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(true)
  const [course, setCourse] = useState('ALL')
  const [topicQuery, setTopicQuery] = useState('')
  const [selectedGapSkill, setSelectedGapSkill] = useState('')

  useEffect(() => {
    const controller = new AbortController()

    const endpoints = {
      curriculum: '/api/curriculum',
      gaps: '/api/skill-gaps',
      evaluation: '/api/evaluation',
    }

    async function load() {
      const results = await Promise.allSettled(
        Object.entries(endpoints).map(async ([key, path]) => [
          key,
          await getJson(path, controller.signal),
        ]),
      )

      if (controller.signal.aborted) return

      const next = {
        curriculum: null,
        gaps: null,
        evaluation: null,
      }

      const nextErrors = {}

      results.forEach((result, index) => {
        const key = Object.keys(endpoints)[index]

        if (result.status === 'rejected') {
          nextErrors[key] =
            result.reason?.message || 'Request failed'
        } else {
          const [, payload] = result.value

          if (
            (key === 'evaluation' &&
              typeof payload === 'object' &&
              payload !== null) ||
            (key !== 'evaluation' &&
              Array.isArray(payload?.rows))
          ) {
            next[key] = payload
          } else {
            nextErrors[key] = 'Unexpected API response format'
          }
        }
      })

      setData(next)
      setErrors(nextErrors)
      setLoading(false)
    }

    load()

    return () => controller.abort()
  }, [])

  const curriculumRows = useMemo(
    () => data.curriculum?.rows ?? [],
    [data.curriculum],
  )

  const courseIds = useMemo(
    () => [
      ...new Set(
        curriculumRows
          .map((row) => row.course_id)
          .filter(Boolean),
      ),
    ].sort(),
    [curriculumRows],
  )

  const filteredTopics = useMemo(
    () =>
      curriculumRows.filter((row) => {
        if (course !== 'ALL' && row.course_id !== course) {
          return false
        }

        const search = topicQuery.trim().toLowerCase()

        if (!search) return true

        return [
          row.course_id,
          row.course_title,
          row.topic_text,
          row.skill_concept_candidate,
        ].some((value) =>
          String(value ?? '')
            .toLowerCase()
            .includes(search),
        )
      }),
    [course, topicQuery, curriculumRows],
  )

  const gapRows = useMemo(
    () => data.gaps?.rows ?? [],
    [data.gaps],
  )

  const activeGap = selectedGapSkill || spotlightSkill

  const gapRow =
    gapRows.find(
      (row) =>
        row.canonical_skill?.toLowerCase() ===
        String(activeGap).toLowerCase(),
    ) || gapRows[0]

  const cityField = CITY_FIELDS[city] ?? CITY_FIELDS.Mumbai

  const countCandidates = gapRows.reduce(
    (sum, row) =>
      sum + (Number(row.literal_candidate_count) || 0),
    0,
  )

  return (
    <section
      className="curriculum-area"
      aria-label="Curriculum and skill-gap research"
    >
      <div className="curriculum-intro">
        <p className="eyebrow small">
          CURRICULUM × INDUSTRY RESEARCH
        </p>

        <h2>What can the current evidence tell us?</h2>

        <p>
          Selected IIT Bombay CSE course materials are compared
          with observed Data Engineering job samples.
          This is a provisional evidence audit,
          <strong>
            {' '}not a confirmed finding about taught skills
            or curriculum gaps
          </strong>.
        </p>
      </div>

      <div className="curriculum-grid">

        {/* CURRICULUM EXPLORER */}

        <section
          className="curriculum-card"
          aria-labelledby="curriculum-course-heading"
        >
          <div className="curriculum-heading">
            <span>01 / COURSE EVIDENCE</span>

            <h3 id="curriculum-course-heading">
              Curriculum explorer
            </h3>
          </div>

          {loading && (
            <p role="status">
              Loading curriculum evidence…
            </p>
          )}

          {errors.curriculum && (
            <ErrorNotice message={errors.curriculum} />
          )}

          {data.curriculum && (
            <>
              <p className="curriculum-help">
                <strong>
                  {data.curriculum.count ??
                    curriculumRows.length} research topics
                </strong>
                {' · '}
                {courseIds.length} selected courses
                {' · '}
                Historical CS317 excluded.
              </p>

              <div className="curriculum-controls">
                <label>
                  Course

                  <select
                    value={course}
                    onChange={(event) =>
                      setCourse(event.target.value)
                    }
                  >
                    <option value="ALL">
                      All selected courses
                    </option>

                    {courseIds.map((id) => (
                      <option key={id} value={id}>
                        {id}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Find topic

                  <input
                    type="search"
                    value={topicQuery}
                    onChange={(event) =>
                      setTopicQuery(event.target.value)
                    }
                    placeholder="SQL, indexing, Python…"
                  />
                </label>
              </div>

              {/* RESPONSIVE TOPIC CARDS */}

              <div
                className="curriculum-topics"
                role="list"
                aria-label="Curriculum topics"
              >
                {filteredTopics.map((row, index) => (
                  <article
                    className="curriculum-topic-item"
                    role="listitem"
                    key={`${row.topic_id}-${index}`}
                  >
                    <div className="curriculum-topic-header">
                      <strong>
                        {row.course_id} · {row.topic_id}
                      </strong>

                      <span className="curriculum-badge muted">
                        {humanize(
                          row.review_status || 'unreviewed',
                        )}
                      </span>
                    </div>

                    <div className="curriculum-topic-details">
                      <div>
                        <span className="curriculum-topic-label">
                          Course topic
                        </span>

                        <p>
                          {row.topic_text ||
                            'Topic not specified'}
                        </p>
                      </div>

                      <div>
                        <span className="curriculum-topic-label">
                          Candidate concept
                        </span>

                        <p>
                          {row.skill_concept_candidate || (
                            <em>Not assigned</em>
                          )}
                        </p>
                      </div>
                    </div>

                    <div className="curriculum-topic-source">
                      <SourceLink record={row} />

                      <small>
                        {row.source_locator ||
                          'Source section not specified'}
                      </small>
                    </div>
                  </article>
                ))}

                {filteredTopics.length === 0 && (
                  <p className="curriculum-empty">
                    No topics match the filters.
                  </p>
                )}
              </div>

              <p className="curriculum-note">
                Concept labels are researcher-assigned
                candidates. Source links and topic IDs support
                review; they do not establish actual
                instructional coverage.
              </p>
            </>
          )}
        </section>

        {/* SKILL-GAP EVIDENCE */}

        <section
          className="curriculum-card"
          aria-labelledby="curriculum-gap-heading"
        >
          <div className="curriculum-heading">
            <span>02 / SKILL-GAP EVIDENCE</span>

            <h3 id="curriculum-gap-heading">
              Industry vs curriculum
            </h3>
          </div>

          {loading && (
            <p role="status">
              Loading skill-gap evidence…
            </p>
          )}

          {errors.gaps && (
            <ErrorNotice message={errors.gaps} />
          )}

          {data.gaps && (
            <>
              <p className="curriculum-help">
                {gapRows.length} industry skills
                {' · '}
                {countCandidates} provisional literal
                candidate matches.
                {' '}Snapshot:
                <strong> 22 Nov 2026</strong>.
              </p>

              <label className="curriculum-gap-select">
                Select skill

                <select
                  value={gapRow?.canonical_skill || ''}
                  onChange={(event) =>
                    setSelectedGapSkill(event.target.value)
                  }
                >
                  {gapRows.map((row) => (
                    <option
                      key={row.canonical_skill}
                      value={row.canonical_skill}
                    >
                      {humanize(row.canonical_skill)}
                    </option>
                  ))}
                </select>
              </label>

              {gapRow && (
                <div className="curriculum-evidence">

                  <div>
                    <small>
                      Observed demand · {city}
                    </small>

                    <strong>
                      {safePercent(gapRow[cityField])}
                    </strong>

                    <span>
                      Share of sampled listings · 22 Nov
                    </span>
                  </div>

                  <div>
                    <small>Curriculum coverage</small>

                    <strong>
                      {String(
                        gapRow.curriculum_coverage_status ||
                          'unknown',
                      ).toUpperCase()}
                    </strong>

                    <span>
                      Not independently established
                    </span>
                  </div>

                  <div>
                    <small>Gap assessment</small>

                    <strong className="no-assess">
                      {gapRow.gap_assessment_status ||
                        'NOT_ASSESSABLE'}
                    </strong>

                    <span>No supported gap score</span>
                  </div>

                </div>
              )}

              {gapRow && (
                <p className="curriculum-note">
                  Evidence:
                  {' '}
                  {humanize(
                    gapRow.evidence_status || 'unavailable',
                  )}
                  {' · '}
                  {Number(gapRow.literal_candidate_count) || 0}
                  {' '}literal candidate(s).
                  A missing match does not prove a missing skill.
                </p>
              )}

              <div className="curriculum-scroll curriculum-gap-table">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Industry skill</th>
                      <th scope="col">{city} demand</th>
                      <th scope="col">Coverage</th>
                      <th scope="col">Gap</th>
                    </tr>
                  </thead>

                  <tbody>
                    {gapRows.map((row) => (
                      <tr
                        key={row.canonical_skill}
                        className={
                          row.canonical_skill ===
                          gapRow?.canonical_skill
                            ? 'curriculum-selected'
                            : ''
                        }
                      >
                        <th scope="row">
                          {humanize(row.canonical_skill)}
                        </th>

                        <td>
                          {safePercent(row[cityField])}
                        </td>

                        <td>
                          {String(
                            row.curriculum_coverage_status ||
                              'unknown',
                          ).toUpperCase()}
                        </td>

                        <td>
                          {row.gap_assessment_status ||
                            'NOT_ASSESSABLE'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </section>
      </div>

      {/* EVALUATION */}

      <section
        className="curriculum-card curriculum-evaluation"
        aria-labelledby="evaluation-heading"
      >
        <div className="curriculum-heading">
          <span>03 / RESEARCH VALIDATION</span>

          <h3 id="evaluation-heading">
            Evaluation readiness
          </h3>
        </div>

        {loading && (
          <p role="status">
            Loading evaluation status…
          </p>
        )}

        {errors.evaluation && (
          <ErrorNotice message={errors.evaluation} />
        )}

        {data.evaluation && (
          <div className="curriculum-evaluation-body">

            <div>
              <small>Human reference labels</small>

              <strong>
                {data.evaluation.reference_labels_complete
                  ? 'Complete'
                  : 'Pending'}
              </strong>
            </div>

            <div>
              <small>Skill-level evaluation</small>

              <strong>
                {data.evaluation.metrics
                  ? 'Metrics provided'
                  : 'Not available'}
              </strong>
            </div>

            <div>
              <small>Benchmark</small>

              <span>
                {data.evaluation.benchmark ||
                  'Literal mention detection'}
              </span>
            </div>

            <p>
              {data.evaluation.note ||
                'Human review is required before reporting precision, recall or F1.'}
            </p>
          </div>
        )}
      </section>

      <p className="curriculum-footer">
        Academic research prototype · These outputs do not
        establish full IIT Bombay curriculum coverage or
        statistically representative industry trends.
      </p>
    </section>
  )
}