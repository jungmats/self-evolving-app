/**
 * Property-based tests for Admin Dashboard GitHub API Client
 * 
 * Feature: self-evolving-app, Property 5: State Machine Integrity (admin view)
 * 
 * These tests validate that the admin dashboard correctly interprets and displays
 * state machine invariants from GitHub Issues.
 * 
 * **Validates: Requirements 3.4, 10.1**
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { GitHubAPIClient } from '../GitHubAPIClient'
import type { Issue } from '../../types/github'

describe('GitHubAPIClient State Machine Properties', () => {
  let client: GitHubAPIClient
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockFetch = vi.fn()
    // @ts-ignore - Setting global fetch for testing
    globalThis.fetch = mockFetch
    client = new GitHubAPIClient('test-token', 'test-owner', 'test-repo')
  })

  /**
   * Property 5: State Machine Integrity (Admin View)
   * 
   * For any Issue retrieved from GitHub API, the admin dashboard should verify
   * that exactly one stage:* label is present.
   */
  it('should validate that all issues have exactly one stage label', async () => {
    // Create test issues with various label configurations
    const testCases = [
      {
        name: 'valid issue with one stage label',
        issue: createMockIssue(123, 'Test Issue', [
          { name: 'stage:triage' },
          { name: 'request:bug' },
          { name: 'source:user' },
        ]),
        shouldBeValid: true,
      },
      {
        name: 'invalid issue with multiple stage labels',
        issue: createMockIssue(124, 'Invalid Issue', [
          { name: 'stage:triage' },
          { name: 'stage:plan' },
          { name: 'request:bug' },
        ]),
        shouldBeValid: false,
      },
      {
        name: 'invalid issue with no stage label',
        issue: createMockIssue(125, 'No Stage Issue', [
          { name: 'request:bug' },
          { name: 'source:user' },
        ]),
        shouldBeValid: false,
      },
    ]

    for (const testCase of testCases) {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [testCase.issue],
        headers: new Headers(),
      })

      const issues = await client.getIssuesByStage('triage')
      const issue = issues[0]

      // Count stage labels
      const stageLabels = issue.labels.filter(label => label.name.startsWith('stage:'))
      
      if (testCase.shouldBeValid) {
        expect(stageLabels.length).toBe(1)
      } else {
        expect(stageLabels.length).not.toBe(1)
      }
    }
  })

  /**
   * Property 5: State Machine Integrity (Admin View)
   * 
   * For any Issue in a specific stage, the admin dashboard should correctly
   * identify and display the current stage.
   */
  it('should correctly extract stage from issue labels', async () => {
    const stages = [
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

    for (const stage of stages) {
      const issue = createMockIssue(123, `Issue in ${stage}`, [
        { name: `stage:${stage}` },
        { name: 'request:bug' },
      ])

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [issue],
        headers: new Headers(),
      })

      const issues = await client.getIssuesByStage(stage)
      expect(issues.length).toBeGreaterThan(0)
      
      const retrievedIssue = issues[0]
      const stageLabel = retrievedIssue.labels.find(l => l.name.startsWith('stage:'))
      expect(stageLabel?.name).toBe(`stage:${stage}`)
    }
  })

  /**
   * Property 5: State Machine Integrity (Admin View)
   * 
   * For any Issue with a Trace_ID, the admin dashboard should correctly extract
   * and display the Trace_ID for audit purposes.
   */
  it('should extract Trace_ID from issue body for traceability', async () => {
    const testCases = [
      {
        body: 'Issue description\nTrace_ID: abc-123-def\nMore details',
        expectedTraceId: 'abc-123-def',
      },
      {
        body: 'Issue description\nTrace-ID: xyz-456-ghi\nMore details',
        expectedTraceId: 'xyz-456-ghi',
      },
      {
        body: 'Issue without trace ID',
        expectedTraceId: undefined,
      },
    ]

    for (const testCase of testCases) {
      const issue = createMockIssue(123, 'Test Issue', [
        { name: 'stage:triage' },
      ])
      issue.body = testCase.body

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [issue],
        headers: new Headers(),
      })

      const issues = await client.getIssuesByStage('triage')
      const retrievedIssue = issues[0]
      
      expect(retrievedIssue.trace_id).toBe(testCase.expectedTraceId)
    }
  })

  /**
   * Property 5: State Machine Integrity (Admin View)
   * 
   * For any approval action (approve/deny), the admin dashboard should correctly
   * update labels to maintain state machine integrity.
   */
  it('should maintain single stage label when approving implementation', async () => {
    // Mock the label operations
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
        headers: new Headers(),
      }) // addLabel
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
        headers: new Headers(),
      }) // removeLabel

    await client.approveImplementation(123)

    // Verify addLabel was called with stage:implement
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/issues/123/labels'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ labels: ['stage:implement'] }),
      })
    )

    // Verify removeLabel was called with stage:awaiting-implementation-approval
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/issues/123/labels/stage%3Aawaiting-implementation-approval'),
      expect.objectContaining({
        method: 'DELETE',
      })
    )
  })

  /**
   * Property 5: State Machine Integrity (Admin View)
   * 
   * For any Issue grouping by stage, the admin dashboard should correctly
   * filter and display issues in their respective stages.
   */
  it('should correctly group issues by stage', async () => {
    const stages = ['triage', 'plan', 'prioritize']
    const issuesByStage: Record<string, Issue[]> = {}

    for (const stage of stages) {
      const issues = [
        createMockIssue(100 + stages.indexOf(stage), `Issue in ${stage}`, [
          { name: `stage:${stage}` },
          { name: 'request:bug' },
        ]),
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => issues,
        headers: new Headers(),
      })

      issuesByStage[stage] = await client.getIssuesByStage(stage)
    }

    // Verify each stage has its issues
    for (const stage of stages) {
      expect(issuesByStage[stage].length).toBeGreaterThan(0)
      
      // Verify all issues in this stage have the correct stage label
      for (const issue of issuesByStage[stage]) {
        const stageLabel = issue.labels.find(l => l.name.startsWith('stage:'))
        expect(stageLabel?.name).toBe(`stage:${stage}`)
      }
    }
  })

  /**
   * Property 5: State Machine Integrity (Admin View)
   * 
   * For any Issue with priority label, the admin dashboard should correctly
   * identify and display exactly one priority label.
   */
  it('should validate that issues have at most one priority label', async () => {
    const testCases = [
      {
        name: 'issue with one priority label',
        labels: [
          { name: 'stage:triage' },
          { name: 'priority:p0' },
          { name: 'request:bug' },
        ],
        expectedPriorityCount: 1,
      },
      {
        name: 'issue with no priority label',
        labels: [
          { name: 'stage:triage' },
          { name: 'request:bug' },
        ],
        expectedPriorityCount: 0,
      },
      {
        name: 'invalid issue with multiple priority labels',
        labels: [
          { name: 'stage:triage' },
          { name: 'priority:p0' },
          { name: 'priority:p1' },
          { name: 'request:bug' },
        ],
        expectedPriorityCount: 2, // Should be detected as invalid
      },
    ]

    for (const testCase of testCases) {
      const issue = createMockIssue(123, testCase.name, testCase.labels)

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [issue],
        headers: new Headers(),
      })

      const issues = await client.getIssuesByStage('triage')
      const retrievedIssue = issues[0]
      
      const priorityLabels = retrievedIssue.labels.filter(l => l.name.startsWith('priority:'))
      expect(priorityLabels.length).toBe(testCase.expectedPriorityCount)
      
      // Valid issues should have 0 or 1 priority labels
      if (testCase.expectedPriorityCount <= 1) {
        expect(priorityLabels.length).toBeLessThanOrEqual(1)
      }
    }
  })
})

// Helper function to create mock issues
function createMockIssue(
  number: number,
  title: string,
  labels: Array<{ name: string }>
): Issue {
  return {
    id: number,
    number,
    title,
    body: `Issue body for ${title}\nTrace_ID: test-trace-${number}`,
    state: 'open',
    labels: labels.map((l, i) => ({
      id: i,
      name: l.name,
      color: '000000',
      description: null,
    })),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    user: {
      login: 'test-user',
      id: 1,
      type: 'User',
    },
    html_url: `https://github.com/test-owner/test-repo/issues/${number}`,
    trace_id: `test-trace-${number}`,
  }
}
