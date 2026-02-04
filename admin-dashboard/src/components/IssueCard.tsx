import { useState, useEffect } from 'react'
import { useGitHub } from '../context/GitHubContext'
import type { Issue, WorkflowOutcome } from '../types/github'
import { getRequestTypeLabel, getStageLabel, getPriorityLabel, getSeverityLabel } from '../utils/labelUtils'
import { calculateTimeInStage, formatTimeAgo } from '../utils/timeUtils'
import { extractWorkflowOutcome } from '../utils/workflowUtils'
import { CollapsibleSection } from './CollapsibleSection'
import './IssueCard.css'

interface IssueCardProps {
  issue: Issue
}

export function IssueCard({ issue }: IssueCardProps) {
  const { client } = useGitHub()
  const [workflowOutcome, setWorkflowOutcome] = useState<WorkflowOutcome | null>(null)
  const [loadingOutcome, setLoadingOutcome] = useState(false)

  const requestType = getRequestTypeLabel(issue.labels)
  const stage = getStageLabel(issue.labels)
  const priority = getPriorityLabel(issue.labels)
  const severity = getSeverityLabel(issue.labels) || extractSeverityFromBody(issue.body)

  function extractSeverityFromBody(body: string | null): string | undefined {
    if (!body) return undefined
    // Match **Severity:** or **Severity** : with flexible spacing
    const match = body.match(/\*\*Severity\*\*\s*:\s*(\w+)/im)
    return match ? match[1].toLowerCase() : undefined
  }

  // Debug: log labels to see what's available
  useEffect(() => {
    console.log(`Issue #${issue.number} labels:`, issue.labels.map(l => l.name))
    console.log(`Severity extracted: "${severity}"`)
    console.log(`Trace ID: "${issue.trace_id}"`)
    console.log(`Issue body preview:`, issue.body?.substring(0, 200))
  }, [issue.number])

  useEffect(() => {
    loadWorkflowOutcome()
  }, [issue.number])

  async function loadWorkflowOutcome() {
    try {
      setLoadingOutcome(true)
      const comments = await client.getIssueComments(issue.number)
      const outcome = extractWorkflowOutcome(comments)
      setWorkflowOutcome(outcome)
    } catch (err) {
      console.error('Failed to load workflow outcome:', err)
    } finally {
      setLoadingOutcome(false)
    }
  }

  function cleanDescription(body: string): string {
    // Remove common metadata lines that are shown elsewhere
    const lines = body.split('\n')
    const filteredLines = lines.filter(line => {
      const trimmed = line.trim()
      // Filter out metadata lines - handle both **Label:** and **Label**:
      return !trimmed.match(/^\*\*(Severity|Priority|Trace[_-]ID|Source|Request Type)\*\*\s*:/i)
    })
    return filteredLines.join('\n').trim()
  }

  return (
    <div className="issue-card-enhanced">
      <div className="issue-card-header">
        <a
          href={issue.html_url}
          target="_blank"
          rel="noopener noreferrer"
          className="issue-number"
        >
          #{issue.number}
        </a>
        <div className="issue-tags">
          {stage && (
            <span className={`tag tag-stage tag-${stage}`}>
              {stage}
            </span>
          )}
          {priority && (
            <span className={`tag tag-priority tag-${priority}`}>
              {priority.toUpperCase()}
            </span>
          )}
          {severity && (
            <span className={`tag tag-severity tag-${severity}`}>
              SEV: {severity.toUpperCase()}
            </span>
          )}
          {requestType && (
            <span className={`tag tag-type tag-${requestType}`}>
              {requestType}
            </span>
          )}
        </div>
      </div>

      <h4 className="issue-title">{issue.title}</h4>

      {issue.body && (
        <div className="issue-description">
          {cleanDescription(issue.body).substring(0, 300)}
          {cleanDescription(issue.body).length > 300 && '...'}
        </div>
      )}

      <div className="issue-meta">
        <span className="meta-item">
          <strong>In stage:</strong> {calculateTimeInStage(issue.updated_at)}
        </span>
        <span className="meta-item">
          <strong>Created:</strong> {formatTimeAgo(issue.created_at)}
        </span>
        <span className="meta-item">
          <strong>Updated:</strong> {formatTimeAgo(issue.updated_at)}
        </span>
        {issue.trace_id && (
          <span className="trace-id-badge">
            {issue.trace_id}
          </span>
        )}
      </div>

      {workflowOutcome && (
        <CollapsibleSection 
          title={`Latest Workflow Outcome: ${workflowOutcome.stage}`}
          badge={formatTimeAgo(workflowOutcome.timestamp)}
        >
          {workflowOutcome.content}
        </CollapsibleSection>
      )}

      {loadingOutcome && (
        <div className="loading-outcome">Loading workflow outcome...</div>
      )}
    </div>
  )
}
