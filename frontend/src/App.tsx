
import { useState } from 'react'
import './App.css'

type Decision = {
  decision_id: string
  status: string
  risk_score: number
  confidence: number
  reasoning: string
  recommendations: string[]
  policy_reasons?: string[]
  requires_human_review: boolean
  scenario: string
  decider_action: string
  decider_model: string | null
  decider_probabilities?: Record<string, number>
  human_review_probability: number | null
  bedrock_explanation?: string | null
}

const API_URL = 'http://127.0.0.1:8000/api/v1/decisions'

function App() {
  const [scenario, setScenario] = useState('')
  const [environment, setEnvironment] = useState('production')
  const [severity, setSeverity] = useState('high')
  const [result, setResult] = useState<Decision | null>(null)
  const [history, setHistory] = useState<Decision[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [active, setActive] = useState('Risk Assessment')

  const highRiskCount = history.filter(
    (item) => item.risk_score >= 70,
  ).length

  const reviewCount = history.filter(
    (item) => item.requires_human_review,
  ).length

  const averageRisk = history.length
    ? Math.round(
        history.reduce((sum, item) => sum + item.risk_score, 0) /
          history.length,
      )
    : 0

  async function evaluateRisk() {
    if (scenario.trim().length < 10) {
      setError('Please enter a scenario with at least 10 characters.')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          scenario: scenario.trim(),
          context: {
            environment,
            severity,
          },
        }),
      })

      if (!response.ok) {
        const responseText = await response.text().catch(() => '')
        throw new Error(
          `Request failed (${response.status} ${response.statusText})${
            responseText ? `: ${responseText.slice(0, 300)}` : ''
          }`,
        )
      }

      const data: Decision = await response.json()

      setResult(data)
      setHistory((previous) => [data, ...previous].slice(0, 10))
      setActive('Risk Assessment')

      setTimeout(() => {
        document.getElementById('latest-decision')?.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
        })
      }, 50)
    } catch (err) {
      console.error('LaunchGuard API error:', err)

      if (err instanceof TypeError) {
        setError(
          'Network request failed. Check the backend URL, CORS settings, and browser Console for details.',
        )
      } else {
        setError(
          err instanceof Error
            ? `API request failed: ${err.message}`
            : 'An unknown API error occurred.',
        )
      }
    } finally {
      setLoading(false)
    }
  }

  function navigate(section: string) {
    setActive(section)

    const target =
      section === 'Decision History'
        ? 'decision-history'
        : 'assessment'

    document.getElementById(target)?.scrollIntoView({
      behavior: 'smooth',
    })
  }

  return (
    <div className="command-center">
      <aside className="sidebar">
        <a className="brand" href="#overview">
          <span className="brand-logo">
            <span>L</span>
          </span>

          <span className="brand-name">
            <strong>
              LaunchGuard<span>-AI</span>
            </strong>
            <small>CLOUD SAFETY GATE</small>
          </span>
        </a>

        <div className="sidebar-section">WORKSPACE</div>

        <button
          className={`nav-link ${active === 'Overview' ? 'selected' : ''}`}
          onClick={() => navigate('Overview')}
        >
          <span className="nav-icon">⌂</span> Overview
        </button>

        <button
          className={`nav-link ${
            active === 'Risk Assessment' ? 'selected' : ''
          }`}
          onClick={() => navigate('Risk Assessment')}
        >
          <span className="nav-icon">◈</span> Risk Assessment
        </button>

        <button
          className={`nav-link ${
            active === 'Decision History' ? 'selected' : ''
          }`}
          onClick={() => navigate('Decision History')}
        >
          <span className="nav-icon">◷</span> Decision History
        </button>

        <div className="sidebar-section">ASSESSMENT</div>

        <button
          className="nav-link"
          onClick={() => navigate('Risk Assessment')}
        >
          <span className="nav-icon">◇</span> Risk Scenarios
        </button>

        <button
          className="nav-link"
          onClick={() => navigate('Risk Assessment')}
        >
          <span className="nav-icon">⬡</span> Safety Policies
        </button>

        <div className="sidebar-section">GOVERNANCE</div>

        <div className="nav-link nav-static">
          <span className="nav-icon">⬡</span> Human Oversight
        </div>

        <div className="nav-link nav-static">
          <span className="nav-icon">▤</span> Reports
        </div>

        <div className="sidebar-bottom">
          <div className="bottom-shield">⬡</div>
          <strong>Safety first</strong>
          <p>Evaluate cloud changes before taking action.</p>
          <span className="local-status">
            <i /> LOCAL PROTOTYPE
          </span>
        </div>
      </aside>

      <main className="dashboard" id="overview">
        <header className="topbar">
          <div className="breadcrumb">
            <span>⌂</span> Workspace <b>/</b> {active}
          </div>

          <div className="topbar-right">
            <span className="online-status">
              <i /> Local services
            </span>
            <span className="service-address">
              API :8000&nbsp; · &nbsp;Decider :8001
            </span>
            <span className="avatar">LG</span>
          </div>
        </header>

        <section className="hero-section">
          <div className="hero-copy">
            <div className="eyebrow">
              CLOUD OPERATIONS · RISK GOVERNANCE · AI SAFETY
            </div>

            <h1>
              Make safer cloud decisions
              <br />
              before you launch.
            </h1>

            <p>
              Evaluate operational risk using Strands Decider 2B and
              deterministic safety policies with clear recommendations
              and human oversight.
            </p>
          </div>

          <div className="hero-art">
            <div className="art-orbit orbit-one" />
            <div className="art-orbit orbit-two" />
            <div className="art-cloud">☁</div>
            <div className="art-server server-one">
              <i />
              <i />
              <i />
            </div>
            <div className="art-server server-two">
              <i />
              <i />
              <i />
            </div>
            <div className="art-shield">
              <span>✓</span>
            </div>
            <div className="art-platform" />
          </div>

          <div className="hero-callout">
            <span className="callout-icon">⬡</span>
            <strong>Pre-flight safety check</strong>
            <p>
              Identify risks, enforce guardrails and require human
              review for high-risk changes.
            </p>
            <span className="callout-label">
              AI-POWERED GOVERNANCE <b>→</b>
            </span>
          </div>
        </section>

        <section className="kpi-grid">
          <article className="kpi-card">
            <div className="kpi-icon purple">▤</div>
            <div className="kpi-content">
              <span>Total assessments</span>
              <strong>{history.length}</strong>
              <small>Current browser session</small>
            </div>
            <span className="kpi-mark purple-text">01</span>
          </article>

          <article className="kpi-card">
            <div className="kpi-icon red">△</div>
            <div className="kpi-content">
              <span>High-risk scenarios</span>
              <strong>{highRiskCount}</strong>
              <small>Risk score ≥ 70</small>
            </div>
            <span className="kpi-mark red-text">02</span>
          </article>

          <article className="kpi-card">
            <div className="kpi-icon blue">♙</div>
            <div className="kpi-content">
              <span>Human review</span>
              <strong>{reviewCount}</strong>
              <small>Reviews required this session</small>
            </div>
            <span className="kpi-mark blue-text">03</span>
          </article>

          <article className="kpi-card">
            <div className="kpi-icon green">✓</div>
            <div className="kpi-content">
              <span>Average risk score</span>
              <strong>
                {history.length ? averageRisk : '—'}
                {history.length ? '/100' : ''}
              </strong>
              <small>
                {history.length
                  ? 'Based on session results'
                  : 'Awaiting first assessment'}
              </small>
            </div>
            <span className="kpi-mark green-text">04</span>
          </article>
        </section>

        <section className="content-grid" id="assessment">
          <article className="panel assessment-panel">
            <div className="panel-heading">
              <div className="panel-heading-icon">▤</div>

              <div>
                <h2>Evaluate a proposed change</h2>
                <p>
                  Describe the scenario and provide its operational
                  context.
                </p>
              </div>

              <span className="step-badge">STEP 1 / ASSESS</span>
            </div>

            <div className="form-body">
              <label htmlFor="scenario">Scenario description</label>

              <textarea
                id="scenario"
                value={scenario}
                onChange={(event) => setScenario(event.target.value)}
                maxLength={5000}
                placeholder="Example: A production payment service has a sudden increase in failed transactions after a configuration change..."
              />

              <div className="char-count">
                {scenario.length}/5000 characters
              </div>

              <div className="form-row">
                <div className="field">
                  <label htmlFor="environment">Environment</label>
                  <select
                    id="environment"
                    value={environment}
                    onChange={(event) =>
                      setEnvironment(event.target.value)
                    }
                  >
                    <option value="production">Production</option>
                    <option value="staging">Staging</option>
                    <option value="development">Development</option>
                  </select>
                </div>

                <div className="field">
                  <label htmlFor="severity">Incident severity</label>
                  <select
                    id="severity"
                    value={severity}
                    onChange={(event) =>
                      setSeverity(event.target.value)
                    }
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </div>

              <div className="guardrail-note">
                <span>ⓘ</span>
                <p>
                  This assessment does not execute infrastructure
                  changes. High-risk or uncertain decisions require
                  human review.
                </p>
              </div>

              {error && (
                <div className="error-message" role="alert">
                  {error}
                </div>
              )}

              <button
                className="evaluate-button"
                onClick={evaluateRisk}
                disabled={loading}
              >
                <span>{loading ? '◌' : '✦'}</span>
                {loading
                  ? 'Evaluating with LaunchGuard-AI...'
                  : 'Evaluate risk with LaunchGuard-AI'}
                <b>→</b>
              </button>
            </div>
          </article>

          <article className="panel latest-panel" id="latest-decision">
            <div className="panel-heading">
              <div className="panel-heading-icon">▧</div>

              <div>
                <h2>Latest decision</h2>
                <p>AI recommendation and safety outcome</p>
              </div>

              <span
                className={`status-badge ${
                  result
                    ? result.requires_human_review
                      ? 'needs-review'
                      : 'approved'
                    : 'waiting'
                }`}
              >
                <i />
                {result
                  ? result.requires_human_review
                    ? 'REVIEW REQUIRED'
                    : 'POLICY PASSED'
                  : 'AWAITING INPUT'}
              </span>
            </div>

            {result ? (
              <div className="decision-body">
                <div className="decision-overview">
                  <div
                    className="risk-gauge"
                    style={
                      { '--risk': `${result.risk_score}%` } as React.CSSProperties
                    }
                  >
                    <div className="gauge-inner">
                      <strong>{result.risk_score}</strong>
                      <span>RISK SCORE</span>
                    </div>
                  </div>

                  <div className="decision-summary">
                    <span className="summary-label">Decision</span>
                    <strong>
                      {result.requires_human_review
                        ? 'Needs human review'
                        : 'Review not triggered'}
                    </strong>

                    <span className="summary-label">
                      Decider recommendation
                    </span>
                    <code>{result.decider_action}</code>

                    <div className="mini-stats">
                      <div>
                        <small>Confidence</small>
                        <strong>
                          {(result.confidence * 100).toFixed(1)}%
                        </strong>
                      </div>
                      <div>
                        <small>Model</small>
                        <strong>Decider 2B</strong>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="recommendations">
                  <h3>Key recommendations</h3>
                  {result.recommendations.map((recommendation, index) => (
                    <div className="recommendation" key={recommendation}>
                      <span>{index + 1}</span>
                      <p>{recommendation}</p>
                    </div>
                  ))}
                </div>

                <div className="reasoning-box">
                  <strong>Decision reasoning</strong>
                  <p>{result.reasoning}</p>
                </div>

                {result.bedrock_explanation && (
                  <div className="reasoning-box">
                    <strong>Bedrock explanation</strong>
                    <p>{result.bedrock_explanation}</p>
                  </div>
                )}

                <div className="decision-meta">
                  <span>{result.decider_model ?? 'Model unavailable'}</span>
                  <span>ID {result.decision_id.slice(0, 8)}</span>
                </div>
              </div>
            ) : (
              <div className="waiting-state">
                <div className="waiting-symbol">⬡</div>
                <strong>No decision generated yet</strong>
                <p>
                  Submit a scenario to view the risk score, model
                  recommendation and required safeguards.
                </p>
                <span>Waiting for assessment</span>
              </div>
            )}
          </article>
        </section>

        <section className="lower-grid">
          <article
            className="panel history-panel"
            id="decision-history"
          >
            <div className="lower-heading">
              <div>
                <h2>Recent decisions</h2>
                <p>Assessments from this browser session</p>
              </div>
              <span className="history-count">
                {history.length} total
              </span>
            </div>

            {history.length ? (
              <div className="history-list">
                {history.map((item) => (
                  <button
                    className="history-row"
                    key={item.decision_id}
                    onClick={() => setResult(item)}
                  >
                    <span
                      className={`history-icon ${
                        item.requires_human_review
                          ? 'history-red'
                          : 'history-green'
                      }`}
                    >
                      {item.requires_human_review ? '!' : '✓'}
                    </span>

                    <span className="history-description">
                      <strong>{item.scenario}</strong>
                      <small>
                        {item.decision_id.slice(0, 8)} · Risk{' '}
                        {item.risk_score}/100
                      </small>
                    </span>

                    <span
                      className={`history-status ${
                        item.requires_human_review
                          ? 'text-red'
                          : 'text-green'
                      }`}
                    >
                      {item.requires_human_review ? 'Review' : 'Passed'}
                    </span>
                  </button>
                ))}
              </div>
            ) : (
              <div className="empty-history">
                Your completed assessments will appear here.
              </div>
            )}
          </article>

          <article className="panel safety-panel">
            <div className="lower-heading">
              <div>
                <h2>Safety guardrails</h2>
                <p>Decision safeguards</p>
              </div>
            </div>

            <div className="safety-item">
              <span className="guardrail-symbol">✓</span>
              <div>
                <strong>Deterministic policy</strong>
                <small>Risk rules run alongside AI decisions.</small>
              </div>
            </div>

            <div className="safety-item">
              <span className="guardrail-symbol">♙</span>
              <div>
                <strong>Human oversight</strong>
                <small>High risk or uncertainty triggers review.</small>
              </div>
            </div>

            <div className="safety-item">
              <span className="guardrail-symbol">⌑</span>
              <div>
                <strong>No automatic execution</strong>
                <small>
                  This prototype does not change cloud resources.
                </small>
              </div>
            </div>

            <div className="prototype-label">
              <i /> LOCAL PROTOTYPE · NOT CLOUD CONNECTED
            </div>
          </article>
        </section>

        <footer className="dashboard-footer">
          <span>LaunchGuard-AI · Cloud Safety Gate</span>
          <span>
            Decision support only · Human approval remains essential
          </span>
        </footer>
      </main>
    </div>
  )
}

export default App

