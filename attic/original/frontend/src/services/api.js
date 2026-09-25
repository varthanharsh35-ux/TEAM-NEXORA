const API_BASE = import.meta.env.VITE_API_URL || '/api';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

// Assessment API
export const assessmentAPI = {
  submit: (data) => request('/assess', { method: 'POST', body: JSON.stringify(data) }),
  get: (id) => request(`/assessment/${id}`),
};

// Schemes API
export const schemesAPI = {
  list: (filters = {}) => {
    const params = new URLSearchParams(filters).toString();
    return request(`/schemes?${params}`);
  },
  getEMI: (schemeId, params) => {
    const query = new URLSearchParams(params).toString();
    return request(`/schemes/${schemeId}/emi?${query}`);
  },
};

// Financial API
export const financialAPI = {
  plan: (data) => request('/financial/plan', { method: 'POST', body: JSON.stringify(data) }),
  cashflow: (data) => request('/financial/cashflow', { method: 'POST', body: JSON.stringify(data) }),
};

export default { assessmentAPI, schemesAPI, financialAPI };
