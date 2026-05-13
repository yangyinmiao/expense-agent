import api from './axios'

export const chatWithAgent = (question: string) =>
  api.post('/agent/chat', { question })