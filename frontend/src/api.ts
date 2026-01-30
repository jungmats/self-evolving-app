import { BugReportRequest, FeatureRequestRequest, RequestResponse, StatusResponse } from './types';

// Use full URL in development, relative path in production
const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000/api' 
  : '/api';

export const api = {
  async submitBugReport(bugReport: BugReportRequest): Promise<RequestResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/submit/bug`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(bugReport),
      });

      if (!response.ok) {
        let errorMessage = 'Failed to submit bug report';
        try {
          const error = await response.json();
          errorMessage = error.detail || errorMessage;
        } catch {
          errorMessage = `Server error: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      return response.json();
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Cannot connect to server. Please make sure the backend is running on http://localhost:8000');
      }
      throw error;
    }
  },

  async submitFeatureRequest(featureRequest: FeatureRequestRequest): Promise<RequestResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/submit/feature`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(featureRequest),
      });

      if (!response.ok) {
        let errorMessage = 'Failed to submit feature request';
        try {
          const error = await response.json();
          errorMessage = error.detail || errorMessage;
        } catch {
          errorMessage = `Server error: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      return response.json();
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Cannot connect to server. Please make sure the backend is running on http://localhost:8000');
      }
      throw error;
    }
  },

  async getRequestStatus(traceId: string): Promise<StatusResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/status/${traceId}`);

      if (!response.ok) {
        let errorMessage = 'Failed to get request status';
        try {
          const error = await response.json();
          errorMessage = error.detail || errorMessage;
        } catch {
          errorMessage = `Server error: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      return response.json();
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Cannot connect to server. Please make sure the backend is running on http://localhost:8000');
      }
      throw error;
    }
  },
};