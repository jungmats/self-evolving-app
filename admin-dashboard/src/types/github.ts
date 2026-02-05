// GitHub API Types

export interface Label {
  id: number
  name: string
  color: string
  description: string | null
}

export interface User {
  login: string
  id: number
  type: string
}

export interface Issue {
  id: number
  number: number
  title: string
  body: string | null
  state: string
  labels: Label[]
  created_at: string
  updated_at: string
  user: User
  html_url: string
  trace_id?: string  // Extracted from body
}

export interface PullRequest {
  id: number
  number: number
  title: string
  body: string | null
  state: string
  labels: Label[]
  head: {
    sha: string
    ref: string
  }
  base: {
    sha: string
    ref: string
  }
  created_at: string
  updated_at: string
  merged_at: string | null
  html_url: string
  trace_id?: string  // Extracted from body
}

export interface WorkflowRun {
  id: number
  name: string
  status: string
  conclusion: string | null
  created_at: string
  updated_at: string
  html_url: string
  run_number: number
  event: string
  issue_number?: number  // Extracted from workflow context
}

export interface WorkflowStatus {
  id: number
  status: string
  conclusion: string | null
}

// Comment on an issue
export interface Comment {
  id: number
  body: string
  user: User
  created_at: string
  updated_at: string
}

// Workflow outcome parsed from comments
export interface WorkflowOutcome {
  stage: string
  content: string
  timestamp: string
}

// Grouped workflow runs by issue
export interface GroupedWorkflowRuns {
  issueNumber: number
  issueTitle: string
  issueUrl: string
  runs: WorkflowRun[]
}

// Filter types
export interface IssueFilters {
  stage?: string
  requestType?: string
  priority?: string
  source?: string
  dateFrom?: string
  dateTo?: string
}

export interface PRFilters {
  state?: 'open' | 'closed' | 'all'
  dateFrom?: string
  dateTo?: string
}

export interface WorkflowFilters {
  workflowType?: string
  status?: string
  dateFrom?: string
  dateTo?: string
}
