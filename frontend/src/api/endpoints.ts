import { http } from "./http";

export const authApi = {
  login: (username: string, password: string) => http.post("/api/auth/login", { username, password }),
  me: () => http.get("/api/auth/me"),
};

export const checklistApi = {
  list: () => http.get("/api/checklists"),
};

export const registrationApi = {
  list: () => http.get("/api/registrations"),
  create: (payload: Record<string, unknown>) => http.post("/api/registrations", payload),
  submit: (registrationId: number) => http.post("/api/registrations/submit", { registration_id: registrationId }),
  supplementary: (registrationId: number, reason: string) =>
    http.post("/api/registrations/supplementary", { registration_id: registrationId, reason }),
};

export const materialApi = {
  upload: (formData: FormData) =>
    http.post("/api/materials/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  list: (registrationId: number) => http.get(`/api/materials/${registrationId}`),
};

export const workflowApi = {
  queue: (params: Record<string, unknown>) => http.get("/api/workflows/queue", { params }),
  transition: (payload: Record<string, unknown>) => http.post("/api/workflows/transition", payload),
  batchTransition: (payload: Record<string, unknown>) => http.post("/api/workflows/batch-transition", payload),
  history: (registrationId: number) => http.get(`/api/workflows/${registrationId}/history`),
};

export const financeApi = {
  overview: () => http.get("/api/finance/overview"),
  createAccount: (payload: Record<string, unknown>) => http.post("/api/finance/accounts", payload),
  createTransaction: (formData: FormData) =>
    http.post("/api/finance/transactions", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  stats: (params: Record<string, unknown>) => http.get("/api/finance/stats", { params }),
};

export const metricsApi = {
  recompute: () => http.post("/api/metrics/recompute"),
};

export const alertsApi = {
  list: () => http.get("/api/alerts"),
  resolve: (id: number) => http.post(`/api/alerts/${id}/resolve`),
};

export const reportsApi = {
  reconciliation: () => http.post("/api/reports/reconciliation"),
  audit: () => http.post("/api/reports/audit"),
  compliance: () => http.post("/api/reports/compliance"),
  whitelist: () => http.post("/api/reports/whitelist"),
};

export const backupApi = {
  create: () => http.post("/api/backups/create"),
  list: () => http.get("/api/backups"),
  recover: (id: number) => http.post(`/api/backups/${id}/recover`),
};

export const similarityApi = {
  check: (sha256Hash: string) => http.get("/api/similarity/check", { params: { sha256_hash: sha256Hash } }),
};
