import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// 请求拦截器 - 添加token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const authAPI = {
  login: (data) => api.post('/auth/login', data),
  logout: () => api.post('/auth/logout'),
  getMe: () => api.get('/auth/me'),
};

// Users
export const usersAPI = {
  list: (params) => api.get('/users', { params }),
  create: (data) => api.post('/users', data),
  get: (id) => api.get(`/users/${id}`),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
};

// Teams
export const teamsAPI = {
  list: () => api.get('/teams'),
  create: (data) => api.post('/teams', data),
  get: (id) => api.get(`/teams/${id}`),
  update: (id, data) => api.put(`/teams/${id}`, data),
  delete: (id) => api.delete(`/teams/${id}`),
  addMember: (id, data) => api.post(`/teams/${id}/members`, data),
  removeMember: (teamId, userId) => api.delete(`/teams/${teamId}/members/${userId}`),
};

// Projects
export const projectsAPI = {
  list: (params) => api.get('/projects', { params }),
  create: (data) => api.post('/projects', data),
  get: (id) => api.get(`/projects/${id}`),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
};

// Modules
export const modulesAPI = {
  list: (projectId) => api.get(`/projects/${projectId}/modules`),
  create: (projectId, data) => api.post(`/projects/${projectId}/modules`, data),
  get: (id) => api.get(`/modules/${id}`),
  update: (id, data) => api.put(`/modules/${id}`, data),
  delete: (id) => api.delete(`/modules/${id}`),
};

// Cases
export const casesAPI = {
  list: (moduleId, params) => api.get(`/modules/${moduleId}/cases`, { params }),
  create: (moduleId, data) => api.post(`/modules/${moduleId}/cases`, data),
  get: (id) => api.get(`/cases/${id}`),
  update: (id, data) => api.put(`/cases/${id}`, data),
  delete: (id) => api.delete(`/cases/${id}`),
  getVersions: (id) => api.get(`/cases/${id}/versions`),
  getVersion: (caseId, versionId) => api.get(`/cases/${caseId}/versions/${versionId}`),
  rollback: (caseId, versionId) => api.post(`/cases/${caseId}/rollback/${versionId}`),
  toggleFavorite: (id) => api.post(`/cases/${id}/favorite`),
  import: (formData) => api.post('/cases/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  export: (projectId) => api.get(`/cases/export/${projectId}`, {
    responseType: 'blob'
  }),
};

// Plans
export const plansAPI = {
  list: (projectId) => api.get(`/projects/${projectId}/plans`),
  create: (projectId, data) => api.post(`/projects/${projectId}/plans`, data),
  get: (id) => api.get(`/plans/${id}`),
  update: (id, data) => api.put(`/plans/${id}`, data),
  delete: (id) => api.delete(`/plans/${id}`),
  updateCases: (id, data) => api.put(`/plans/${id}/cases`, data),
  copy: (id) => api.post(`/plans/${id}/copy`),
};

// Tasks
export const tasksAPI = {
  list: (params) => api.get('/tasks', { params }),
  create: (data) => api.post('/tasks', data),
  get: (id) => api.get(`/tasks/${id}`),
  dispatch: (id) => api.post(`/tasks/${id}/dispatch`),
  cancel: (id) => api.post(`/tasks/${id}/cancel`),
  retry: (id, data) => api.post(`/tasks/${id}/retry`, data),
  getResults: (id) => api.get(`/tasks/${id}/results`),
  getLogs: (id, params) => api.get(`/tasks/${id}/logs`, { params }),
  getPerformance: (id) => api.get(`/tasks/${id}/performance`),
};

// Agents
export const agentsAPI = {
  list: (params) => api.get('/agents', { params }),
  get: (id) => api.get(`/agents/${id}`),
  update: (id, data) => api.put(`/agents/${id}`, data),
  delete: (id) => api.delete(`/agents/${id}`),
  listGroups: () => api.get('/agents/groups'),
  createGroup: (data) => api.post('/agents/groups', data),
  updateGroup: (id, data) => api.put(`/agents/groups/${id}`, data),
  deleteGroup: (id) => api.delete(`/agents/groups/${id}`),
  addToGroup: (groupId, data) => api.post(`/agents/groups/${groupId}/agents`, data),
  removeFromGroup: (groupId, agentId) => api.delete(`/agents/groups/${groupId}/agents/${agentId}`),
};

// Schedules
export const schedulesAPI = {
  list: () => api.get('/schedules'),
  create: (data) => api.post('/schedules', data),
  update: (id, data) => api.put(`/schedules/${id}`, data),
  delete: (id) => api.delete(`/schedules/${id}`),
  enable: (id) => api.post(`/schedules/${id}/enable`),
  disable: (id) => api.post(`/schedules/${id}/disable`),
};

// Webhooks
export const webhooksAPI = {
  list: () => api.get('/webhooks'),
  create: (data) => api.post('/webhooks', data),
  get: (id) => api.get(`/webhooks/${id}`),
  update: (id, data) => api.put(`/webhooks/${id}`, data),
  delete: (id) => api.delete(`/webhooks/${id}`),
};

// Reports
export const reportsAPI = {
  getSummary: (params) => api.get('/reports/summary', { params }),
  getTrend: (params) => api.get('/reports/trend', { params }),
  getTaskReport: (taskId) => api.get(`/reports/${taskId}`),
  exportReport: (taskId) => api.get(`/reports/${taskId}/export`, {
    responseType: 'blob'
  }),
};

// Audit Logs
export const auditAPI = {
  list: (params) => api.get('/audit-logs', { params }),
};

// System Configs
export const configsAPI = {
  get: () => api.get('/system-configs'),
  update: (data) => api.put('/system-configs', data),
  listEnvVars: (params) => api.get('/system-configs/env-vars', { params }),
  createEnvVar: (data) => api.post('/system-configs/env-vars', data),
  updateEnvVar: (id, data) => api.put(`/system-configs/env-vars/${id}`, data),
  deleteEnvVar: (id) => api.delete(`/system-configs/env-vars/${id}`),
};

export default api;