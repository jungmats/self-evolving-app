import { useEffect, useState } from 'react'
import { useGitHub } from '../context/GitHubContext'
import type { Issue } from '../types/github'
import { getStageLabel, getPriorityLabel, getSourceLabel } from '../utils/labelUtils'
import { formatTimeAgo } from '../utils/timeUtils'
import './IssuesByStageTab.css'

const REQUEST_TYPES = ['bug', 'feature', 'investigate']

export function IssuesByRequestTypeTab() {
  const { client } = useGitHub()
  const [issuesByType, setIssuesByType] = useState<Record<string, Issue[]>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [priorityFilter, setPriorityFilter] = useState<string>('')
  const [sourceFilter, setSourceFilter] = useState<string>('')
  const [dateFrom, setDateFrom] = useState<string>('')
  const [dateTo, setDateTo] = useState<string>('')

  useEffect(() => {
    loadIssues()
  }, [])

  async function loadIssues() {
    try {
      setLoading(true)
      setError(null)
      
      const issuesMap: Record<string, Issue[]> = {}
      
      // Load issues for each request type
      await Promise.all(
        REQUEST_TYPES.map(async (type) => {
          const issues = await client.getIssuesByRequestType(type)
          issuesMap[type] = issues
        })
      )
      
      setIssuesByType(issuesMap)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load issues')
    } finally {
      setLoading(false)
    }
  }

  function filterIssues(issues: Issue[]): Issue[] {
    let filtered = issues

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      filtered = filtered.filter(issue =>
        issue.title.toLowerCase().includes(term) ||
        issue.number.toString().includes(term) ||
        issue.trace_id?.toLowerCase().includes(term)
      )
    }

    // Priority filter
    if (priorityFilter) {
      filtered = filtered.filter(issue => 
        getPriorityLabel(issue.labels) === priorityFilter
      )
    }

    // Source filter
    if (sourceFilter) {
      filtered = filtered.filter(issue => 
        getSourceLabel(issue.labels) === sourceFilter
      )
    }

    // Date filters
    if (dateFrom) {
      const fromDate = new Date(dateFrom)
      filtered = filtered.filter(issue => new Date(issue.created_at) >= fromDate)
    }
    if (dateTo) {
      const toDate = new Date(dateTo)
      filtered = filtered.filter(issue => new Date(issue.created_at) <= toDate)
    }

    return filtered
  }

  if (loading) {
    return (
      <div className="tab-content">
        <h2>Issues by Request Type</h2>
        <p>Loading issues...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="tab-content">
        <h2>Issues by Request Type</h2>
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
        <h2>Issues by Request Type</h2>
        <div className="controls">
          <input
            type="text"
            placeholder="Search..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <button onClick={loadIssues} className="refresh-button">
            Refresh
          </button>
        </div>
      </div>

      <div className="filters">
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="filter-select"
        >
          <option value="">All Priorities</option>
          <option value="p0">P0</option>
          <option value="p1">P1</option>
          <option value="p2">P2</option>
        </select>

        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
          className="filter-select"
        >
          <option value="">All Sources</option>
          <option value="user">User</option>
          <option value="monitor">Monitor</option>
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
      </div>

      <div className="stages-container">
        {REQUEST_TYPES.map(type => {
          const issues = filterIssues(issuesByType[type] || [])
          
          return (
            <div key={type} className="stage-section">
              <h3 className="stage-title">
                {type.toUpperCase()}
                <span className="issue-count">({issues.length})</span>
              </h3>
              
              {issues.length === 0 ? (
                <p className="no-issues">No {type} issues found</p>
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
                        <span className={`request-type ${getStageLabel(issue.labels)}`}>
                          {getStageLabel(issue.labels) || 'unknown'}
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
