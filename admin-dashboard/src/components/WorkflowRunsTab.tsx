import { useEffect, useState } from 'react'
import { useGitHub } from '../context/GitHubContext'
import type { WorkflowRun, GroupedWorkflowRuns } from '../types/github'
import { formatTimeAgo } from '../utils/timeUtils'
import { groupWorkflowsByIssue, getWorkflowType, getWorkflowTypeIcon } from '../utils/workflowUtils'
import { CollapsibleSection } from './CollapsibleSection'
import './IssuesByStageTab.css'
import './WorkflowRunsTab.css'

export function WorkflowRunsTab() {
  const { client } = useGitHub()
  const [workflowRuns, setWorkflowRuns] = useState<WorkflowRun[]>([])
  const [groupedRuns, setGroupedRuns] = useState<GroupedWorkflowRuns[]>([])
  const [ungroupedRuns, setUngroupedRuns] = useState<WorkflowRun[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [workflowTypeFilter, setWorkflowTypeFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [dateFrom, setDateFrom] = useState<string>('')
  const [dateTo, setDateTo] = useState<string>('')
  const [showSkipped, setShowSkipped] = useState<boolean>(false)
  const [groupByIssue, setGroupByIssue] = useState<boolean>(true)

  useEffect(() => {
    loadWorkflowRuns()
  }, [showSkipped])

  useEffect(() => {
    if (groupByIssue) {
      groupWorkflows()
    }
  }, [workflowRuns, groupByIssue])

  async function loadWorkflowRuns() {
    try {
      setLoading(true)
      setError(null)
      
      const runs = await client.getRecentWorkflowRuns(50, {
        workflowType: workflowTypeFilter || undefined,
        status: statusFilter || undefined,
        dateFrom: dateFrom || undefined,
        dateTo: dateTo || undefined,
      }, showSkipped)
      
      setWorkflowRuns(runs)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load workflow runs')
    } finally {
      setLoading(false)
    }
  }

  async function groupWorkflows() {
    // Extract unique issue numbers
    const issueNumbers = new Set<number>()
    workflowRuns.forEach(run => {
      if (run.issue_number) {
        issueNumbers.add(run.issue_number)
      }
    })

    // Fetch issue details
    const issuesMap = new Map<number, { title: string; url: string }>()
    await Promise.all(
      Array.from(issueNumbers).map(async (num) => {
        try {
          const issue = await client.getIssue(num)
          issuesMap.set(num, { title: issue.title, url: issue.html_url })
        } catch (err) {
          console.error(`Failed to fetch issue #${num}:`, err)
        }
      })
    )

    // Group workflows
    const grouped = groupWorkflowsByIssue(workflowRuns, issuesMap)
    setGroupedRuns(grouped)

    // Separate ungrouped runs
    const ungrouped = workflowRuns.filter(run => !run.issue_number)
    setUngroupedRuns(ungrouped)
  }

  if (loading) {
    return (
      <div className="tab-content">
        <h2>Workflow Runs</h2>
        <p>Loading workflow runs...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="tab-content">
        <h2>Workflow Runs</h2>
        <div className="error-message">
          <p>Error: {error}</p>
          <button onClick={loadWorkflowRuns}>Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="tab-content">
      <div className="tab-header">
        <h2>Workflow Runs</h2>
        <div className="controls">
          <button onClick={loadWorkflowRuns} className="refresh-button">
            Refresh
          </button>
        </div>
      </div>

      <div className="filters">
        <select
          value={workflowTypeFilter}
          onChange={(e) => setWorkflowTypeFilter(e.target.value)}
          className="filter-select"
        >
          <option value="">All Workflows</option>
          <option value="triage">Triage</option>
          <option value="plan">Planning</option>
          <option value="prioritize">Prioritization</option>
          <option value="implement">Implementation</option>
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="filter-select"
        >
          <option value="">All Statuses</option>
          <option value="completed">Completed</option>
          <option value="in_progress">In Progress</option>
          <option value="queued">Queued</option>
        </select>

        <input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          className="date-input"
          placeholder="From date"
        />

        <input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          className="date-input"
          placeholder="To date"
        />

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={showSkipped}
            onChange={(e) => setShowSkipped(e.target.checked)}
          />
          Show skipped
        </label>

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={groupByIssue}
            onChange={(e) => setGroupByIssue(e.target.checked)}
          />
          Group by issue
        </label>

        <button onClick={loadWorkflowRuns} className="apply-filters-button">
          Apply Filters
        </button>
      </div>

      {groupByIssue ? (
        <>
          {groupedRuns.length > 0 && (
            <div className="stage-section">
              <h3 className="stage-title">
                Workflows by Issue
                <span className="issue-count">({groupedRuns.length} issues)</span>
              </h3>
              
              <div className="grouped-workflows">
                {groupedRuns.map(group => (
                  <CollapsibleSection
                    key={group.issueNumber}
                    title={`Issue #${group.issueNumber}: ${group.issueTitle}`}
                    badge={`${group.runs.length} runs`}
                  >
                    <div className="workflow-runs-list">
                      {group.runs.map(run => (
                        <WorkflowRunCard key={run.id} run={run} />
                      ))}
                    </div>
                  </CollapsibleSection>
                ))}
              </div>
            </div>
          )}

          {ungroupedRuns.length > 0 && (
            <div className="stage-section">
              <h3 className="stage-title">
                Other Workflows
                <span className="issue-count">({ungroupedRuns.length})</span>
              </h3>
              
              <div className="workflow-runs-list">
                {ungroupedRuns.map(run => (
                  <WorkflowRunCard key={run.id} run={run} />
                ))}
              </div>
            </div>
          )}

          {groupedRuns.length === 0 && ungroupedRuns.length === 0 && (
            <p className="no-issues">No workflow runs found</p>
          )}
        </>
      ) : (
        <div className="stage-section">
          <h3 className="stage-title">
            Recent Workflow Executions
            <span className="issue-count">({workflowRuns.length})</span>
          </h3>
          
          {workflowRuns.length === 0 ? (
            <p className="no-issues">No workflow runs found</p>
          ) : (
            <div className="workflow-runs-list">
              {workflowRuns.map(run => (
                <WorkflowRunCard key={run.id} run={run} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

interface WorkflowRunCardProps {
  run: WorkflowRun
}

function WorkflowRunCard({ run }: WorkflowRunCardProps) {
  const workflowType = getWorkflowType(run.name)
  const icon = getWorkflowTypeIcon(workflowType)

  function calculateDuration(run: WorkflowRun): string {
    const created = new Date(run.created_at)
    const updated = new Date(run.updated_at)
    const diffMs = updated.getTime() - created.getTime()
    const diffSecs = Math.floor(diffMs / 1000)
    const diffMins = Math.floor(diffSecs / 60)
    
    if (diffMins < 1) return `${diffSecs}s`
    if (diffMins < 60) return `${diffMins}m ${diffSecs % 60}s`
    
    const hours = Math.floor(diffMins / 60)
    const mins = diffMins % 60
    return `${hours}h ${mins}m`
  }

  function getStatusClass(status: string, conclusion: string | null): string {
    if (status === 'completed') {
      if (conclusion === 'success') return 'status-success'
      if (conclusion === 'failure') return 'status-failure'
      if (conclusion === 'cancelled') return 'status-cancelled'
      if (conclusion === 'skipped') return 'status-skipped'
    }
    if (status === 'in_progress') return 'status-in-progress'
    if (status === 'queued') return 'status-queued'
    return 'status-unknown'
  }

  function getStatusText(status: string, conclusion: string | null): string {
    if (status === 'completed' && conclusion) {
      return conclusion.toUpperCase()
    }
    return status.toUpperCase().replace('_', ' ')
  }

  return (
    <div className="workflow-run-card">
      <div className="workflow-header">
        <div className="workflow-name-section">
          <span className="workflow-icon">{icon}</span>
          <a
            href={run.html_url}
            target="_blank"
            rel="noopener noreferrer"
            className="workflow-name"
          >
            {run.name}
          </a>
          <span className="run-number">#{run.run_number}</span>
          {run.issue_number && (
            <span className="issue-link">
              (Issue #{run.issue_number})
            </span>
          )}
        </div>
        <span className={`workflow-status ${getStatusClass(run.status, run.conclusion)}`}>
          {getStatusText(run.status, run.conclusion)}
        </span>
      </div>
      
      <div className="workflow-meta">
        <span className="duration">
          Duration: {calculateDuration(run)}
        </span>
        <span className="created-at">
          Started: {formatTimeAgo(run.created_at)}
        </span>
        <span className="event">
          Event: {run.event}
        </span>
      </div>
    </div>
  )
}
