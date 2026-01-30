export interface BugReportRequest {
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface FeatureRequestRequest {
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high';
}

export interface RequestResponse {
  success: boolean;
  trace_id: string;
  message: string;
  github_issue_id?: number;
}

export interface StatusResponse {
  trace_id: string;
  status: string;
  request_type: string;
  title: string;
  github_issue_id?: number;
  created_at: string;
  updated_at: string;
}