import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, App as AntApp } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider, useAuth } from './context/AuthContext'
import { theme } from './styles/theme'
import AppLayout from './components/AppLayout'
import Login from './pages/Login'
import Submit from './pages/Submit'
import Batch from './pages/Batch'
import MyClaims from './pages/MyClaims'
import Pending from './pages/Pending'
import Reports from './pages/Reports'
import AgentChat from './pages/AgentChat'
import './styles/global.css'

const qc = new QueryClient()

function ProtectedRoutes() {
  const { token } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/submit" replace />} />
        <Route path="submit"  element={<Submit />} />
        <Route path="batch"   element={<Batch />} />
        <Route path="my"      element={<MyClaims />} />
        <Route path="pending" element={<Pending />} />
        <Route path="reports" element={<Reports />} />
        <Route path="chat"    element={<AgentChat />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <ConfigProvider theme={theme} locale={zhCN}>
        <AntApp>
          <AuthProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/*" element={<ProtectedRoutes />} />
              </Routes>
            </BrowserRouter>
          </AuthProvider>
        </AntApp>
      </ConfigProvider>
    </QueryClientProvider>
  )
}