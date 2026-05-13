import { useState } from 'react'
import {
  Row, Col, Card, Statistic, DatePicker, Button, Empty, Spin, message,
} from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import dayjs, { Dayjs } from 'dayjs'
import { getMonthlyStats, getDeptStats, getTrendStats } from '../api/admin'
import { useAuth } from '../context/AuthContext'

// lazy-load plotly to keep initial bundle small
let Plotly: any
const getPlotly = async () => {
  if (!Plotly) Plotly = (await import('react-plotly.js')).default
  return Plotly
}

const BLUES = ['#1D4ED8','#2563EB','#3B82F6','#60A5FA','#93C5FD','#BFDBFE']

function PlotlyChart({ data, layout }: { data: any[]; layout: any }) {
  const [P, setP] = useState<any>(null)
  if (!P) { getPlotly().then(setP); return <Spin /> }
  return <P data={data} layout={{ ...layout, paper_bgcolor: '#fff', plot_bgcolor: '#fff', font: { family: 'PingFang SC' } }} config={{ displayModeBar: false }} style={{ width: '100%', height: 280 }} />
}

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
            <Col xs={24} md={12}>
              <div className="card-white">
                {stats.cat.length > 0 ? (
                  <PlotlyChart
                    data={[{ type: 'bar', x: stats.cat.map((r: any) => r['类别'] ?? r[0]), y: stats.cat.map((r: any) => r['总金额'] ?? r[2]), marker: { color: BLUES } }]}
                    layout={{ title: { text: `${stats.y}/${stats.m} 各类别金额`, font: { size: 14 } }, margin: { t: 36, b: 40, l: 50, r: 10 } }}
                  />
                ) : <Empty description="暂无数据" />}
              </div>
            </Col>
            <Col xs={24} md={12}>
              <div className="card-white">
                {stats.cat.length > 0 ? (
                  <PlotlyChart
                    data={[{ type: 'pie', labels: stats.cat.map((r: any) => r['类别'] ?? r[0]), values: stats.cat.map((r: any) => r['总金额'] ?? r[2]), hole: 0.45, marker: { colors: BLUES } }]}
                    layout={{ title: { text: '类别占比', font: { size: 14 } }, margin: { t: 36, b: 10, l: 10, r: 10 }, legend: { orientation: 'v' } }}
                  />
                ) : <Empty description="暂无数据" />}
              </div>
            </Col>
            <Col xs={24} md={12}>
              <div className="card-white">
                {stats.dept.length > 0 ? (
                  <PlotlyChart
                    data={[{ type: 'bar', x: stats.dept.map((r: any) => r['部门'] ?? r[0]), y: stats.dept.map((r: any) => r['总金额'] ?? r[2]), marker: { color: BLUES } }]}
                    layout={{ title: { text: '部门报销对比', font: { size: 14 } }, margin: { t: 36, b: 40, l: 50, r: 10 } }}
                  />
                ) : <Empty description="暂无数据" />}
              </div>
            </Col>
            <Col xs={24} md={12}>
              <div className="card-white">
                {stats.trend.length > 0 ? (
                  <PlotlyChart
                    data={[{
                      type: 'scatter', mode: 'lines+markers',
                      x: stats.trend.map((r: any) => r['月份'] ?? r[0]),
                      y: stats.trend.map((r: any) => r['总金额'] ?? r[2]),
                      fill: 'tozeroy', fillcolor: 'rgba(29,78,216,.07)',
                      line: { color: '#1D4ED8', width: 2.5 },
                      marker: { color: '#1D4ED8', size: 7 },
                    }]}
                    layout={{ title: { text: `${stats.y}年月度趋势`, font: { size: 14 } }, margin: { t: 36, b: 40, l: 50, r: 10 }, xaxis: { title: '月份' }, yaxis: { title: '金额（元）' } }}
                  />
                ) : <Empty description="暂无数据" />}
              </div>
            </Col>
          </Row>
        </>
      )}
    </div>
  )
}