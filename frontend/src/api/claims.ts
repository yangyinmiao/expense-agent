import api from './axios'

export const createClaim = (invoiceId: number, description: string) =>
  api.post('/claims/', { invoice_id: invoiceId, description })

export const submitClaim = (id: number) =>
  api.post(`/claims/${id}/submit`)

export const getMyClaims = () => api.get('/claims/my')

export const getPending = () => api.get('/claims/pending')

export const approveClaim = (id: number, comment: string) =>
  api.post(`/claims/${id}/approve`, { comment })

export const rejectClaim = (id: number, comment: string) =>
  api.post(`/claims/${id}/reject`, { comment })

export const getClaimDetail = (id: number) => api.get(`/claims/${id}/detail`)

export const getApprovalHistory = () => api.get('/claims/approval-history')
