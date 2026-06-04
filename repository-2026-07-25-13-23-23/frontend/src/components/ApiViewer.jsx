import { useState, useEffect } from 'react';
import { ChevronDown, ChevronRight, Send, ArrowUpRight } from 'lucide-react';
import { generateApiDescriptions, getApiEndpoints } from '../services/api';

const METHOD_COLORS = {
  GET: '#4caf50',
  POST: '#2196f3',
  PUT: '#ff9800',
  PATCH: '#ff9800',
  DELETE: '#f44336',
};

export default function ApiViewer({ endpoints, projectId }) {
  const [expandedIdx, setExpandedIdx] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [generateSuccess, setGenerateSuccess] = useState(false);
  const [localEndpoints, setLocalEndpoints] = useState(endpoints || []);

  // Sync props to local state if props change
  useEffect(() => {
    setLocalEndpoints(endpoints || []);
  }, [endpoints]);

  // Polling mechanism
  useEffect(() => {
    let intervalId;
    if (generating && projectId) {
      intervalId = setInterval(async () => {
        try {
          const data = await getApiEndpoints(projectId);
          if (data && data.endpoints) {
            setLocalEndpoints(data.endpoints);
            
            // Check if we're done
            const allDone = data.endpoints.every(e => 
              e.description && 
              e.description !== "No description" && 
              e.description.toLowerCase() !== "unknown"
            );
            
            if (allDone) {
              setGenerating(false);
              setGenerateSuccess(true);
              setTimeout(() => setGenerateSuccess(false), 3000);
            }
          }
        } catch (err) {
          console.error("Failed to poll endpoints", err);
        }
      }, 2000); // poll every 2s
    }
    return () => clearInterval(intervalId);

  }, [generating, projectId]);

  const handleGenerate = async () => {
    if (!projectId) return;
    setGenerating(true);
    setGenerateSuccess(false);
    try {
      await generateApiDescriptions(projectId);
      // Polling effect will take over
    } catch (err) {
      console.error('Failed to trigger description generation', err);
      setGenerating(false);
    }
  };

  if (!localEndpoints || localEndpoints.length === 0) {
    return (
      <div className="animate-fade-in">
        <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: 16 }}>
          🔌 API Endpoints
        </h1>
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          height: 200, color: 'var(--text-muted)', flexDirection: 'column', gap: 8,
        }}>
          <p>No API endpoints discovered.</p>
          <p style={{ fontSize: '0.8rem' }}>APIs are detected from route definitions in the codebase.</p>
        </div>
      </div>
    );
  }

  // Count progress
  const totalEndpoints = localEndpoints.length;
  const describedEndpoints = localEndpoints.filter(e => 
    e.description && e.description !== "No description" && e.description.toLowerCase() !== "unknown"
  ).length;

  return (
    <div className="animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 700 }}>
          🔌 API Endpoints
        </h1>
        <button 
