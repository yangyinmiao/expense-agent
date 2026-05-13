import { useEffect, useState } from 'react'
import {
  Row, Col, Card, Statistic, Table, Tag, Empty,
  Spin, message, Typography, Space,
} from 'antd'
import {
  CheckCircleOutlined, CloseCircleOutlined, EyeOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { getApprovalHistory } from '../api/claims'
import { useAuth } from '../context/AuthContext'
import ClaimDetailModal from '../components/ClaimDetailModal'

const { Text } = Typography

const CLAIM_STATUS_MAP: Record<string, { color: string; label: string }> = {
  draft:            { color: 'default',  label: '草稿' },
  pending:          { color: 'warning',  label: '待审批' },
  manager_approved: { color: 'cyan',     label: '主管已批' },
  finance_approved: { color: 'success',  label: '财务已批' },
  rejected:         { color: 'error',    label: '已驳回' },
  paid:             { color: 'blue',     label: '已打款' },
}

export default function ApprovalHistory() {
  const { user } = useAuth()
  const [records, setRecords] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedClaimId, setSelectedClaimId] = useState<number | null>(null)
  const [msgApi, ctx] = message.useMessage()

  useEffect(() => {
    if (!['manager', 'finance', 'admin'].includes(user?.role ?? '')) {
      setLoading(false)
      return
    }
    getApprovalHistory()
      .then((r) => setRecords(r.data))
      .catch(() => msgApi.error('获取失败'))
      .finally(() => setLoading(false))
  }, [])

  if (!['manager', 'finance', 'admin'].includes(user?.role ?? '')) {
    return (
      <div className="page-wrapper">
        <Empty description="此页面仅限主管 / 财务 / 管理员查看" />
      </div>
    )
  }

  const approvedCnt = records.filter((r) => r.action === 'approved').length
  const rejectedCnt = records.filter((r) => r.action === 'rejected').length
  const totalAmt = records
    .filter((r) => r.action === 'approved')
    .reduce((s, r) => s + (r.total ?? 0), 0)

  const cols = [
    {
      title: '操作时间', dataIndex: 'created_at', width: 140,
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '—',
      defaultSortOrder: 'descend' as const,
      sorter: (a: any, b: any) => (a.created_at ?? '').localeCompare(b.created_at ?? ''),
    },
    {
      title: '审批结果', dataIndex: 'action', width: 100,
      filters: [{ text: '通过', value: 'approved' }, { text: '驳回', value: 'rejected' }],
      onFilter: (value: any, record: any) => record.action === value,
      render: (v: string) => v === 'approved'
        ? <Tag icon={<CheckCircleOutlined />} color="success">通过</Tag>
        : <Tag icon={<CloseCircleOutlined />} color="error">驳回</Tag>,
    },
    { title: '申请人', dataIndex: 'applicant_name', width: 100 },
    { title: '供应商', dataIndex: 'vendor', render: (v: string) => v || '—', ellipsis: true },
    {
      title: '金额', dataIndex: 'total', width: 110,
      render: (v: number) => v != null
        ? <Text strong style={{ color: '#1D4ED8' }}>¥{v.toFixed(2)}</Text>
        : '—',
      sorter: (a: any, b: any) => (a.total ?? 0) - (b.total ?? 0),
    },
    { title: '类别', dataIndex: 'category', width: 90,
      render: (v: string) => v ? <Tag>{v}</Tag> : '—' },
    { title: '开票日期', dataIndex: 'invoice_date', width: 110,
      render: (v: string) => v || '—' },
    {
      title: '申请当前状态', dataIndex: 'claim_status', width: 120,
      render: (v: string) => {
        const s = CLAIM_STATUS_MAP[v] ?? { color: 'default', label: v }
        return <Tag color={s.color}>{s.label}</Tag>
      },
    },
    {
      title: '审批备注', dataIndex: 'comment',
      render: (v: string) => v
        ? <Text type="secondary" style={{ fontSize: 12 }}>{v}</Text>
        : <Text type="secondary" style={{ fontSize: 12, fontStyle: 'italic' }}>（无）</Text>,
    },
    {
      title: '', width: 70, align: 'center' as const,
      render: (_: any, record: any) => (
        <span
          onClick={() => setSelectedClaimId(record.claim_id)}
          style={{ color: '#1D4ED8', cursor: 'pointer', fontSize: 12 }}
        >
          <EyeOutlined /> 详情
        </span>
      ),
    },
  ]

  return (
    <div className="page-wrapper">
      {ctx}
      <div className="page-title">🗂️ 我的审批记录</div>
      <div className="page-subtitle">查看所有历史审批操作，点击「详情」可查看发票原件</div>

      <Row gutter={16} style={{ marginBottom: 20 }}>
        {[
          ['审批总数', records.length, '#0F172A'],
          ['已通过', approvedCnt, '#10B981'],
          ['已驳回', rejectedCnt, '#EF4444'],
          ['累计通过金额', `¥${totalAmt.toFixed(2)}`, '#1D4ED8'],
        ].map(([label, val, color]) => (
          <Col span={6} key={label as string}>
            <Card size="small" className="stat-card">
              <Statistic
                title={label}
                value={val}
                valueStyle={{ fontWeight: 700, color: color as string, fontSize: 15 }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 48 }}><Spin size="large" /></div>
      ) : records.length === 0 ? (
        <div className="card-white" style={{ padding: '48px 0', textAlign: 'center' }}>
          <Empty description="暂无审批记录" />
        </div>
      ) : (
        <div className="card-white" style={{ padding: 0, overflow: 'hidden' }}>
          <Table
            columns={cols}
            dataSource={records}
            rowKey="approval_id"
            size="middle"
            pagination={{ pageSize: 20, showSizeChanger: false, showTotal: (t) => `共 ${t} 条` }}
            onRow={(record) => ({
              onClick: () => setSelectedClaimId(record.claim_id),
              style: { cursor: 'pointer' },
            })}
          />
        </div>
      )}

      <ClaimDetailModal
        claimId={selectedClaimId}
        onClose={() => setSelectedClaimId(null)}
      />
    </div>
  )
}