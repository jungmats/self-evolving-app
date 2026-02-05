import { useEffect, useState } from 'react'
import { useGitHub } from '../context/GitHubContext'
import type { Issue } from '../types/github'
import { getRequestTypeLabel } from '../utils/labelUtils'
import { calculateTimeInStage } from '../utils/timeUtils'
import './IssuesByStageTab.css'

const STAGES = [
  'triage',
  'plan',
  'prioritize',
  'awaiting-implementation-approval',
  'implement',
  'pr-opened',
  'awaiting-deploy-approval',
  'blocked',
  'done',
]

export function IssuesByStageTab() {
  const { client } = useGitHub()
  const [issuesByStage, setIssuesByStage] = useState<Record<string, Issue[]>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    loadIssues()
  }, [])

  async function loadIssues() {
    try {
      setLoading(true)
      setError(null)
      
      const issuesMap: Record<string, Issue[]> = {}
      
      // Load issues for each stage
      await Promise.all(
        STAGES.map(async (stage) => {
          const issues = await client.getIssuesByStage(stage)
          issuesMap[stage] = issues
        })
      )
      
      setIssuesByStage(issuesMap)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load issues')
    } finally {
      setLoading(false)
    }
  }

  function filterIssues(issues: Issue[]): Issue[] {
    if (!searchTerm) return issues
    
    const term = searchTerm.toLowerCase()
    return issues.filter(issue =>
      issue.title.toLowerCase().includes(term) ||
      issue.number.toString().includes(term) ||
      issue.trace_id?.toLowerCase().includes(term)
    )
  }

  if (loading) {
    return (
      <div className="tab-content">
        <h2>Issues by Stage</h2>
        <p>Loading issues...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="tab-content">
        <h2>Issues by Stage</h2>
        <div className="error-message">
          <p>Error: {error}</p>
          <button onClick={loadIssues}>Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="tab-content">
      <div className="tab-header">
        <h2>Issues by Stage</h2>
        <div className="controls">
          <input
            type="text"
            placeholder="Search by title, number, or Trace ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <button onClick={loadIssues} className="refresh-button">
            Refresh
          </button>
        </div>
      </div>

      <div className="stages-container">
        {STAGES.map(stage => {
          const issues = filterIssues(issuesByStage[stage] || [])
          
          return (
            <div key={stage} className="stage-section">
              <h3 className="stage-title">
                {stage.replace(/-/g, ' ').toUpperCase()}
                <span className="issue-count">({issues.length})</span>
              </h3>
              
              {issues.length === 0 ? (
                <p className="no-issues">No issues in this stage</p>
              ) : (
                <div className="issues-list">
                  {issues.map(issue => (
                    <div key={issue.id} className="issue-card">
                      <div className="issue-header">
                        <a
                          href={issue.html_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="issue-number"
                        >
                          #{issue.number}
                        </a>
                        <span className={`request-type ${getRequestTypeLabel(issue.labels)}`}>
                          {getRequestTypeLabel(issue.labels) || 'unknown'}
                        </span>
                      </div>
                      
                      <h4 className="issue-title">{issue.title}</h4>
                      
                      <div className="issue-meta">
                        {issue.trace_id && (
                          <span className="trace-id">
                            Trace ID: {issue.trace_id}
                          </span>
                        )}
                        <span className="time-in-stage">
                          In stage: {calculateTimeInStage(issue.updated_at)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
