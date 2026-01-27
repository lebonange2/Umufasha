import { useState, useEffect } from 'react';
import { CodingEnvironmentAPI } from '../services/api';
import './ModelSelector.css';

interface Model {
  value: string;
  label: string;
  provider: string;
}

interface ModelSelectorProps {
  selectedModel: string;
  onModelChange: (model: string) => void;
}

export default function ModelSelector({ selectedModel, onModelChange }: ModelSelectorProps) {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadModels = async () => {
      try {
        const data = await CodingEnvironmentAPI.getModels();
        setModels(data.models || []);
      } catch (error) {
        console.error('Failed to load models:', error);
      } finally {
        setLoading(false);
      }
    };

    loadModels();
  }, []);

  if (loading) {
    return (
      <div className="model-selector">
        <span className="model-label">Loading models...</span>
      </div>
    );
  }

  return (
    <div className="model-selector">
      <label htmlFor="model-select" className="model-label">
        LLM Model:
      </label>
      <select
        id="model-select"
        value={selectedModel}
        onChange={(e) => onModelChange(e.target.value)}
        className="model-select"
      >
        {models.length === 0 ? (
          <option value="">No models available</option>
        ) : (
          models.map((model) => (
            <option key={model.value} value={model.value}>
              {model.label}
            </option>
          ))
        )}
      </select>
    </div>
  );
}
