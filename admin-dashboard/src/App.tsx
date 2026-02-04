import { useState } from 'react'
import './App.css'
import { GitHubProvider } from './context/GitHubContext'
import { Tabs, Tab } from './components/Tabs'
import { IssuesByStageTab } from './components/IssuesByStageTab'
import { IssuesByRequestTypeTab } from './components/IssuesByRequestTypeTab'
import { PullRequestsTab } from './components/PullRequestsTab'
import { ApprovalsRequiredTab } from './components/ApprovalsRequiredTab'
import { WorkflowRunsTab } from './components/WorkflowRunsTab'

function AppContent() {
  const [activeTab, setActiveTab] = useState('issues-by-stage')

  const tabs: Tab[] = [
    {
      id: 'issues-by-stage',
      label: 'Issues by Stage',
      content: <IssuesByStageTab />,
    },
    {
      id: 'issues-by-type',
      label: 'Issues by Type',
      content: <IssuesByRequestTypeTab />,
    },
    {
      id: 'pull-requests',
      label: 'Pull Requests',
      content: <PullRequestsTab />,
    },
    {
      id: 'approvals',
      label: 'Approvals Required',
      content: <ApprovalsRequiredTab />,
    },
    {
      id: 'workflows',
      label: 'Workflow Runs',
      content: <WorkflowRunsTab />,
    },
  ]

  return (
    <div className="App">
      <header className="app-header">
        <h1>Admin Operations Dashboard</h1>
      </header>
      <Tabs tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  )
}

function App() {
  return (
    <GitHubProvider>
      <AppContent />
    </GitHubProvider>
  )
}

export default App
