import type {
  Issue,
  PullRequest,
  WorkflowRun,
  WorkflowStatus,
  IssueFilters,
  PRFilters,
  WorkflowFilters,
} from '../types/github'

export class GitHubAPIClient {
  private token: string
  private owner: string
  private repo: string
  private baseUrl: string

  constructor(token: string, owner: string, repo: string, baseUrl: string = 'https://api.github.com') {
    this.token = token
    this.owner = owner
    this.repo = repo
    this.baseUrl = baseUrl
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        ...options.headers,
      },
    })

    if (!response.ok) {
      const errorBody = await response.text()
      throw new Error(`GitHub API error: ${response.status} ${response.statusText} - ${errorBody}`)
    }

    // Check rate limiting
    const remaining = response.headers.get('X-RateLimit-Remaining')
    if (remaining && parseInt(remaining) < 10) {
      console.warn(`GitHub API rate limit low: ${remaining} requests remaining`)
    }

    return response.json()
  }

  // Extract Trace_ID from issue/PR body
  private extractTraceId(body: string | null): string | undefined {
    if (!body) return undefined
    const match = body.match(/Trace[_-]ID:\s*([a-zA-Z0-9-]+)/)
    return match ? match[1] : undefined
  }

  // Issue queries
  async getIssuesByStage(stage: string): Promise<Issue[]> {
    const issues = await this.request<Issue[]>(
      `/repos/${this.owner}/${this.repo}/issues?labels=stage:${stage}&state=all&per_page=100`
    )
    return issues.map(issue => ({
      ...issue,
      trace_id: this.extractTraceId(issue.body),
    }))
  }

  async getIssuesByRequestType(requestType: string): Promise<Issue[]> {
    const issues = await this.request<Issue[]>(
      `/repos/${this.owner}/${this.repo}/issues?labels=request:${requestType}&state=all&per_page=100`
    )
    return issues.map(issue => ({
      ...issue,
      trace_id: this.extractTraceId(issue.body),
    }))
  }

  async getIssuesAwaitingApproval(): Promise<Issue[]> {
    const implementationApproval = await this.request<Issue[]>(
      `/repos/${this.owner}/${this.repo}/issues?labels=stage:awaiting-implementation-approval&state=open&per_page=100`
    )
    const deployApproval = await this.request<Issue[]>(
      `/repos/${this.owner}/${this.repo}/issues?labels=stage:awaiting-deploy-approval&state=open&per_page=100`
    )
    
    const allIssues = [...implementationApproval, ...deployApproval]
    return allIssues.map(issue => ({
      ...issue,
      trace_id: this.extractTraceId(issue.body),
    }))
  }

  async getAllIssues(filters?: IssueFilters): Promise<Issue[]> {
    let labels: string[] = []
    
    if (filters?.stage) {
      labels.push(`stage:${filters.stage}`)
    }
    if (filters?.requestType) {
      labels.push(`request:${filters.requestType}`)
    }
    if (filters?.priority) {
      labels.push(`priority:${filters.priority}`)
    }
    if (filters?.source) {
      labels.push(`source:${filters.source}`)
    }

    const labelQuery = labels.length > 0 ? `&labels=${labels.join(',')}` : ''
    const issues = await this.request<Issue[]>(
      `/repos/${this.owner}/${this.repo}/issues?state=all&per_page=100${labelQuery}`
    )
    
    let filteredIssues = issues.map(issue => ({
      ...issue,
      trace_id: this.extractTraceId(issue.body),
    }))

    // Apply date filters
    if (filters?.dateFrom) {
      const fromDate = new Date(filters.dateFrom)
      filteredIssues = filteredIssues.filter(issue => new Date(issue.created_at) >= fromDate)
    }
    if (filters?.dateTo) {
      const toDate = new Date(filters.dateTo)
      filteredIssues = filteredIssues.filter(issue => new Date(issue.created_at) <= toDate)
    }

    return filteredIssues
  }

  async getIssue(issueNumber: number): Promise<Issue> {
    const issue = await this.request<Issue>(
      `/repos/${this.owner}/${this.repo}/issues/${issueNumber}`
    )
    return {
      ...issue,
      trace_id: this.extractTraceId(issue.body),
    }
  }

  // Pull Request queries
  async getPullRequestsByLabel(label: string, filters?: PRFilters): Promise<PullRequest[]> {
    const state = filters?.state || 'all'
    const prs = await this.request<PullRequest[]>(
      `/repos/${this.owner}/${this.repo}/pulls?state=${state}&per_page=100`
    )
    
    // Filter by label (GitHub API doesn't support label filtering for PRs directly)
    let filteredPRs = prs.filter(pr => 
      pr.labels.some(l => l.name === label)
    ).map(pr => ({
      ...pr,
      trace_id: this.extractTraceId(pr.body),
    }))

    // Apply date filters
    if (filters?.dateFrom) {
      const fromDate = new Date(filters.dateFrom)
      filteredPRs = filteredPRs.filter(pr => new Date(pr.created_at) >= fromDate)
    }
    if (filters?.dateTo) {
      const toDate = new Date(filters.dateTo)
      filteredPRs = filteredPRs.filter(pr => new Date(pr.created_at) <= toDate)
    }

    return filteredPRs
  }

  async getPullRequest(prNumber: number): Promise<PullRequest> {
    const pr = await this.request<PullRequest>(
      `/repos/${this.owner}/${this.repo}/pulls/${prNumber}`
    )
    return {
      ...pr,
      trace_id: this.extractTraceId(pr.body),
    }
  }

  // Workflow queries
  async getRecentWorkflowRuns(limit: number = 50, filters?: WorkflowFilters): Promise<WorkflowRun[]> {
    const runs = await this.request<{ workflow_runs: WorkflowRun[] }>(
      `/repos/${this.owner}/${this.repo}/actions/runs?per_page=${limit}`
    )
    
    let filteredRuns = runs.workflow_runs

    // Apply filters
    if (filters?.workflowType) {
      filteredRuns = filteredRuns.filter(run => 
        run.name.toLowerCase().includes(filters.workflowType!.toLowerCase())
      )
    }
    if (filters?.status) {
      filteredRuns = filteredRuns.filter(run => run.status === filters.status)
    }
    if (filters?.dateFrom) {
      const fromDate = new Date(filters.dateFrom)
      filteredRuns = filteredRuns.filter(run => new Date(run.created_at) >= fromDate)
    }
    if (filters?.dateTo) {
      const toDate = new Date(filters.dateTo)
      filteredRuns = filteredRuns.filter(run => new Date(run.created_at) <= toDate)
    }

    return filteredRuns
  }

  async getWorkflowRunStatus(runId: number): Promise<WorkflowStatus> {
    return this.request<WorkflowStatus>(
      `/repos/${this.owner}/${this.repo}/actions/runs/${runId}`
    )
  }

  // Approval actions
  async approveImplementation(issueNumber: number): Promise<void> {
    await this.addLabel(issueNumber, 'stage:implement')
    await this.removeLabel(issueNumber, 'stage:awaiting-implementation-approval')
  }

  async denyImplementation(issueNumber: number): Promise<void> {
    await this.addLabel(issueNumber, 'stage:blocked')
    await this.removeLabel(issueNumber, 'stage:awaiting-implementation-approval')
    
    // Add comment explaining denial
    await this.addComment(issueNumber, 'Implementation denied by administrator.')
  }

  async approveDeployment(issueNumber: number): Promise<void> {
    // Deployment approval is handled by merging the PR
    // This method adds a comment to indicate approval
    await this.addComment(issueNumber, 'Deployment approved by administrator. Please merge the associated PR.')
  }

  async denyDeployment(issueNumber: number): Promise<void> {
    await this.addLabel(issueNumber, 'stage:blocked')
    await this.removeLabel(issueNumber, 'stage:awaiting-deploy-approval')
    
    // Add comment explaining denial
    await this.addComment(issueNumber, 'Deployment denied by administrator.')
  }

  // Label management
  async addLabel(issueNumber: number, label: string): Promise<void> {
    await this.request(
      `/repos/${this.owner}/${this.repo}/issues/${issueNumber}/labels`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ labels: [label] }),
      }
    )
  }

  async removeLabel(issueNumber: number, label: string): Promise<void> {
    try {
      await this.request(
        `/repos/${this.owner}/${this.repo}/issues/${issueNumber}/labels/${encodeURIComponent(label)}`,
        {
          method: 'DELETE',
        }
      )
    } catch (error) {
      // Ignore 404 errors (label doesn't exist)
      if (error instanceof Error && !error.message.includes('404')) {
        throw error
      }
    }
  }

  // Comment management
  async addComment(issueNumber: number, body: string): Promise<void> {
    await this.request(
      `/repos/${this.owner}/${this.repo}/issues/${issueNumber}/comments`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ body }),
      }
    )
  }

  // Rate limit check
  async getRateLimit(): Promise<{ remaining: number; limit: number; reset: number }> {
    const response = await this.request<{
      rate: { remaining: number; limit: number; reset: number }
    }>('/rate_limit')
    return response.rate
  }
}
