import { BugReportRequest, FeatureRequestRequest, RequestResponse, StatusResponse } from './types';

const API_BASE_URL = '/api';

export const api = {
  async submitBugReport(bugReport: BugReportRequest): Promise<RequestResponse> {
    const response = await fetch(`${API_BASE_URL}/submit/bug`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(bugReport),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to submit bug report');
    }

    return response.json();
  },

  async submitFeatureRequest(featureRequest: FeatureRequestRequest): Promise<RequestResponse> {
    const response = await fetch(`${API_BASE_URL}/submit/feature`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(featureRequest),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to submit feature request');
    }

    return response.json();
  },

  async getRequestStatus(traceId: string): Promise<StatusResponse> {
    const response = await fetch(`${API_BASE_URL}/status/${traceId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get request status');
    }

    return response.json();
  },
};