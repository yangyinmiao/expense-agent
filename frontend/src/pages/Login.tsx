import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Form, Input, Button, Tabs, Select, message, Typography, Space } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useAuth } from '../context/AuthContext'
import { login, register } from '../api/auth'

const { Title, Text } = Typography

const ROLES = [
  { value: 'employee', label: '员工' },
  { value: 'manager',  label: '主管' },
  { value: 'finance',  label: '财务' },
  { value: 'admin',    label: '管理员' },
]

export default function Login() {
  const { setAuth } = useAuth()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [msgApi, ctx] = message.useMessage()

  const onLogin = async (vals: { username: string; password: string }) => {
    setLoading(true)
    try {
      const { data } = await login(vals.username, vals.password)
      setAuth(data.access_token, data.user)
      navigate('/')
    } catch (e: any) {
      msgApi.error(e.response?.data?.detail ?? '登录失败，请检查账号密码')
    } finally { setLoading(false) }
  }

  const onRegister = async (vals: any) => {
    setLoading(true)
    try {
      await register(vals)
      msgApi.success('注册成功，请登录')
    } catch (e: any) {
      msgApi.error(e.response?.data?.detail ?? '注册失败')
    } finally { setLoading(false) }
  }

  return (
    <div style={{
      minHeight: '100vh', background: 'linear-gradient(135deg,#1e3a8a 0%,#1d4ed8 50%,#3b82f6 100%)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      {ctx}
      <div style={{
        background: '#fff', borderRadius: 16, padding: '40px 44px',
        width: 420, boxShadow: '0 20px 60px rgba(0,0,0,.15)',
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 42 }}>🧾</div>
          <Title level={3} style={{ margin: '8px 0 4px', color: '#0F172A' }}>智报</Title>
          <Text type="secondary" style={{ fontSize: 13 }}>企业财务报销管理系统</Text>
        </div>

        <Tabs
          defaultActiveKey="login"
          centered
          items={[
            {
              key: 'login', label: '登  录',
              children: (
                <Form layout="vertical" onFinish={onLogin} style={{ marginTop: 8 }}>
                  <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
                    <Input prefix={<UserOutlined />} placeholder="用户名 / 邮箱" size="large" />
                  </Form.Item>
                  <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
                    <Input.Password prefix={<LockOutlined />} placeholder="密码" size="large" />
                  </Form.Item>
                  <Button type="primary" htmlType="submit" loading={loading}
                    block size="large" style={{ marginTop: 4 }}>
                    登 录
                  </Button>
                  <div style={{
                    marginTop: 16, padding: '10px 12px', background: '#EFF6FF',
                    borderRadius: 8, fontSize: 12, color: '#1D4ED8',
                  }}>
                    <b>测试账号（密码均为 test123456）</b><br />
                    员工小李 · 主管张经理 · 财务王姐 · 管理员Admin
                  </div>
                </Form>
              ),
            },
            {
              key: 'register', label: '注  册',
              children: (
                <Form layout="vertical" onFinish={onRegister} style={{ marginTop: 8 }}>
                  <Space.Compact block>
                    <Form.Item name="name" label="姓名" rules={[{ required: true }]} style={{ flex: 1, marginRight: 8 }}>
                      <Input placeholder="真实姓名" />
                    </Form.Item>
                    <Form.Item name="department" label="部门" style={{ flex: 1 }}>
                      <Input placeholder="研发部" />
                    </Form.Item>
                  </Space.Compact>
                  <Form.Item name="email" label="邮箱" rules={[{ required: true, type: 'email' }]}>
                    <Input placeholder="name@company.com" />
                  </Form.Item>
                  <Form.Item name="password" label="密码" rules={[{ required: true, min: 6 }]}>
                    <Input.Password placeholder="至少 6 位" />
                  </Form.Item>
                  <Form.Item name="role" label="角色" initialValue="employee">
                    <Select options={ROLES} />
                  </Form.Item>
                  <Button htmlType="submit" loading={loading} block>注 册</Button>
                </Form>
              ),
            },
          ]}
        />
      </div>
    </div>
  )
}