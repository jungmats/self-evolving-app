import { useState } from 'react'
import './App.css'
import { GitHubProvider } from './context/GitHubContext'
import { Tabs, Tab } from './components/Tabs'
import { IssuesTab } from './components/IssuesTab'
import { PullRequestsTab } from './components/PullRequestsTab'
import { ApprovalsRequiredTab } from './components/ApprovalsRequiredTab'
import { WorkflowRunsTab } from './components/WorkflowRunsTab'

function AppContent() {
  const [activeTab, setActiveTab] = useState('issues')

  const tabs: Tab[] = [
    {
      id: 'issues',
      label: 'Issues',
      content: <IssuesTab />,
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
