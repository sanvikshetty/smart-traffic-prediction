const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

async function get(path) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(await res.text() || `Request failed: ${res.status}`);
  return res.json();
}

async function post(path) {
  const res = await fetch(`${API}${path}`, { method: 'POST' });
  if (!res.ok) throw new Error(await res.text() || `Request failed: ${res.status}`);
  return res.json();
}

export const api = {
  health: () => get('/health'),
  schema: () => get('/schema'),
  dashboard: () => get('/dashboard'),
  current: () => get('/traffic/current'),
  history: (node) => get(`/traffic/history${node ? `?node_id=${encodeURIComponent(node)}` : ''}`),
  sensors: () => get('/sensors'),
  junctions: () => get('/junctions'),
  nodes: () => get('/nodes'),
  edges: () => get('/edges'),
  analytics: () => get('/analytics'),
  alerts: () => get('/congestion'),
  prediction: (node) => get(`/prediction/${encodeURIComponent(node)}`),
  predictions: () => get('/predictions'),
  runGNN: (epochs = 300) => post(`/predict/gnn?epochs=${epochs}`),
  neighbors: (junction) => get(`/graph/neighbors/${encodeURIComponent(junction)}`),
  graphSummary: () => get('/graph/summary')
};
