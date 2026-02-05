export interface GitHubConfig {
  token: string
  owner: string
  repo: string
  baseUrl: string
}

export function getGitHubConfig(): GitHubConfig {
  const token = import.meta.env.VITE_GITHUB_TOKEN
  const owner = import.meta.env.VITE_GITHUB_OWNER
  const repo = import.meta.env.VITE_GITHUB_REPO
  const baseUrl = import.meta.env.VITE_GITHUB_API_BASE_URL || 'https://api.github.com'

  if (!token || !owner || !repo) {
    throw new Error(
      'Missing required environment variables. Please configure VITE_GITHUB_TOKEN, VITE_GITHUB_OWNER, and VITE_GITHUB_REPO.'
    )
  }

  return {
    token,
    owner,
    repo,
    baseUrl,
  }
}
