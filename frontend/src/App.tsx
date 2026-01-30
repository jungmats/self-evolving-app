import React, { useState } from 'react';
import BugReportForm from './components/BugReportForm';
import FeatureRequestForm from './components/FeatureRequestForm';
import { api } from './api';
import { BugReportRequest, FeatureRequestRequest, RequestResponse } from './types';

type TabType = 'bug' | 'feature';

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('bug');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [lastResponse, setLastResponse] = useState<RequestResponse | null>(null);

  const handleBugReportSubmit = async (bugReport: BugReportRequest) => {
    setIsSubmitting(true);
    setMessage(null);

    try {
      const response = await api.submitBugReport(bugReport);
      setLastResponse(response);
      setMessage({
        type: 'success',
        text: `Bug report submitted successfully! Trace ID: ${response.trace_id}`,
      });
    } catch (error) {
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Failed to submit bug report',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFeatureRequestSubmit = async (featureRequest: FeatureRequestRequest) => {
    setIsSubmitting(true);
    setMessage(null);

    try {
      const response = await api.submitFeatureRequest(featureRequest);
      setLastResponse(response);
      setMessage({
        type: 'success',
        text: `Feature request submitted successfully! Trace ID: ${response.trace_id}`,
      });
    } catch (error) {
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Failed to submit feature request',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container">
      <div className="header">
        <h1>Self-Evolving Web Application</h1>
        <p>Submit bug reports and feature requests to help improve the system</p>
      </div>

      {message && (
        <div className={`alert ${message.type === 'success' ? 'alert-success' : 'alert-error'}`}>
          {message.text}
        </div>
      )}

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'bug' ? 'active' : ''}`}
          onClick={() => setActiveTab('bug')}
        >
          Bug Report
        </button>
        <button
          className={`tab ${activeTab === 'feature' ? 'active' : ''}`}
          onClick={() => setActiveTab('feature')}
        >
          Feature Request
        </button>
      </div>

      {activeTab === 'bug' && (
        <BugReportForm onSubmit={handleBugReportSubmit} isSubmitting={isSubmitting} />
      )}

      {activeTab === 'feature' && (
        <FeatureRequestForm onSubmit={handleFeatureRequestSubmit} isSubmitting={isSubmitting} />
      )}

      {lastResponse && (
        <div className="form-container">
          <h3>Submission Details</h3>
          <p><strong>Trace ID:</strong> {lastResponse.trace_id}</p>
          <p><strong>Status:</strong> Submitted successfully</p>
          <p><strong>Message:</strong> {lastResponse.message}</p>
          <p><em>You can use the Trace ID to check the status of your request later.</em></p>
        </div>
      )}
    </div>
  );
}

export default App;