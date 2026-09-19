const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

async function get(path) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(await res.text() || `Request failed: ${res.status}`);
  return res.json();
}

export const api = {
  dashboard: () => get('/dashboard'),
  current: () => get('/traffic/current'),
  history: (sensor) => get(`/traffic/history${sensor ? `?sensor_id=${encodeURIComponent(sensor)}` : ''}`),
  sensors: () => get('/sensors'),
  junctions: () => get('/junctions'),
  analytics: () => get('/analytics'),
  alerts: () => get('/congestion'),
  prediction: (sensor) => get(`/prediction/${encodeURIComponent(sensor)}`),
  neighbors: (junction) => get(`/graph/neighbors/${encodeURIComponent(junction)}`),
  graphSummary: () => get('/graph/summary')
};
