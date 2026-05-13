import { useEffect, useState } from 'react'
import {
  Table, Tag, Button, Input, Space, Popconfirm, Empty,
  Spin, message, Typography,
} from 'antd'
import { CheckOutlined, CloseOutlined, EyeOutlined } from '@ant-design/icons'
import { getPending, approveClaim, rejectClaim } from '../api/claims'
import { useAuth } from '../context/AuthContext'
import ClaimDetailModal from '../components/ClaimDetailModal'

const { Text } = Typography

export default function Pending() {
  const { user } = useAuth()
  const [claims, setClaims] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [comments, setComments] = useState<Record<number, string>>({})
  const [acting, setActing] = useState<number | null>(null)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [msgApi, ctx] = message.useMessage()

  const load = () => {
    setLoading(true)
    getPending().then((r) => setClaims(r.data)).catch(() => msgApi.error('获取失败'))
      .finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [])

  if (!['manager', 'finance', 'admin'].includes(user?.role ?? '')) {
    return (
      <div className="page-wrapper">
        <Empty description="此页面仅限主管 / 财务 / 管理员使用" />
      </div>
    )
  }

  const act = async (id: number, type: 'approve' | 'reject') => {
    setActing(id)
    try {
      const comment = comments[id] ?? ''
      if (type === 'approve') await approveClaim(id, comment)
      else await rejectClaim(id, comment || '不符合报销规定')
      msgApi.success(type === 'approve' ? '已通过' : '已驳回')
      load()
    } catch (e: any) {
      msgApi.error(e.response?.data?.detail ?? '操作失败')
    } finally { setActing(null) }
  }

  const cols = [
    { title: '申请编号', dataIndex: 'id', render: (v: number) => `#${v}`, width: 90 },
    { title: '申请人', dataIndex: 'user_id', width: 80 },
    { title: '供应商', dataIndex: 'vendor', render: (v: string) => v || '—' },
    { title: '金额', dataIndex: 'total',
      render: (v: number) => v ? (
        <Text strong style={{ color: '#1D4ED8' }}>¥{v.toFixed(2)}</Text>
      ) : '—', width: 110 },
    { title: '类别', dataIndex: 'category', render: (v: string) => v ? <Tag>{v}</Tag> : '—', width: 100 },
    { title: '发票日期', dataIndex: 'invoice_date', render: (v: string) => v || '—', width: 110 },
    { title: '说明', dataIndex: 'description', render: (v: string) => v || '—' },
    {
      title: '操作', width: 360,
      render: (_: any, record: any) => (
        <Space size={4} onClick={(e) => e.stopPropagation()}>
          <Button
            size="small" icon={<EyeOutlined />}
            onClick={() => setSelectedId(record.id)}
            style={{ color: '#1D4ED8', borderColor: '#1D4ED8' }}
          >详情</Button>
          <Input
            size="small" placeholder="审批备注"
            value={comments[record.id] ?? ''}
            onChange={(e) => setComments((p) => ({ ...p, [record.id]: e.target.value }))}
            style={{ width: 110 }}
          />
          <Popconfirm title="确认通过此申请？"
            onConfirm={() => act(record.id, 'approve')} okText="确认" cancelText="取消">
            <Button type="primary" size="small" icon={<CheckOutlined />}
              loading={acting === record.id}>通过</Button>
          </Popconfirm>
          <Popconfirm title="确认驳回此申请？"
            onConfirm={() => act(record.id, 'reject')} okText="确认" okType="danger" cancelText="取消">
            <Button danger size="small" icon={<CloseOutlined />}
              loading={acting === record.id}>驳回</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div className="page-wrapper">
      {ctx}
      <div className="page-title">✅ 待审批列表</div>
      <div className="page-subtitle">点击「详情」可查看发票原件，填写备注后点击通过/驳回</div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 48 }}><Spin size="large" /></div>
      ) : claims.length === 0 ? (
        <div className="card-white" style={{ padding: '48px 0', textAlign: 'center' }}>
          <Empty description="🎉 暂无待审批申请" />
        </div>
      ) : (
        <div className="card-white" style={{ padding: 0, overflow: 'hidden' }}>
          <Table
            columns={cols}
            dataSource={claims}
            rowKey="id"
            size="middle"
            pagination={{ pageSize: 15, showSizeChanger: false }}
            onRow={(record) => ({
              style: { cursor: 'pointer' },
            })}
          />
        </div>
      )}

      <ClaimDetailModal
        claimId={selectedId}
        onClose={() => setSelectedId(null)}
      />
    </div>
  )
}