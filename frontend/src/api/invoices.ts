import api from './axios'

export const uploadInvoice = (file: File) => {
  const fd = new FormData()
  fd.append('file', file)
  return api.post('/invoices/upload', fd)
}

export const batchUpload = (files: File[]) => {
  const fd = new FormData()
  files.forEach((f) => fd.append('files', f))
  return api.post('/invoices/batch-upload', fd)
}

export const getInvoice = (id: number) => api.get(`/invoices/${id}`)
