import { useState } from 'react'
import {
  connectWallet,
  fingerprintFile,
  verifyRegisteredProject,
} from './blockchain'
import './App.css'

type Project = {
  id: number
  name: string
  team: string
  status: string
  similarity: number | null
}
// Add the new types below this line

type AnalysisComparison = {
  compared_submission_id: string
  token_similarity: number
  structural_similarity: number
  embedding_similarity: number | null
  combined_similarity: number
  matched_regions: unknown[]
  boilerplate_matched: unknown[]
  warnings: string[]
  review_recommendation: string
}

type AnalysisSubmission = {
  submission_id: string
  language: string
  num_tokens: number
  comparisons: AnalysisComparison[]
  warnings: string[]
}

type AnalysisResponse = {
  results: AnalysisSubmission[]
  method: string
  warnings: string[]
  disclaimer: string
  score_to_percentage: string
}

function App() {
  const [page, setPage] = useState('Dashboard')
  const [projects, setProjects] = useState<Project[]>([
    { id: 1, name: 'Student Management System', team: 'Team Alpha', status: 'Verified', similarity: 8 },
    { id: 2, name: 'Library Management App', team: 'Team Beta', status: 'Pending', similarity: null },
    { id: 3, name: 'Online Voting System', team: 'Team Gamma', status: 'Verified', similarity: 12 },
  ])

  const [projectName, setProjectName] = useState('')
  const [teamName, setTeamName] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [message, setMessage] = useState('')
  const [walletAddress, setWalletAddress] = useState('')
  const [verificationFile, setVerificationFile] = useState<File | null>(null)
  const [verificationResult, setVerificationResult] = useState<{
  isRegistered: boolean
  owner: string
  timestamp: number
} | null>(null)
  const [verificationBusy, setVerificationBusy] = useState(false)
  const [blockchainBusy, setBlockchainBusy] = useState(false)
  // AI Analysis state — add these six lines
  const [language, setLanguage] = useState('python')
  const [sourceA, setSourceA] = useState('def calculate():\n    return 42')
  const [sourceB, setSourceB] = useState('def calculate():\n    return 42')
  const [analysisResult, setAnalysisResult] = useState<unknown>(null)
  const [analysisError, setAnalysisError] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
    
async function analyzeCode() {
  setAnalyzing(true)
  setAnalysisError('')
  setAnalysisResult(null)

  try {
    const response = await fetch('/api/v1/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        submissions: [
  {
    submission_id: 'submission-a',
    language,
    source_code: sourceA,
  },
  {
    submission_id: 'submission-b',
    language,
    source_code: sourceB,
  },
],
        shingle_k: 5,
      }),
    })

    const data: unknown = await response.json()

    if (!response.ok) {
      throw new Error(
        `Analysis failed (${response.status}): ${JSON.stringify(data)}`
      )
    }

    setAnalysisResult(data)
  } catch (error) {
    setAnalysisError(
      error instanceof Error
        ? error.message
        : 'An unexpected error occurred.'
    )
  } finally {
    setAnalyzing(false)
  }
}

  const verified = projects.filter(p => p.status === 'Verified').length

  
async function verifyProjectFile() {
  if (!verificationFile || !verificationFile.name.toLowerCase().endsWith('.zip')) {
    setMessage('Please select a ZIP file to verify.')
    return
  }

  setVerificationBusy(true)
  setMessage('')
  setVerificationResult(null)

  try {
    const fingerprint = await fingerprintFile(verificationFile)
    const result = await verifyRegisteredProject(fingerprint)

    setVerificationResult(result)

    if (result.isRegistered) {
      setMessage('This ZIP file is registered on the blockchain.')
    } else {
      setMessage('This ZIP file is not registered on the blockchain.')
    }
  } catch (error) {
    setMessage(
      error instanceof Error
        ? error.message
        : 'Verification failed. Please try again.'
    )
  } finally {
    setVerificationBusy(false)
  }
}

    
async function registerProject() {
  if (!projectName.trim() || !teamName.trim()) {
    setMessage('Please enter the project name and team name.')
    return
  }

  if (!file || !file.name.toLowerCase().endsWith('.zip')) {
    setMessage('Please choose a ZIP file containing your source code.')
    return
  }

  setBlockchainBusy(true)
  setMessage('Preparing blockchain registration...')

  try {
    const fingerprint = await fingerprintFile(file)
    const { account, contract } = await connectWallet()

    setWalletAddress(account)
    setMessage('Confirm the registration transaction in MetaMask...')

    const alreadyRegistered: boolean = await contract.isProjectRegistered(
      fingerprint
    )

    if (alreadyRegistered) {
      throw new Error(
        'This exact ZIP file is already registered on the blockchain.'
      )
    }

    const transaction = await contract.registerProject(fingerprint)

    setMessage(`Transaction submitted: ${transaction.hash}`)

    const receipt = await transaction.wait()

    if (!receipt || receipt.status !== 1) {
      throw new Error('The blockchain transaction failed.')
    }

    setProjects(previous => [
      ...previous,
      {
        id: Date.now(),
        name: projectName.trim(),
        team: teamName.trim(),
        status: 'Verified',
        similarity: null,
      },
    ])

    setMessage(
      `Project registered successfully! Fingerprint: ${fingerprint}. Transaction: ${transaction.hash}`
    )

    setProjectName('')
    setTeamName('')
    setFile(null)

    const input = document.getElementById(
      'source-file'
    ) as HTMLInputElement | null

    if (input) input.value = ''
  } catch (error) {
    setMessage(
      error instanceof Error
        ? error.message
        : 'Registration failed. Please try again.'
    )
  } finally {
    setBlockchainBusy(false)
  }
}

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span>⬡</span>  CodeProof  </div>
        <p className="side-label">WORKSPACE</p>

        {['Dashboard', 'Register Project', 'AI Analysis' , 'Verification'].map(item => (
          <button
            key={item}
            className={`nav-item ${page === item ? 'active' : ''}`}
            onClick={() => {
              setPage(item)
              setMessage('')
            }}
          >
            <span>{item === 'Dashboard' ? '▦' : item === 'Register Project' ? '＋' : item === 'AI Analysis' ? '✦' : '✓'}</span>
            {item}
          </button>
        ))}

        <div className="sidebar-bottom">
          <div className="lock-icon">🔐</div>
          <strong>Code you can trust.</strong>
          <p>Originality checks and blockchain verification in one place.</p>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">BLOCKCHAIN + AI</p>
            <h1>{page}</h1>
          </div>
        </header>

        
{page === 'Dashboard' && (
  <>
    <section className="welcome">
      <div className="welcome-text">
        <p className="eyebrow light">YOUR PROJECT WORKSPACE</p>
        <h2>Original work.<br />Verified with confidence.</h2>
        <p>
          Register source code, review similarity reports, and
          verify project ownership on the blockchain.
        </p>
        <button
          className="primary-button"
          onClick={() => setPage('Register Project')}
        >
          + Register a project
        </button>
      </div>
      <div className="hero-symbol" aria-hidden="true">⬡</div>
    </section>

    <div className="dashboard-section-heading">
  <div>
    <h2>Workspace overview</h2>
    <p>Quick snapshot of the projects in this session.</p>
  </div>
</div>

    <section className="stats-grid">
      <article className="stat-card">
        <span className="stat-icon purple" aria-hidden="true">▦</span>
        <div className="stat-content">
          <p>Total projects</p>
          <strong>{projects.length}</strong>
          <small>Listed in this session</small>
        </div>
      </article>

      <article className="stat-card">
        <span className="stat-icon green" aria-hidden="true">✓</span>
        <div className="stat-content">
          <p>Verified</p>
          <strong>{verified}</strong>
          <small>Marked verified in the list</small>
        </div>
      </article>

      <article className="stat-card">
        <span className="stat-icon orange" aria-hidden="true">◷</span>
        <div className="stat-content">
          <p>Pending</p>
          <strong>{projects.filter(p => p.status === 'Pending').length}</strong>
          <small>Marked pending in the list</small>
        </div>
      </article>
    </section>

    <section className="panel dashboard-projects">
      <div className="panel-heading">
        <div>
          <h3>Recent projects</h3>
          <p>Projects currently listed in your workspace.</p>
        </div>
        <button
          className="text-button"
          onClick={() => setPage('Verification')}
        >
          View verification →
        </button>
      </div>

      {projects.length === 0 ? (
        <div className="dashboard-empty-state">
          <div className="empty-state-icon" aria-hidden="true">⌁</div>
          <h3>No projects yet</h3>
          <p>
            Register your first ZIP project to get started with
            blockchain ownership verification.
          </p>
          <button
            className="empty-state-button"
            onClick={() => setPage('Register Project')}
          >
            Register your first project
          </button>
        </div>
      ) : (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Project</th>
                  <th>Team</th>
                  <th>Similarity</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {projects.slice(-5).reverse().map(project => (
                  <tr key={project.id}>
                    <td>
                      <div className="project-name-cell">
                        <span className="project-row-icon" aria-hidden="true">
                          {'</>'}
                        </span>
                        <strong>{project.name}</strong>
                      </div>
                    </td>
                    <td>{project.team || '—'}</td>
                    <td>
                      {project.similarity === null
                        ? 'Not analyzed'
                        : `${project.similarity}%`}
                    </td>
                    <td>
                      <span
                        className={`status ${project.status.toLowerCase()}`}
                      >
                        {project.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="dashboard-footnote">
            Sample entries are illustrative. Newly registered projects
            are added to this session's list; the dashboard is not yet
            backed by persistent project storage.
          </p>
        </>
      )}
    </section>
  </>
)}


        {page === 'Register Project' && (
          <section className="panel form-panel">
            <div className="panel-heading">
              <div>
                <h3>Register a new project</h3>
                <p>Enter your project details and select your source-code ZIP file.</p>
              </div>
            </div>

            <label htmlFor="project-name">Project name</label>
            <input
              id="project-name"
              value={projectName}
              onChange={e => setProjectName(e.target.value)}
              placeholder="e.g. Student Management System"
            />

            <label htmlFor="team-name">Team or owner name</label>
            <input
              id="team-name"
              value={teamName}
              onChange={e => setTeamName(e.target.value)}
              placeholder="e.g. Team Alpha"
            />

            
<label htmlFor="source-file">Source code ZIP file</label>
<div className="upload-zone">
  <div className="upload-zone-icon" aria-hidden="true">↑</div>
  <strong>{file ? file.name : 'Choose your project ZIP'}</strong>
  <p>
    {file
      ? `${(file.size / (1024 * 1024)).toFixed(2)} MB · File selected`
      : 'Select a ZIP archive containing your source code.'}
  </p>
  <label className="upload-button" htmlFor="source-file">
    {file ? 'Choose another file' : 'Browse files'}
  </label>
  <input
    id="source-file"
    className="source-file-input"
    type="file"
    accept=".zip,application/zip"
    onChange={e => setFile(e.target.files?.[0] ?? null)}
  />
</div>
<p className="field-help">
  ZIP files only. Your project fingerprint is registered on the blockchain.
</p>


            {message && <p className="message">{message}</p>}

            {walletAddress && (
  <p className="field-help">
    Connected wallet: {walletAddress}
  </p>
)}

            <div className="form-actions">
              <button className="secondary-button" onClick={() => setPage('Dashboard')}>Cancel</button>
              <button
  className="primary-button"
  onClick={registerProject}
  disabled={blockchainBusy}
>
  {blockchainBusy ? 'Registering...' : 'Register project'}
</button>
            </div>
          
          </section>
        )}

        {page === 'AI Analysis' && (
          <section className="panel form-panel">
            <div className="panel-heading">
              <div>
                <h3>AI Code Similarity Analysis</h3>
                <p>
                  Compare two Python or Java source-code submissions.
                </p>
              </div>
            </div>

            
<label id="language-label" htmlFor="language">
  Programming language
</label>

<div className="language-picker">
  <button
    id="language"
    type="button"
    className="language-picker-trigger"
    aria-labelledby="language-label"
    aria-haspopup="listbox"
    aria-expanded={false}
    onClick={() => {
      const menu = document.getElementById('language-options')
      if (menu) {
        menu.hidden = !menu.hidden
      }
    }}
  >
    <span>{language === 'python' ? 'Python' : 'Java'}</span>
    <span aria-hidden="true">⌄</span>
  </button>

  <div id="language-options" className="language-picker-menu" role="listbox" hidden>
    <button
      type="button"
      role="option"
      aria-selected={language === 'python'}
      className="language-picker-option"
      onClick={() => {
        setLanguage('python')
        const menu = document.getElementById('language-options')
        if (menu) menu.hidden = true
      }}
    >
      Python
    </button>
    <button
      type="button"
      role="option"
      aria-selected={language === 'java'}
      className="language-picker-option"
      onClick={() => {
        setLanguage('java')
        const menu = document.getElementById('language-options')
        if (menu) menu.hidden = true
      }}
    >
      Java
    </button>
  </div>
</div>


            <label htmlFor="source-a">First code submission</label>
            <textarea
              id="source-a"
              rows={8}
              value={sourceA}
              onChange={e => setSourceA(e.target.value)}
              placeholder="Paste the first code sample here..."
              spellCheck={false}
            />

            <label htmlFor="source-b">Second code submission</label>
            <textarea
              id="source-b"
              rows={8}
              value={sourceB}
              onChange={e => setSourceB(e.target.value)}
              placeholder="Paste the second code sample here..."
              spellCheck={false}
            />

            <div className="form-actions">
              <button
                className="primary-button"
                disabled={analyzing || !sourceA.trim() || !sourceB.trim()}
                onClick={analyzeCode}
              >
                {analyzing ? 'Analyzing...' : 'Analyze similarity'}
              </button>
            </div>

            {analysisError && (
              <p className="message" role="alert">
                {analysisError}
              </p>
            )}

            
{analysisResult !== null && (
  <div className="analysis-results">
    {(() => {
      const report = analysisResult as AnalysisResponse

      return (
        <>
          <h3>Analysis Results</h3>

          <p className="results-intro">
            CodeProof compared your submissions and measured how much
            their code overlaps. Review the scores below before drawing
            any conclusions.
          </p>

          {report.results.slice(0, 1).map(submission =>
  submission.comparisons.slice(0, 1).map(comparison => {
              const score = Math.round(
                comparison.combined_similarity * 100
              )

              const level =
                score < 30
                  ? 'Low overlap'
                  : score < 70
                    ? 'Moderate overlap'
                    : 'High overlap'

              const explanation =
                score < 30
                  ? 'The detector found relatively little overall similarity.'
                  : score < 70
                    ? 'The detector found some similarities that may need closer review.'
                    : 'The detector found substantial similarity. Review the code carefully.'

              return (
                <div
                  className="result-card"
                  key={`${submission.submission_id}-${comparison.compared_submission_id}`}
                >
                  <div className="result-card-heading">
                    <div>
                      <span className="result-eyebrow">
                        COMBINED SIMILARITY
                      </span>
                      <h2>{score}%</h2>
                      <span className="result-level">{level}</span>
                    </div>

                    <div className="score-circle">
                      {score}%
                    </div>
                  </div>

                  <div className="score-track">
                    <div
                      className="score-fill"
                      style={{ width: `${score}%` }}
                    />
                  </div>

                  <p>{explanation}</p>

                  <p className="comparison-label">
                    Submission {submission.submission_id} compared with{' '}
                    {comparison.compared_submission_id}
                  </p>

                  <div className="metric-grid">
                    <div className="metric-item">
                      <span>Token similarity</span>
                      <strong>
                        {Math.round(comparison.token_similarity * 100)}%
                      </strong>
                      <p>Similarity in code-token patterns.</p>
                    </div>

                    <div className="metric-item">
                      <span>Structural similarity</span>
                      <strong>
                        {Math.round(comparison.structural_similarity * 100)}%
                      </strong>
                      <p>Similarity in the sequence of code tokens.</p>
                    </div>
                  </div>

                  
{comparison.matched_regions.length > 0 && (
  <div className="matched-regions">
    <h4>Matching Code Regions</h4>
    <p className="match-explanation">
      These snippets were identified as similar by the detector.
      Review them in context before drawing conclusions.
    </p>

    {comparison.matched_regions.map((region, index) => {
      const match = region as {
        snippet_a?: string
        snippet_b?: string
        token_length?: number
      }

      return (
        <div className="match-pair" key={index}>
          <div className="match-pane">
            <span className="match-pane-label">Submission A</span>
            <pre>{match.snippet_a ?? 'Snippet unavailable'}</pre>
          </div>

          <div className="match-pane">
            <span className="match-pane-label">Submission B</span>
            <pre>{match.snippet_b ?? 'Snippet unavailable'}</pre>
          </div>

          {match.token_length !== undefined && (
            <p className="match-token-count">
              Matching region: {match.token_length} tokens
            </p>
          )}
        </div>
      )
    })}
  </div>
)}


                  {(
                    submission.warnings.length > 0 ||
                    comparison.warnings.length > 0
                  ) && (
                    <div className="result-warning">
                      <strong>Things to keep in mind</strong>
                      <ul>
                        {[
                          ...submission.warnings,
                          ...comparison.warnings,
                        ].map((warning, index) => (
                          <li key={`${warning}-${index}`}>{warning}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="review-note">
                    <strong>Detector guidance</strong>
                    <p>{comparison.review_recommendation}</p>
                  </div>
                </div>
              )
            })
          )}

          <details className="technical-details">
            <summary>View technical response (JSON)</summary>
            <pre className="analysis-output">
              {JSON.stringify(analysisResult, null, 2)}
            </pre>
          </details>

          <p className="demo-note">
            Important: Similarity is an indicator of code overlap, not proof
            of plagiarism. Scores can be affected by short programs,
            common patterns, and boilerplate code. Human review is required.
          </p>
        </>
      )
    })()}
  </div>
)}

          </section>
        )}

        {page === 'Verification' && (
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h3>Project verification</h3>
                <p>Review project status and available similarity results.</p>
              </div>
            </div>

            

<div className="verification-form">
  <h4>Verify project ownership</h4>
  <p className="field-help">
    Select the original ZIP archive to check its fingerprint
    against the blockchain registry.
  </p>

  <div className="upload-zone">
    <div className="upload-zone-icon" aria-hidden="true">⌕</div>
    <strong>
      {verificationFile
        ? verificationFile.name
        : 'Select a project ZIP to verify'}
    </strong>
    <p>
      {verificationFile
        ? `${(verificationFile.size / (1024 * 1024)).toFixed(2)} MB · File selected`
        : 'Choose the same ZIP archive that was registered earlier.'}
    </p>

    <input
      id="verification-file"
      className="source-file-input"
      type="file"
      accept=".zip,application/zip"
      onChange={event => {
        setVerificationFile(event.target.files?.[0] ?? null)
        setVerificationResult(null)
        setMessage('')
      }}
    />

    <label className="upload-button" htmlFor="verification-file">
      {verificationFile ? 'Choose another file' : 'Browse files'}
    </label>
  </div>

  <button
    className="primary-button"
    onClick={verifyProjectFile}
    disabled={verificationBusy}
  >
    {verificationBusy ? 'Verifying...' : 'Verify on blockchain'}
  </button>

  {message && <p className="message">{message}</p>}

  {verificationResult && (
    <div className="verification-details">
      <div>
        <small>Blockchain registration</small>
        <strong>
          {verificationResult.isRegistered ? 'Registered' : 'Not registered'}
        </strong>
      </div>

      {verificationResult.isRegistered && (
        <>
          <div>
            <small>Owner wallet</small>
            <strong>{verificationResult.owner}</strong>
          </div>
          <div>
            <small>Registration timestamp</small>
            <strong>
              {new Date(
                verificationResult.timestamp * 1000
              ).toLocaleString()}
            </strong>
          </div>
        </>
      )}
    </div>
  )}
</div>


            {projects.map(project => (
              <article className="verification-card" key={project.id}>
                <div className="verification-top">
                  <div>
                    <h4>{project.name}</h4>
                    <p>{project.team}</p>
                  </div>
                  <span className={`status ${project.status.toLowerCase()}`}>{project.status}</span>
                </div>
                <div className="verification-details">
                  <div>
                    <small>Similarity score</small>
                    <strong>{project.similarity === null ? 'Not available' : `${project.similarity}%`}</strong>
                  </div>
                  <div>
                    <small>Blockchain status</small>
                    <strong>Not connected</strong>
                  </div>
                </div>
              </article>
            ))}

            <p className="demo-note">Similarity scores and verification statuses are illustrative. Real results require connection to the AI and blockchain modules.</p>
          </section>
        )}

        <footer className="footer">CodeProof · Source code originality and verification</footer>
      </main>
    </div>
  )
}

export default App