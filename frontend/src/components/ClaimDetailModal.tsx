import { useEffect, useState } from 'react'
import {
  Modal, Row, Col, Descriptions, Tag, Image, Timeline,
  Spin, Divider, Empty, Typography, Badge, Button, Space,
} from 'antd'
import {
  CheckCircleOutlined, CloseCircleOutlined,
  ClockCircleOutlined, DownloadOutlined, FilePdfOutlined, FileImageOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { getClaimDetail } from '../api/claims'

const { Text, Title } = Typography

const STATUS_MAP: Record<string, { color: string; label: string }> = {
  draft:            { color: 'default',  label: '草稿' },
  pending:          { color: 'warning',  label: '待主管审批' },
  manager_approved: { color: 'cyan',     label: '主管已批，待财务' },
  finance_approved: { color: 'success',  label: '财务已批' },
  rejected:         { color: 'error',    label: '已驳回' },
  paid:             { color: 'blue',     label: '已打款' },
}

interface Props {
  claimId: number | null
  onClose: () => void
}

function InvoiceViewer({ url, fileId }: { url: string; fileId?: string }) {
  const isPdf = fileId?.toLowerCase().endsWith('.pdf') || url.includes('.pdf')

  if (!url) return (
    <div style={{
      border: '1px dashed #CBD5E1', borderRadius: 8,
      padding: '40px 0', textAlign: 'center', color: '#94A3B8',
    }}>
      <FileImageOutlined style={{ fontSize: 32, marginBottom: 8, display: 'block' }} />
      <div style={{ fontSize: 13 }}>暂无附件</div>
    </div>
  )

  return (
    <div>
      {isPdf ? (
        <div style={{ border: '1px solid #E2E8F0', borderRadius: 8, overflow: 'hidden' }}>
          <div style={{
            background: '#F8FAFC', padding: '8px 12px',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            borderBottom: '1px solid #E2E8F0',
          }}>
            <span style={{ fontSize: 13, color: '#475569' }}>
              <FilePdfOutlined style={{ color: '#EF4444', marginRight: 6 }} />
              PDF 发票
            </span>
            <Button
              size="small" icon={<DownloadOutlined />} type="link"
              href={url} target="_blank" download
              style={{ padding: 0, fontSize: 12 }}
            >
              下载原件
            </Button>
          </div>
          <iframe
            src={url}
            style={{ width: '100%', height: 420, border: 'none', display: 'block' }}
            title="发票预览"
          />
        </div>
      ) : (
        <div style={{
          border: '1px solid #E2E8F0', borderRadius: 8, overflow: 'hidden',
          background: '#F8FAFC',
        }}>
          <div style={{
            background: '#F8FAFC', padding: '8px 12px',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            borderBottom: '1px solid #E2E8F0',
          }}>
            <span style={{ fontSize: 13, color: '#475569' }}>
              <FileImageOutlined style={{ color: '#1D4ED8', marginRight: 6 }} />
              图片发票
            </span>
            <Button
              size="small" icon={<DownloadOutlined />} type="link"
              href={url} target="_blank" download
              style={{ padding: 0, fontSize: 12 }}
            >
              下载原件
            </Button>
          </div>
          <Image
            src={url}
            alt="发票原件"
            style={{ maxWidth: '100%', maxHeight: 420, objectFit: 'contain', display: 'block' }}
            placeholder={
              <div style={{ padding: 40, textAlign: 'center' }}>
                <Spin />
                <div style={{ marginTop: 8, color: '#94A3B8', fontSize: 12 }}>加载中...</div>
              </div>
            }
          />
        </div>
      )}
    </div>
  )
}

export default function ClaimDetailModal({ claimId, onClose }: Props) {
  const [loading, setLoading] = useState(false)
  const [detail, setDetail] = useState<any>(null)

  useEffect(() => {
    if (!claimId) return
    setLoading(true)
    setDetail(null)
    getClaimDetail(claimId)
      .then((r) => setDetail(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [claimId])

  const inv = detail?.invoice
  const claim = detail?.claim
  const approvals = detail?.approvals ?? []
  const status = STATUS_MAP[claim?.status] ?? { color: 'default', label: claim?.status }

  return (
    <Modal
      open={!!claimId}
      onCancel={onClose}
      footer={null}
      width={900}
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontWeight: 700, fontSize: 16 }}>申请详情</span>
          {claim && (
            <>
              <Text type="secondary" style={{ fontWeight: 400, fontSize: 14 }}>
                #{claim.id} · {claim.user_name}
              </Text>
              <Tag color={status.color}>{status.label}</Tag>
            </>
          )}
        </div>
      }
      styles={{ body: { padding: '16px 24px', maxHeight: '82vh', overflowY: 'auto' } }}
    >
      {loading && <div style={{ textAlign: 'center', padding: 48 }}><Spin size="large" /></div>}

      {!loading && detail && (
        <Row gutter={24}>
          {/* 左列：发票信息 + 审批记录 */}
          <Col xs={24} md={13}>
            <Title level={5} style={{ marginTop: 0, marginBottom: 12, color: '#1D4ED8' }}>
              📋 发票信息
            </Title>
            <Descriptions
              bordered size="small" column={2}
              labelStyle={{ background: '#F8FAFC', fontWeight: 500, width: 88 }}
            >
              <Descriptions.Item label="发票类型" span={2}>{inv.invoice_type ?? '—'}</Descriptions.Item>
              <Descriptions.Item label="发票号码" span={2}>
                <Text code style={{ fontSize: 12 }}>{inv.invoice_number ?? '—'}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="供应商" span={2}>{inv.vendor ?? '—'}</Descriptions.Item>
              <Descriptions.Item label="开票日期">{inv.invoice_date ?? '—'}</Descriptions.Item>
              <Descriptions.Item label="费用类别">
                <Tag color="blue">{inv.category ?? '—'}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="不含税额">
                {inv.amount != null ? `¥${Number(inv.amount).toFixed(2)}` : '—'}
              </Descriptions.Item>
              <Descriptions.Item label="税额">
                {inv.tax != null ? `¥${Number(inv.tax).toFixed(2)}` : '—'}
              </Descriptions.Item>
              <Descriptions.Item label="价税合计" span={2}>
                <Text strong style={{ fontSize: 15, color: '#1D4ED8' }}>
                  {inv.total != null ? `¥${Number(inv.total).toFixed(2)}` : '—'}
                </Text>
              </Descriptions.Item>
              <Descriptions.Item label="报销说明" span={2}>
                {claim.description || <Text type="secondary">（无）</Text>}
              </Descriptions.Item>
              <Descriptions.Item label="提交时间" span={2}>
                {claim.submitted_at ? dayjs(claim.submitted_at).format('YYYY-MM-DD HH:mm') : '—'}
              </Descriptions.Item>
            </Descriptions>

            {inv.raw_json && (
              <details style={{ marginTop: 10 }}>
                <summary style={{ cursor: 'pointer', color: '#6B7280', fontSize: 12, userSelect: 'none' }}>
                  ▶ 查看 AI 完整识别数据
                </summary>
                <pre style={{
                  marginTop: 6, padding: '8px 12px',
                  background: '#F8FAFC', borderRadius: 6,
                  fontSize: 11, overflow: 'auto', maxHeight: 160, color: '#374151',
                  border: '1px solid #E2E8F0',
                }}>
                  {JSON.stringify(inv.raw_json, null, 2)}
                </pre>
              </details>
            )}

            <Divider style={{ margin: '14px 0' }} />

            <Title level={5} style={{ marginBottom: 12, color: '#1D4ED8' }}>📌 审批记录</Title>
            {approvals.length === 0 ? (
              <Empty description="暂无审批记录" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            ) : (
              <Timeline
                items={approvals.map((ap: any) => ({
                  dot: ap.action === 'approved'
                    ? <CheckCircleOutlined style={{ color: '#22C55E' }} />
                    : <CloseCircleOutlined style={{ color: '#EF4444' }} />,
                  children: (
                    <div>
                      <Space size={6}>
                        <Text strong style={{ fontSize: 13 }}>{ap.approver_name}</Text>
                        <Tag color={ap.action === 'approved' ? 'success' : 'error'} style={{ fontSize: 11 }}>
                          {ap.action === 'approved' ? '通过' : '驳回'}
                        </Tag>
                      </Space>
                      {ap.comment && (
                        <div style={{ fontSize: 12, color: '#6B7280', marginTop: 2 }}>
                          备注：{ap.comment}
                        </div>
                      )}
                      <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 2 }}>
                        {ap.created_at ? dayjs(ap.created_at).format('YYYY-MM-DD HH:mm') : ''}
                      </div>
                    </div>
                  ),
                }))}
              />
            )}
          </Col>

          {/* 右列：发票原件 */}
          <Col xs={24} md={11}>
            <Title level={5} style={{ marginTop: 0, marginBottom: 12, color: '#1D4ED8' }}>
              🧾 发票原件
            </Title>
            <InvoiceViewer url={inv.image_url} fileId={inv.file_id ?? ''} />

            <div style={{
              marginTop: 14, padding: '10px 14px',
              background: '#F0F7FF', borderRadius: 8,
              border: '1px solid #BFDBFE',
            }}>
              <Text style={{ fontSize: 12, color: '#1D4ED8', fontWeight: 600 }}>当前状态</Text>
              <div style={{ marginTop: 6 }}>
                <Badge
                  status={
                    claim.status === 'rejected' ? 'error'
                    : ['finance_approved', 'paid'].includes(claim.status) ? 'success'
                    : 'processing'
                  }
                  text={<Text style={{ fontSize: 13, fontWeight: 500 }}>{status.label}</Text>}
                />
              </div>
            </div>
          </Col>
        </Row>
      )}

      {!loading && !detail && <Empty description="加载失败，请重试" />}
    </Modal>
  )
}