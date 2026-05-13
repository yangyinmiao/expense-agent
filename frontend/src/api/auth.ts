import api from './axios'

export interface LoginResp {
  access_token: string
  user: UserInfo
}

export interface UserInfo {
  id: number
  name: string
  email: string
  role: 'employee' | 'manager' | 'finance' | 'admin'
  department?: string
}

export const login = (username: string, password: string) =>
  api.post<LoginResp>('/auth/login', new URLSearchParams({ username, password }), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })

export const register = (data: {
  name: string; email: string; password: string; department: string; role: string
}) => api.post('/auth/register', data)
