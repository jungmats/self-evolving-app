import { useEffect, useState } from 'react'
import { useGitHub } from '../context/GitHubContext'
import type { Issue } from '../types/github'
import { IssueCard } from './IssueCard'
import './IssuesTab.css'

type SortField = 'number' | 'title' | 'stage' | 'priority' | 'created' | 'updated'
type SortDirection = 'asc' | 'desc'

export function IssuesTab() {
  const { client } = useGitHub()
  const [issues, setIssues] = useState<Issue[]>([])
  const [filteredIssues, setFilteredIssues] = useState<Issue[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Search and filters
  const [searchTerm, setSearchTerm] = useState('')
  const [stageFilter, setStageFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  // Sorting
  const [sortField, setSortField] = useState<SortField>('updated')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')

  useEffect(() => {
    loadIssues()
  }, [])

  useEffect(() => {
    applyFiltersAndSort()
  }, [issues, searchTerm, stageFilter, typeFilter, priorityFilter, sourceFilter, dateFrom, dateTo, sortField, sortDirection])

  async function loadIssues() {
    try {
      setLoading(true)
      setError(null)
      const allIssues = await client.getAllIssues()
      setIssues(allIssues)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load issues')
    } finally {
      setLoading(false)
    }
  }

  function applyFiltersAndSort() {
    let filtered = [...issues]

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      filtered = filtered.filter(issue =>
        issue.title.toLowerCase().includes(term) ||
        issue.number.toString().includes(term) ||
        issue.trace_id?.toLowerCase().includes(term) ||
        issue.body?.toLowerCase().includes(term)
      )
    }

    // Stage filter
    if (stageFilter) {
      filtered = filtered.filter(issue =>
        issue.labels.some(label => label.name === `stage:${stageFilter}`)
      )
    }

    // Type filter
    if (typeFilter) {
      filtered = filtered.filter(issue =>
        issue.labels.some(label => label.name === `request:${typeFilter}`)
      )
    }

    // Priority filter
    if (priorityFilter) {
      filtered = filtered.filter(issue =>
        issue.labels.some(label => label.name === `priority:${priorityFilter}`)
      )
    }

    // Source filter
    if (sourceFilter) {
      filtered = filtered.filter(issue =>
        issue.labels.some(label => label.name === `source:${sourceFilter}`)
      )
    }

    // Date filters
    if (dateFrom) {
      const fromDate = new Date(dateFrom)
      filtered = filtered.filter(issue => new Date(issue.created_at) >= fromDate)
    }
    if (dateTo) {
      const toDate = new Date(dateTo)
      toDate.setHours(23, 59, 59, 999)
      filtered = filtered.filter(issue => new Date(issue.created_at) <= toDate)
    }

    // Sort
    filtered.sort((a, b) => {
      let aVal: any
      let bVal: any

      switch (sortField) {
        case 'number':
          aVal = a.number
          bVal = b.number
          break
        case 'title':
          aVal = a.title.toLowerCase()
          bVal = b.title.toLowerCase()
          break
        case 'stage':
          aVal = a.labels.find(l => l.name.startsWith('stage:'))?.name || ''
          bVal = b.labels.find(l => l.name.startsWith('stage:'))?.name || ''
          break
        case 'priority':
          aVal = a.labels.find(l => l.name.startsWith('priority:'))?.name || 'priority:p9'
          bVal = b.labels.find(l => l.name.startsWith('priority:'))?.name || 'priority:p9'
          break
        case 'created':
          aVal = new Date(a.created_at).getTime()
          bVal = new Date(b.created_at).getTime()
          break
        case 'updated':
          aVal = new Date(a.updated_at).getTime()
          bVal = new Date(b.updated_at).getTime()
          break
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1
      return 0
    })

    setFilteredIssues(filtered)
  }

  function clearFilters() {
    setSearchTerm('')
    setStageFilter('')
    setTypeFilter('')
    setPriorityFilter('')
    setSourceFilter('')
    setDateFrom('')
    setDateTo('')
  }

  function handleSort(field: SortField) {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  const hasActiveFilters = searchTerm || stageFilter || typeFilter || priorityFilter || sourceFilter || dateFrom || dateTo

  if (loading) {
    return (
      <div className="tab-content">
        <h2>Issues</h2>
        <p>Loading issues...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="tab-content">
        <h2>Issues</h2>
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
        <h2>Issues ({filteredIssues.length})</h2>
        <button onClick={loadIssues} className="refresh-button">
          Refresh
        </button>
      </div>

      <div className="search-section">
        <input
          type="text"
          placeholder="Search by title, number, trace ID, or description..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input-full"
        />
      </div>

      <div className="filters-section">
        <select
          value={stageFilter}
          onChange={(e) => setStageFilter(e.target.value)}
          className="filter-select"
        >
          <option value="">All Stages</option>
          <option value="triage">Triage</option>
          <option value="plan">Plan</option>
          <option value="prioritize">Prioritize</option>
          <option value="awaiting-implementation-approval">Awaiting Implementation Approval</option>
          <option value="implement">Implement</option>
          <option value="pr-opened">PR Opened</option>
          <option value="awaiting-deploy-approval">Awaiting Deploy Approval</option>
          <option value="blocked">Blocked</option>
          <option value="done">Done</option>
        </select>

        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="filter-select"
        >
          <option value="">All Types</option>
          <option value="bug">Bug</option>
          <option value="feature">Feature</option>
          <option value="investigate">Investigate</option>
        </select>

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

        {hasActiveFilters && (
          <button onClick={clearFilters} className="clear-filters-button">
            Clear Filters
          </button>
        )}
      </div>

      <div className="sort-section">
        <span className="sort-label">Sort by:</span>
        <button
          className={`sort-button ${sortField === 'updated' ? 'active' : ''}`}
          onClick={() => handleSort('updated')}
        >
          Updated {sortField === 'updated' && (sortDirection === 'asc' ? '↑' : '↓')}
        </button>
        <button
          className={`sort-button ${sortField === 'created' ? 'active' : ''}`}
          onClick={() => handleSort('created')}
        >
          Created {sortField === 'created' && (sortDirection === 'asc' ? '↑' : '↓')}
        </button>
        <button
          className={`sort-button ${sortField === 'number' ? 'active' : ''}`}
          onClick={() => handleSort('number')}
        >
          Number {sortField === 'number' && (sortDirection === 'asc' ? '↑' : '↓')}
        </button>
        <button
          className={`sort-button ${sortField === 'priority' ? 'active' : ''}`}
          onClick={() => handleSort('priority')}
        >
          Priority {sortField === 'priority' && (sortDirection === 'asc' ? '↑' : '↓')}
        </button>
        <button
          className={`sort-button ${sortField === 'stage' ? 'active' : ''}`}
          onClick={() => handleSort('stage')}
        >
          Stage {sortField === 'stage' && (sortDirection === 'asc' ? '↑' : '↓')}
        </button>
      </div>

      <div className="issues-list">
        {filteredIssues.length === 0 ? (
          <p className="no-issues">No issues found matching the current filters.</p>
        ) : (
          filteredIssues.map(issue => (
            <IssueCard key={issue.id} issue={issue} />
          ))
        )}
      </div>
    </div>
  )
}
