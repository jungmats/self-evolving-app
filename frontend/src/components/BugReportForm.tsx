import React, { useState } from 'react';
import { BugReportRequest } from '../types';

interface BugReportFormProps {
  onSubmit: (bugReport: BugReportRequest) => void;
  isSubmitting: boolean;
}

const BugReportForm: React.FC<BugReportFormProps> = ({ onSubmit, isSubmitting }) => {
  const [formData, setFormData] = useState<BugReportRequest>({
    title: '',
    description: '',
    severity: 'medium',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <div className="form-container">
      <h2>Report a Bug</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="title">Bug Title *</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            maxLength={200}
            placeholder="Brief description of the bug"
          />
        </div>

        <div className="form-group">
          <label htmlFor="severity">Severity *</label>
          <select
            id="severity"
            name="severity"
            value={formData.severity}
            onChange={handleChange}
            required
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="description">Description *</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            required
            maxLength={2000}
            placeholder="Detailed description of the bug, steps to reproduce, expected vs actual behavior"
          />
        </div>

        <button type="submit" className="btn" disabled={isSubmitting}>
          {isSubmitting ? 'Submitting...' : 'Submit Bug Report'}
        </button>
      </form>
    </div>
  );
};

export default BugReportForm;