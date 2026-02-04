import { useState } from 'react'
import './CollapsibleSection.css'

interface CollapsibleSectionProps {
  title: string
  children: React.ReactNode
  defaultExpanded?: boolean
  badge?: string
}

export function CollapsibleSection({ 
  title, 
  children, 
  defaultExpanded = false,
  badge 
}: CollapsibleSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  return (
    <div className="collapsible-section">
      <button 
        className="collapsible-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="collapsible-icon">
          {isExpanded ? '▼' : '▶'}
        </span>
        <span className="collapsible-title">{title}</span>
        {badge && <span className="collapsible-badge">{badge}</span>}
      </button>
      {isExpanded && (
        <div className="collapsible-content">
          {children}
        </div>
      )}
    </div>
  )
}
