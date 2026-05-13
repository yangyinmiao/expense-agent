import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  Layout, Menu, Avatar, Dropdown, Typography, Space, Tag,
} from 'antd'
import {
  UploadOutlined, AppstoreOutlined, CheckSquareOutlined, HistoryOutlined,
  BarChartOutlined, RobotOutlined, MenuFoldOutlined,
  MenuUnfoldOutlined, LogoutOutlined, UserOutlined,
  InboxOutlined,
} from '@ant-design/icons'
import { useAuth } from '../context/AuthContext'

const { Sider, Header, Content } = Layout
const { Text } = Typography

const ROLE_LABEL: Record<string, string> = {
  employee: '员工', manager: '主管', finance: '财务', admin: '管理员',
}

const NAV = [
  { key: '/submit',   icon: <UploadOutlined />,       label: '提交报销' },
  { key: '/batch',    icon: <InboxOutlined />,         label: '批量上传' },
  { key: '/my',       icon: <AppstoreOutlined />,      label: '我的申请' },
  { key: '/pending',  icon: <CheckSquareOutlined />,   label: '待审批' },
  { key: '/reports',  icon: <BarChartOutlined />,      label: '统计报表' },
  { key: '/chat',     icon: <RobotOutlined />,         label: '智能问答' },
]

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()

  const dropdownItems = [
    {
      key: 'logout', icon: <LogoutOutlined />, label: '退出登录',
      onClick: () => { logout(); navigate('/login') },
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        width={220}
        style={{ position: 'sticky', top: 0, height: '100vh', overflow: 'auto' }}
        theme="dark"
      >
        {/* Logo */}
        <div style={{
          height: 64, display: 'flex', alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          padding: collapsed ? 0 : '0 20px',
          borderBottom: '1px solid rgba(255,255,255,.08)',
          transition: 'all .2s',
        }}>
          <span style={{ fontSize: 22, lineHeight: 1 }}>🧾</span>
          {!collapsed && (
            <span style={{ marginLeft: 10, color: '#fff', fontWeight: 700, fontSize: 16 }}>
              智报
            </span>
          )}
        </div>

        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[pathname]}
          items={NAV}
          onClick={({ key }) => navigate(key)}
          style={{ marginTop: 8, border: 'none' }}
        />
      </Sider>

      <Layout>
        <Header style={{
          background: '#fff', padding: '0 24px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          borderBottom: '1px solid #E2E8F0', height: 56, position: 'sticky', top: 0, zIndex: 10,
        }}>
          <Space>
            <span
              style={{ cursor: 'pointer', fontSize: 16, color: '#475569' }}
              onClick={() => setCollapsed(!collapsed)}
            >
              {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            </span>
          </Space>

          <Dropdown menu={{ items: dropdownItems }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar size={32} icon={<UserOutlined />} style={{ background: '#1D4ED8' }} />
              <Text strong style={{ color: '#0F172A' }}>{user?.name}</Text>
              <Tag color="blue" style={{ margin: 0 }}>
                {ROLE_LABEL[user?.role ?? ''] ?? user?.role}
              </Tag>
            </Space>
          </Dropdown>
        </Header>

        <Content style={{ overflow: 'auto' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}