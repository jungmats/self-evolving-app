import { useEffect, useState } from 'react'
import { useGitHub } from '../context/GitHubContext'
import type { Issue } from '../types/github'
import { getRequestTypeLabel, getPriorityLabel } from '../utils/labelUtils'
import { formatTimeAgo } from '../utils/timeUtils'
import './IssuesByStageTab.css'
import './ApprovalsRequiredTab.css'

export function ApprovalsRequiredTab() {
  const { client } = useGitHub()
  const [implementationApprovals, setImplementationApprovals] = useState<Issue[]>([])
  const [deploymentApprovals, setDeploymentApprovals] = useState<Issue[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [processingIssue, setProcessingIssue] = useState<number | null>(null)

  useEffect(() => {
    loadApprovals()
  }, [])

  async function loadApprovals() {
    try {
      setLoading(true)
      setError(null)
      
      const implApprovals = await client.getIssuesByStage('awaiting-implementation-approval')
      const deployApprovals = await client.getIssuesByStage('awaiting-deploy-approval')
      
      setImplementationApprovals(implApprovals)
      setDeploymentApprovals(deployApprovals)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load approvals')
    } finally {
      setLoading(false)
    }
  }

  async function handleApproveImplementation(issueNumber: number) {
    if (!confirm(`Approve implementation for issue #${issueNumber}?`)) {
      return
    }

    try {
      setProcessingIssue(issueNumber)
      await client.approveImplementation(issueNumber)
      await loadApprovals()
    } catch (err) {
      alert(`Failed to approve: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setProcessingIssue(null)
    }
  }

  async function handleDenyImplementation(issueNumber: number) {
    if (!confirm(`Deny implementation for issue #${issueNumber}? This will block the issue.`)) {
      return
    }

    try {
      setProcessingIssue(issueNumber)
      await client.denyImplementation(issueNumber)
      await loadApprovals()
    } catch (err) {
      alert(`Failed to deny: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setProcessingIssue(null)
    }
  }

  async function handleApproveDeployment(issueNumber: number) {
    if (!confirm(`Approve deployment for issue #${issueNumber}? Please merge the associated PR.`)) {
      return
    }

    try {
      setProcessingIssue(issueNumber)
      await client.approveDeployment(issueNumber)
      alert('Deployment approved. Please merge the associated PR to trigger deployment.')
      await loadApprovals()
    } catch (err) {
      alert(`Failed to approve: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setProcessingIssue(null)
    }
  }

  async function handleDenyDeployment(issueNumber: number) {
    if (!confirm(`Deny deployment for issue #${issueNumber}? This will block the issue.`)) {
      return
    }

    try {
      setProcessingIssue(issueNumber)
      await client.denyDeployment(issueNumber)
      await loadApprovals()
    } catch (err) {
      alert(`Failed to deny: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setProcessingIssue(null)
    }
  }

  function extractPlanSummary(body: string | null): string {
    if (!body) return 'No plan available'
    
    // Try to extract a summary from the issue body
    const lines = body.split('\n')
    const summaryLine = lines.find(line => 
      line.toLowerCase().includes('summary') || 
      line.toLowerCase().includes('plan')
    )
    
    if (summaryLine) {
      return summaryLine.substring(0, 200) + (summaryLine.length > 200 ? '...' : '')
    }
    
    return body.substring(0, 200) + (body.length > 200 ? '...' : '')
  }

  if (loading) {
    return (
      <div className="tab-content">
        <h2>Approvals Required</h2>
        <p>Loading approvals...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="tab-content">
        <h2>Approvals Required</h2>
        <div className="error-message">
          <p>Error: {error}</p>
          <button onClick={loadApprovals}>Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="tab-content">
      <div className="tab-header">
        <h2>Approvals Required</h2>
        <div className="controls">
          <button onClick={loadApprovals} className="refresh-button">
            Refresh
          </button>
        </div>
      </div>

      <div className="stages-container">
        {/* Implementation Approvals */}
        <div className="stage-section">
          <h3 className="stage-title">
            Implementation Approval
            <span className="issue-count">({implementationApprovals.length})</span>
          </h3>
          
          {implementationApprovals.length === 0 ? (
            <p className="no-issues">No issues awaiting implementation approval</p>
          ) : (
            <div className="issues-list">
              {implementationApprovals.map(issue => (
                <div key={issue.id} className="issue-card approval-card">
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
                  
                  <div className="plan-summary">
                    <strong>Plan Summary:</strong>
                    <p>{extractPlanSummary(issue.body)}</p>
                  </div>
                  
                  <div className="issue-meta">
                    {issue.trace_id && (
                      <span className="trace-id">
                        Trace ID: {issue.trace_id}
                      </span>
                    )}
                    {getPriorityLabel(issue.labels) && (
                      <span className="priority">
                        Priority: {getPriorityLabel(issue.labels)?.toUpperCase()}
                      </span>
                    )}
                    <span className="created-at">
                      Created: {formatTimeAgo(issue.created_at)}
                    </span>
                  </div>

                  <div className="approval-actions">
                    <button
                      onClick={() => handleApproveImplementation(issue.number)}
                      disabled={processingIssue === issue.number}
                      className="approve-button"
                    >
                      {processingIssue === issue.number ? 'Processing...' : 'Approve'}
                    </button>
                    <button
                      onClick={() => handleDenyImplementation(issue.number)}
                      disabled={processingIssue === issue.number}
                      className="deny-button"
                    >
                      {processingIssue === issue.number ? 'Processing...' : 'Deny'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Deployment Approvals */}
        <div className="stage-section">
          <h3 className="stage-title">
            Deployment Approval
            <span className="issue-count">({deploymentApprovals.length})</span>
          </h3>
          
          {deploymentApprovals.length === 0 ? (
            <p className="no-issues">No issues awaiting deployment approval</p>
          ) : (
            <div className="issues-list">
              {deploymentApprovals.map(issue => (
                <div key={issue.id} className="issue-card approval-card">
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
                    {getPriorityLabel(issue.labels) && (
                      <span className="priority">
                        Priority: {getPriorityLabel(issue.labels)?.toUpperCase()}
                      </span>
                    )}
                    <span className="created-at">
                      Created: {formatTimeAgo(issue.created_at)}
                    </span>
                  </div>

                  <div className="approval-actions">
                    <button
                      onClick={() => handleApproveDeployment(issue.number)}
                      disabled={processingIssue === issue.number}
                      className="approve-button"
                    >
                      {processingIssue === issue.number ? 'Processing...' : 'Approve'}
                    </button>
                    <button
                      onClick={() => handleDenyDeployment(issue.number)}
                      disabled={processingIssue === issue.number}
                      className="deny-button"
                    >
                      {processingIssue === issue.number ? 'Processing...' : 'Deny'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
