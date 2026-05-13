import React, { createContext, useContext, useState, ReactNode } from 'react'

export interface UserInfo {
  id: number; name: string; email: string
  role: 'employee'|'manager'|'finance'|'admin'; department?: string
}

interface AuthCtx {
  user: UserInfo | null
  token: string | null
  setAuth: (token: string, user: UserInfo) => void
  logout: () => void
}

const Ctx = createContext<AuthCtx>({} as AuthCtx)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(sessionStorage.getItem('token'))
  const [user, setUser] = useState<UserInfo | null>(() => {
    const s = sessionStorage.getItem('user')
    return s ? JSON.parse(s) : null
  })

  const setAuth = (t: string, u: UserInfo) => {
    setToken(t); setUser(u)
    sessionStorage.setItem('token', t)
    sessionStorage.setItem('user', JSON.stringify(u))
  }

  const logout = () => {
    setToken(null); setUser(null)
    sessionStorage.removeItem('token')
    sessionStorage.removeItem('user')
  }

  return <Ctx.Provider value={{ user, token, setAuth, logout }}>{children}</Ctx.Provider>
}

export const useAuth = () => useContext(Ctx)