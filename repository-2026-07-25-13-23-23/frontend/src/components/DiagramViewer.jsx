import { useEffect, useRef, useState, Component } from 'react';
import mermaid from 'mermaid';
import { Copy, Check, Maximize2, Minimize2, AlertTriangle } from 'lucide-react';

let mermaidInitialized = false;

function initMermaid() {
  if (mermaidInitialized) return;
  try {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      securityLevel: 'loose',
      fontFamily: 'Inter, sans-serif',
      suppressErrors: true,
      themeVariables: {
        primaryColor: '#6c5ce7',
        primaryTextColor: '#e8e8f0',
        primaryBorderColor: '#4c38b8',
        lineColor: '#a78bfa',
        secondaryColor: '#1a1a3e',
        tertiaryColor: '#22224a',
      },
    });
    mermaidInitialized = true;
  } catch (e) {
    console.warn('Mermaid init error:', e);
  }
}

/**
 * React Error Boundary — catches crashes from mermaid rendering
 * so the whole app doesn't go blank.
 */
class DiagramErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.warn('DiagramErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
