import type { WorkflowRun, WorkflowOutcome, GroupedWorkflowRuns, Comment } from '../types/github'

/**
 * Extract workflow outcome from issue comments
 * Looks for Claude workflow outputs in comments
 */
export function extractWorkflowOutcome(comments: Comment[]): WorkflowOutcome | null {
  // Look for comments from GitHub Actions bot or workflow outputs
  for (const comment of comments.reverse()) {
    const body = comment.body.toLowerCase()
    
    // Check for triage output
    if (body.includes('triage') && body.includes('analysis')) {
      return {
        stage: 'triage',
        content: comment.body,
        timestamp: comment.created_at,
      }
    }
    
    // Check for planning output
    if (body.includes('implementation plan') || body.includes('planning')) {
      return {
        stage: 'plan',
        content: comment.body,
        timestamp: comment.created_at,
      }
    }
    
    // Check for prioritization output
    if (body.includes('prioritization') || body.includes('priority')) {
      return {
        stage: 'prioritize',
        content: comment.body,
        timestamp: comment.created_at,
      }
    }
  }
  
  return null
}

/**
 * Group workflow runs by their associated issue
 */
export function groupWorkflowsByIssue(
  runs: WorkflowRun[],
  issues: Map<number, { title: string; url: string }>
): GroupedWorkflowRuns[] {
  const grouped = new Map<number, WorkflowRun[]>()
  
  // Group runs by issue number
  for (const run of runs) {
    if (run.issue_number) {
      const existing = grouped.get(run.issue_number) || []
      existing.push(run)
      grouped.set(run.issue_number, existing)
    }
  }
  
  // Convert to array format
  const result: GroupedWorkflowRuns[] = []
  for (const [issueNumber, runs] of grouped.entries()) {
    const issueInfo = issues.get(issueNumber)
    if (issueInfo) {
      result.push({
        issueNumber,
        issueTitle: issueInfo.title,
        issueUrl: issueInfo.url,
        runs: runs.sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        ),
      })
    }
  }
  
  // Sort by most recent workflow run
  return result.sort((a, b) => {
    const aLatest = a.runs[0]?.created_at || ''
    const bLatest = b.runs[0]?.created_at || ''
    return new Date(bLatest).getTime() - new Date(aLatest).getTime()
  })
}

/**
 * Get workflow type from workflow name
 */
export function getWorkflowType(workflowName: string): string {
  const name = workflowName.toLowerCase()
  if (name.includes('triage')) return 'triage'
  if (name.includes('plan')) return 'plan'
  if (name.includes('prioritize')) return 'prioritize'
  if (name.includes('implement')) return 'implement'
  return 'unknown'
}

/**
 * Get icon/emoji for workflow type
 */
export function getWorkflowTypeIcon(type: string): string {
  switch (type) {
    case 'triage': return '🔍'
    case 'plan': return '📋'
    case 'prioritize': return '⚖️'
    case 'implement': return '⚙️'
    default: return '❓'
  }
}
