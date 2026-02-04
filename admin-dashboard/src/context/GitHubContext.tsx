import React, { createContext, useContext, useMemo } from 'react'
import { GitHubAPIClient } from '../api/GitHubAPIClient'
import { getGitHubConfig } from '../config/github'

interface GitHubContextType {
  client: GitHubAPIClient
  owner: string
  repo: string
}

const GitHubContext = createContext<GitHubContextType | null>(null)

export function GitHubProvider({ children }: { children: React.ReactNode }) {
  const contextValue = useMemo(() => {
    const config = getGitHubConfig()
    const client = new GitHubAPIClient(config.token, config.owner, config.repo, config.baseUrl)
    
    return {
      client,
      owner: config.owner,
      repo: config.repo,
    }
  }, [])

  return (
    <GitHubContext.Provider value={contextValue}>
      {children}
    </GitHubContext.Provider>
  )
}

export function useGitHub(): GitHubContextType {
  const context = useContext(GitHubContext)
  if (!context) {
    throw new Error('useGitHub must be used within a GitHubProvider')
  }
  return context
}
