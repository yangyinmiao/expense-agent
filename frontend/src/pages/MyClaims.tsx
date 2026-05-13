import { useEffect, useState } from 'react'
import {
  Row, Col, Card, Statistic, Table, Tag, Empty, Spin, message,
} from 'antd'
import dayjs from 'dayjs'
import { getMyClaims } from '../api/claims'

const STATUS_MAP: Record<string, { color: string; label: string }> = {
  draft:            { color: 'default',  label: '草稿' },
  pending:          { color: 'warning',  label: '待审批' },
  manager_approved: { color: 'cyan',     label: '主管已批' },
  finance_approved: { color: 'success',  label: '财务已批' },
  rejected:         { color: 'error',    label: '已驳回' },
  paid:             { color: 'blue',     label: '已打款' },
}

export default function MyClaims() {
  const [claims, setClaims] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [msgApi, ctx] = message.useMessage()

  useEffect(() => {
    getMyClaims()
      .then((r) => setClaims(r.data))
      .catch(() => msgApi.error('获取失败'))
      .finally(() => setLoading(false))
  }, [])

  const total = claims.reduce((s, c) => s + (c.total ?? 0), 0)
  const pending = claims.filter((c) => c.status === 'pending').length
  const approved = claims.filter((c) => ['finance_approved', 'paid'].includes(c.status)).length

  const cols = [
    { title: '申请编号', dataIndex: 'id', render: (v: number) => `#${v}`, width: 90 },
    { title: '供应商', dataIndex: 'vendor', render: (v: string) => v || '—' },
    { title: '金额', dataIndex: 'total', render: (v: number) => v ? `¥${v.toFixed(2)}` : '—', width: 110 },
    { title: '类别', dataIndex: 'category', render: (v: string) => v || '—', width: 100 },
    { title: '状态', dataIndex: 'status', width: 110,
      render: (v: string) => {
        const s = STATUS_MAP[v] ?? { color: 'default', label: v }
        return <Tag color={s.color}>{s.label}</Tag>
      },
    },
    { title: '提交时间', dataIndex: 'submitted_at',
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '—', width: 120,
    },
    { title: '说明', dataIndex: 'description', render: (v: string) => v || '—' },
  ]

  return (
    <div className="page-wrapper">
      {ctx}
      <div className="page-title">📋 我的报销申请</div>
      <div className="page-subtitle">查看所有报销申请的状态与进度</div>

      <Row gutter={16} style={{ marginBottom: 20 }}>
        {[
          ['申请总数', claims.length, undefined],
          ['待审批', pending, '#F59E0B'],
          ['已通过', approved, '#10B981'],
          ['累计金额', `¥${total.toFixed(2)}`, '#1D4ED8'],
        ].map(([label, val, color]) => (
          <Col span={6} key={label as string}>
            <Card size="small" className="stat-card">
              <Statistic title={label} value={val}
                valueStyle={{ fontWeight: 700, color: (color ?? '#0F172A') as string }} />
            </Card>
          </Col>
        ))}
      </Row>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 48 }}><Spin size="large" /></div>
      ) : claims.length === 0 ? (
        <div className="card-white" style={{ padding: '48px 0', textAlign: 'center' }}>
          <Empty description="暂无报销申请，点击「提交报销」上传第一张发票" />
        </div>
      ) : (
        <div className="card-white" style={{ padding: 0, overflow: 'hidden' }}>
          <Table
            columns={cols}
            dataSource={claims}
            rowKey="id"
            size="middle"
            pagination={{ pageSize: 15, showSizeChanger: false }}
          />
        </div>
      )}
    </div>
  )
}