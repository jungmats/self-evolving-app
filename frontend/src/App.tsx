import React, { useState } from 'react';
import Modal from './components/Modal';
import BugReportForm from './components/BugReportForm';
import FeatureRequestForm from './components/FeatureRequestForm';
import { api } from './api';
import { BugReportRequest, FeatureRequestRequest, RequestResponse } from './types';

type ModalType = 'bug' | 'feature' | null;

function App() {
  const [activeModal, setActiveModal] = useState<ModalType>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [lastResponse, setLastResponse] = useState<RequestResponse | null>(null);

  const closeModal = () => {
    setActiveModal(null);
    setMessage(null);
    setLastResponse(null);
  };

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
    <div>
      {/* Homepage */}
      <div className="homepage">
        <div className="homepage-content">
          <h1>Self-Evolving Web Application</h1>
          <p>
            I'm a self-evolving web application. You can contribute to my evolution by submitting 
            feature requests and bug reports. Your feedback helps me grow and improve continuously.
          </p>
        </div>
      </div>

      {/* Floating Action Buttons */}
      <div className="floating-buttons">
        <button 
          className="floating-btn bug" 
          onClick={() => setActiveModal('bug')}
          title="Report a Bug"
        >
          🐛
          <span className="tooltip">Report a Bug</span>
        </button>
        <button 
          className="floating-btn feature" 
          onClick={() => setActiveModal('feature')}
          title="Request a Feature"
        >
          💡
          <span className="tooltip">Request a Feature</span>
        </button>
      </div>

      {/* Bug Report Modal */}
      <Modal
        isOpen={activeModal === 'bug'}
        onClose={closeModal}
        title="Report a Bug"
      >
        {message && (
          <div className={`alert ${message.type === 'success' ? 'alert-success' : 'alert-error'}`}>
            {message.text}
          </div>
        )}

        {lastResponse && message?.type === 'success' ? (
          <div className="success-details">
            <h3>Submission Details</h3>
            <p><strong>Trace ID:</strong> {lastResponse.trace_id}</p>
            <p><strong>Status:</strong> Submitted successfully</p>
            <p><strong>Message:</strong> {lastResponse.message}</p>
            <p><em>You can use the Trace ID to check the status of your request later.</em></p>
          </div>
        ) : (
          <BugReportForm 
            onSubmit={handleBugReportSubmit} 
            isSubmitting={isSubmitting}
          />
        )}
      </Modal>

      {/* Feature Request Modal */}
      <Modal
        isOpen={activeModal === 'feature'}
        onClose={closeModal}
        title="Request a Feature"
      >
        {message && (
          <div className={`alert ${message.type === 'success' ? 'alert-success' : 'alert-error'}`}>
            {message.text}
          </div>
        )}

        {lastResponse && message?.type === 'success' ? (
          <div className="success-details">
            <h3>Submission Details</h3>
            <p><strong>Trace ID:</strong> {lastResponse.trace_id}</p>
            <p><strong>Status:</strong> Submitted successfully</p>
            <p><strong>Message:</strong> {lastResponse.message}</p>
            <p><em>You can use the Trace ID to check the status of your request later.</em></p>
          </div>
        ) : (
          <FeatureRequestForm 
            onSubmit={handleFeatureRequestSubmit} 
            isSubmitting={isSubmitting}
          />
        )}
      </Modal>
    </div>
  );
}

export default App;