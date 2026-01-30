import React, { useState } from 'react';
import { FeatureRequestRequest } from '../types';

interface FeatureRequestFormProps {
  onSubmit: (featureRequest: FeatureRequestRequest) => void;
  isSubmitting: boolean;
  onSuccess?: () => void;
}

const FeatureRequestForm: React.FC<FeatureRequestFormProps> = ({ onSubmit, isSubmitting, onSuccess }) => {
  const [formData, setFormData] = useState<FeatureRequestRequest>({
    title: '',
    description: '',
    priority: 'medium',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
    // Reset form after successful submission
    if (onSuccess) {
      setFormData({
        title: '',
        description: '',
        priority: 'medium',
      });
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="title">Feature Title *</label>
        <input
          type="text"
          id="title"
          name="title"
          value={formData.title}
          onChange={handleChange}
          required
          maxLength={200}
          placeholder="Brief description of the feature"
        />
      </div>

      <div className="form-group">
        <label htmlFor="priority">Priority *</label>
        <select
          id="priority"
          name="priority"
          value={formData.priority}
          onChange={handleChange}
          required
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
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
          placeholder="Detailed description of the feature, use cases, and expected benefits"
        />
      </div>

      <button type="submit" className="btn" disabled={isSubmitting}>
        {isSubmitting ? 'Submitting...' : 'Submit Feature Request'}
      </button>
    </form>
  );
};

export default FeatureRequestForm;