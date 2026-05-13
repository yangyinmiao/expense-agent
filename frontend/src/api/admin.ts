import api from './axios'

export const getMonthlyStats = (year: number, month: number) =>
  api.get('/admin/stats/monthly', { params: { year, month } })

export const getDeptStats = (year: number, month: number) =>
  api.get('/admin/stats/department', { params: { year, month } })

export const getTrendStats = (year: number) =>
  api.get('/admin/stats/trend', { params: { year } })