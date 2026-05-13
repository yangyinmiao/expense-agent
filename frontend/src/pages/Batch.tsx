import { useState } from 'react'
import {
  Upload, Button, Input, Row, Col, Card, Statistic,
  Alert, Tag, Divider, message, Spin, Typography,
} from 'antd'
import { InboxOutlined, RocketOutlined } from '@ant-design/icons'
import { batchUpload } from '../api/invoices'
import { createClaim, submitClaim } from '../api/claims'

const { Dragger } = Upload
const { Text } = Typography

export default function Batch() {
  const [files, setFiles] = useState<File[]>([])
  const [desc, setDesc] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<any>(null)
  const [msgApi, ctx] = message.useMessage()

  const handleSubmit = async () => {
    if (!files.length) return
    setLoading(true); setResults(null)
    try {
      const { data } = await batchUpload(files)
      // auto submit successful ones
      const enriched = await Promise.all(data.results.map(async (item: any) => {
        if (item.success && item.validation['通过']) {
          try {
            const cr = await createClaim(item.invoice_id, desc)
            const cid = cr.data.claim_id
            await submitClaim(cid)
            return { ...item, claim_id: cid }
          } catch { return item }
        }
        return item
      }))
      setResults({ ...data, results: enriched })
    } catch (e: any) {
      msgApi.error(e.response?.data?.detail ?? '上传失败')
    } finally { setLoading(false) }
  }

  return (
    <div className="page-wrapper">
      {ctx}
      <div className="page-title">📦 批量上传发票</div>
      <div className="page-subtitle">一次最多 10 张，并发识别，识别通过后自动提交申请</div>

      <div className="card-white">
        <Dragger
          accept=".jpg,.jpeg,.png,.pdf"
          multiple
          beforeUpload={(_, list) => { setFiles(list); return false }}
          showUploadList
          fileList={files.map((f) => ({ uid: f.name, name: f.name, status: 'done' } as any))}
          onRemove={(f) => setFiles((prev) => prev.filter((x) => x.name !== f.name))}
          style={{ background: '#F8FAFC' }}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined style={{ fontSize: 40, color: '#1D4ED8' }} />
          </p>
          <p style={{ fontWeight: 600, color: '#0F172A', margin: '8px 0 4px' }}>
            点击或拖拽，可多选发票
          </p>
          <p style={{ color: '#94A3B8', fontSize: 13 }}>支持 JPG、PNG、PDF，每次最多 10 张</p>
        </Dragger>

        <Input
          value={desc} onChange={(e) => setDesc(e.target.value)}
          placeholder="统一报销说明，如：Q2 差旅费"
          style={{ marginTop: 12 }}
        />

        <Button
          type="primary" icon={<RocketOutlined />} size="large"
          disabled={!files.length} loading={loading}
          onClick={handleSubmit} style={{ marginTop: 12 }}
        >
          批量识别并提交 ({files.length} 个文件)
        </Button>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '32px 0' }}>
          <Spin size="large" tip={`正在并发识别 ${files.length} 张...`} />
        </div>
      )}

      {results && (
        <>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            {[['提交总数', results.total], ['识别成功', results.success_count], ['识别失败', results.failed_count]].map(([l, v]) => (
              <Col span={8} key={l as string}>
                <Card size="small" className="stat-card">
                  <Statistic title={l} value={v}
                    valueStyle={{ color: l === '识别失败' && v > 0 ? '#DC2626' : '#0F172A', fontWeight: 700 }} />
                </Card>
              </Col>
            ))}
          </Row>

          {results.results.map((item: any, i: number) => (
            <div key={i} className="card-white" style={{ borderLeft: `3px solid ${item.success ? '#22C55E' : '#EF4444'}` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <Tag color={item.success ? 'success' : 'error'}>{item.success ? '✅ 成功' : '❌ 失败'}</Tag>
                <Text strong>{item.filename}</Text>
                {item.success && <Text type="secondary">· {item.info?.['供应商名称']} · ¥{item.info?.['价税合计']}</Text>}
                {item.claim_id && <Tag color="blue">已提交申请 #{item.claim_id}</Tag>}
              </div>
              {item.success
                ? item.validation['通过']
                  ? <Text type="success" style={{ fontSize: 13 }}>{item.validation['建议']}</Text>
                  : <Alert type="warning" message="校验未通过" description={item.validation['问题列表'].join('；')} style={{ fontSize: 13 }} />
                : <Text type="danger">{item.error}</Text>
              }
            </div>
          ))}
        </>
      )}
    </div>
  )
}