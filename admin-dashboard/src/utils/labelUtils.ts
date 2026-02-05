import type { Label } from '../types/github'

export function getStageLabel(labels: Label[]): string | undefined {
  const stageLabel = labels.find(label => label.name.startsWith('stage:'))
  return stageLabel?.name.replace('stage:', '')
}

export function getRequestTypeLabel(labels: Label[]): string | undefined {
  const requestLabel = labels.find(label => label.name.startsWith('request:'))
  return requestLabel?.name.replace('request:', '')
}

export function getPriorityLabel(labels: Label[]): string | undefined {
  const priorityLabel = labels.find(label => label.name.startsWith('priority:'))
  return priorityLabel?.name.replace('priority:', '')
}

export function getSourceLabel(labels: Label[]): string | undefined {
  const sourceLabel = labels.find(label => label.name.startsWith('source:'))
  return sourceLabel?.name.replace('source:', '')
}

export function getSeverityLabel(labels: Label[]): string | undefined {
  const severityLabel = labels.find(label => label.name.startsWith('severity:'))
  return severityLabel?.name.replace('severity:', '')
}
