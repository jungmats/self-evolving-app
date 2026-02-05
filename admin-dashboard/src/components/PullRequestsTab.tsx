import { useEffect, useState } from 'react'
import { useGitHub } from '../context/GitHubContext'
import type { PullRequest } from '../types/github'
import { formatTimeAgo } from '../utils/timeUtils'
import './IssuesByStageTab.css'

export function PullRequestsTab() {
  const { client } = useGitHub()
  const [pullRequests, setPullRequests] = useState<PullRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [stateFilter, setStateFilter] = useState<'open' | 'closed' | 'all'>('all')
  const [dateFrom, setDateFrom] = useState<string>('')
  const [dateTo, setDateTo] = useState<string>('')

  useEffect(() => {
    loadPullRequests()
  }, [stateFilter])

  async function loadPullRequests() {
    try {
      setLoading(true)
      setError(null)
      
      const prs = await client.getPullRequestsByLabel('agent:claude', {
        state: stateFilter,
        dateFrom,
        dateTo,
      })
      
      setPullRequests(prs)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load pull requests')
    } finally {
      setLoading(false)
    }
  }

  function filterPullRequests(prs: PullRequest[]): PullRequest[] {
    let filtered = prs

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      filtered = filtered.filter(pr =>
        pr.title.toLowerCase().includes(term) ||
        pr.number.toString().includes(term) ||
        pr.trace_id?.toLowerCase().includes(term)
      )
    }

    // Date filters
    if (dateFrom) {
      const fromDate = new Date(dateFrom)
      filtered = filtered.filter(pr => new Date(pr.created_at) >= fromDate)
    }
    if (dateTo) {
      const toDate = new Date(dateTo)
      filtered = filtered.filter(pr => new Date(pr.created_at) <= toDate)
    }

    return filtered
  }

  function extractLinkedIssue(body: string | null): string | null {
    if (!body) return null
    
    // Match "Fixes #123" or "Refs #123"
    const match = body.match(/(?:Fixes|Refs)\s+#(\d+)/)
    return match ? match[1] : null
  }

  if (loading) {
    return (
      <div className="tab-content">
        <h2>Pull Requests</h2>
        <p>Loading pull requests...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="tab-content">
        <h2>Pull Requests</h2>
        <div className="error-message">
          <p>Error: {error}</p>
          <button onClick={loadPullRequests}>Retry</button>
        </div>
      </div>
    )
  }

  const filteredPRs = filterPullRequests(pullRequests)

  return (
    <div className="tab-content">
      <div className="tab-header">
        <h2>Pull Requests</h2>
        <div className="controls">
          <input
            type="text"
            placeholder="Search by title, number, or Trace ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <button onClick={loadPullRequests} className="refresh-button">
            Refresh
          </button>
        </div>
      </div>

      <div className="filters">
        <select
          value={stateFilter}
          onChange={(e) => setStateFilter(e.target.value as 'open' | 'closed' | 'all')}
          className="filter-select"
        >
          <option value="all">All States</option>
          <option value="open">Open</option>
          <option value="closed">Closed</option>
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

      <div className="stage-section">
        <h3 className="stage-title">
          Agent-Created Pull Requests
          <span className="issue-count">({filteredPRs.length})</span>
        </h3>
        
        {filteredPRs.length === 0 ? (
          <p className="no-issues">No pull requests found</p>
        ) : (
          <div className="issues-list">
            {filteredPRs.map(pr => {
              const linkedIssue = extractLinkedIssue(pr.body)
              const isMerged = pr.merged_at !== null
              
              return (
                <div key={pr.id} className="issue-card">
                  <div className="issue-header">
                    <a
                      href={pr.html_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="issue-number"
                    >
                      #{pr.number}
                    </a>
                    <span className={`request-type ${pr.state}`}>
                      {isMerged ? 'MERGED' : pr.state.toUpperCase()}
                    </span>
                  </div>
                  
                  <h4 className="issue-title">{pr.title}</h4>
                  
                  <div className="issue-meta">
                    {pr.trace_id && (
                      <span className="trace-id">
                        Trace ID: {pr.trace_id}
                      </span>
                    )}
                    {linkedIssue && (
                      <span className="linked-issue">
                        Linked Issue: #{linkedIssue}
                      </span>
                    )}
                    <span className="created-at">
                      Created: {formatTimeAgo(pr.created_at)}
                    </span>
                    {isMerged && pr.merged_at && (
                      <span className="merged-at">
                        Merged: {formatTimeAgo(pr.merged_at)}
                      </span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
