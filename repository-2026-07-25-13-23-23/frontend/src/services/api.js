import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Projects
export const createProject = (repoUrl) =>
  api.post('/projects', { repo_url: repoUrl }).then(r => r.data);

export const listProjects = () =>
  api.get('/projects').then(r => r.data);

export const getProject = (id) =>
  api.get(`/projects/${id}`).then(r => r.data);

export const deleteProject = (id) =>
  api.delete(`/projects/${id}`).then(r => r.data);

export const regenerateProject = (id) =>
  api.post(`/projects/${id}/regenerate`).then(r => r.data);

// Documentation
export const getDocumentation = (projectId) =>
  api.get(`/docs/${projectId}`).then(r => r.data);

export const getSection = (projectId, section) =>
  api.get(`/docs/${projectId}/section/${section}`).then(r => r.data);

export const getDiagrams = (projectId) =>
  api.get(`/docs/${projectId}/diagrams`).then(r => r.data);

export const getApiEndpoints = (projectId) =>
  api.get(`/docs/${projectId}/apis`).then(r => r.data);

export const getFileTree = (projectId) =>
  api.get(`/docs/${projectId}/files`).then(r => r.data);

export const generateApiDescriptions = (projectId) =>
  api.post(`/docs/${projectId}/generate-api-descriptions`).then(r => r.data);

// Chat
export const chatAboutProject = (projectId, message) =>
  api.post(`/docs/${projectId}/chat`, { message }).then(r => r.data);

// Export
export const exportDocs = (projectId, format = 'markdown', sections = []) =>
  api.post(`/docs/${projectId}/export`, { format, sections }).then(r => r.data);

// Search
export const searchDocs = (projectId, query) =>
  api.get(`/docs/${projectId}/search`, { params: { q: query } }).then(r => r.data);

// Health
export const healthCheck = () =>
  api.get('/health').then(r => r.data);
