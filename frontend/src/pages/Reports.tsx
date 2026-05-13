import { useState } from 'react'
import {
  Row, Col, Card, Statistic, DatePicker, Button, Empty, Spin, message,
} from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import dayjs, { Dayjs } from 'dayjs'
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { getMonthlyStats, getDeptStats, getTrendStats } from '../api/admin'
import { useAuth } from '../context/AuthContext'

const BLUES = ['#1D4ED8', '#2563EB', '#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE']

export default function Reports() {
  const { user } = useAuth()
  const [period, setPeriod] = useState<Dayjs>(dayjs())
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<any>(null)
  const [msgApi, ctx] = message.useMessage()

  if (!['finance', 'admin'].includes(user?.role ?? '')) {
    return <div className="page-wrapper"><Empty description="此页面仅限财务 / 管理员使用" /></div>
  }

  const query = async () => {
    setLoading(true)
    try {
      const y = period.year(), m = period.month() + 1
      const [cat, dept, trend] = await Promise.all([
        getMonthlyStats(y, m),
        getDeptStats(y, m),
        getTrendStats(y),
      ])
      setStats({ cat: cat.data, dept: dept.data, trend: trend.data, y, m })
    } catch {
      msgApi.error('查询失败')
    } finally { setLoading(false) }
  }

  const totalAmt = stats?.cat.reduce((s: number, r: any) => s + (r['总金额'] ?? 0), 0) ?? 0
  const totalCnt = stats?.cat.reduce((s: number, r: any) => s + (r['申请数'] ?? 0), 0) ?? 0

  return (
    <div className="page-wrapper">
      {ctx}
      <div className="page-title">📊 统计报表</div>
      <div className="page-subtitle">查看报销数据汇总与趋势分析</div>

      <div className="card-white" style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <DatePicker
          picker="month"
          value={period}
          onChange={(v) => v && setPeriod(v)}
          format="YYYY年M月"
          allowClear={false}
        />
        <Button type="primary" icon={<SearchOutlined />} loading={loading} onClick={query}>
          查询报表
        </Button>
      </div>

      {loading && <div style={{ textAlign: 'center', padding: 48 }}><Spin size="large" /></div>}

      {stats && !loading && (
        <>
          <Row gutter={16} style={{ marginBottom: 20 }}>
            {[
              ['当月报销总额', `¥${totalAmt.toFixed(2)}`, '#1D4ED8'],
              ['审批通过笔数', totalCnt, '#0F172A'],
              ['涉及部门', stats.dept.length, '#0F172A'],
              ['统计范围', `${stats.y}年${stats.m}月`, '#0F172A'],
            ].map(([l, v, c]) => (
              <Col span={6} key={l as string}>
                <Card size="small" className="stat-card">
                  <Statistic title={l} value={v}
                    valueStyle={{ fontWeight: 700, color: c as string, fontSize: 15 }} />
                </Card>
              </Col>
            ))}
          </Row>

          <Row gutter={16}>
            {/* 各类别金额柱状图 */}
            <Col xs={24} md={12}>
              <div className="card-white">
                <div style={{ fontWeight: 600, marginBottom: 12 }}>{stats.y}/{stats.m} 各类别金额</div>
                {stats.cat.length > 0 ? (
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={stats.cat} margin={{ top: 8, right: 16, bottom: 8, left: 16 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="类别" />
                      <YAxis />
                      <Tooltip formatter={(v: any) => `¥${Number(v).toFixed(2)}`} />
                      <Bar dataKey="总金额" name="金额">
                        {stats.cat.map((_: any, i: number) => <Cell key={i} fill={BLUES[i % BLUES.length]} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : <Empty description="暂无数据" />}
              </div>
            </Col>

            {/* 类别占比饼图 */}
            <Col xs={24} md={12}>
              <div className="card-white">
                <div style={{ fontWeight: 600, marginBottom: 12 }}>类别占比</div>
                {stats.cat.length > 0 ? (
                  <ResponsiveContainer width="100%" height={260}>
                    <PieChart>
                      <Pie
                        data={stats.cat}
                        dataKey="总金额"
                        nameKey="类别"
                        cx="50%" cy="50%"
                        outerRadius={90}
                        innerRadius={45}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      >
                        {stats.cat.map((_: any, i: number) => <Cell key={i} fill={BLUES[i % BLUES.length]} />)}
                      </Pie>
                      <Tooltip formatter={(v: any) => `¥${Number(v).toFixed(2)}`} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : <Empty description="暂无数据" />}
              </div>
            </Col>

            {/* 部门对比柱状图 */}
            <Col xs={24} md={12}>
              <div className="card-white">
                <div style={{ fontWeight: 600, marginBottom: 12 }}>部门报销对比</div>
                {stats.dept.length > 0 ? (
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={stats.dept} margin={{ top: 8, right: 16, bottom: 8, left: 16 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="部门" />
                      <YAxis />
                      <Tooltip formatter={(v: any) => `¥${Number(v).toFixed(2)}`} />
                      <Bar dataKey="总金额" name="金额">
                        {stats.dept.map((_: any, i: number) => <Cell key={i} fill={BLUES[i % BLUES.length]} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : <Empty description="暂无数据" />}
              </div>
            </Col>

            {/* 月度趋势折线图 */}
            <Col xs={24} md={12}>
              <div className="card-white">
                <div style={{ fontWeight: 600, marginBottom: 12 }}>{stats.y}年月度趋势</div>
                {stats.trend.length > 0 ? (
                  <ResponsiveContainer width="100%" height={260}>
                    <LineChart data={stats.trend} margin={{ top: 8, right: 16, bottom: 8, left: 16 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="月份" tickFormatter={(v) => `${v}月`} />
                      <YAxis />
                      <Tooltip formatter={(v: any) => `¥${Number(v).toFixed(2)}`} labelFormatter={(v) => `${v}月`} />
                      <Legend />
                      <Line type="monotone" dataKey="总金额" name="金额" stroke="#1D4ED8" strokeWidth={2.5} dot={{ r: 5 }} activeDot={{ r: 7 }} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : <Empty description="暂无数据" />}
              </div>
            </Col>
          </Row>
        </>
      )}
    </div>
  )
}
