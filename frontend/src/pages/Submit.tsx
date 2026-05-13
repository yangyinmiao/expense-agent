import { useState } from 'react'
import {
  Upload, Button, Input, Card, Row, Col, Statistic,
  Divider, Alert, Collapse, message, Spin, Typography, Space,
} from 'antd'
import { InboxOutlined, SearchOutlined } from '@ant-design/icons'
import { uploadInvoice } from '../api/invoices'
import { createClaim, submitClaim } from '../api/claims'

const { Dragger } = Upload
const { TextArea } = Input
const { Text } = Typography

export default function Submit() {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [desc, setDesc] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [msgApi, ctx] = message.useMessage()

  const handleSubmit = async () => {
    if (!file) return
    setLoading(true); setResult(null)
    try {
      const { data } = await uploadInvoice(file)
      const { info, validation, invoice_id } = data
      if (validation['通过']) {
        const cr = await createClaim(invoice_id, desc)
        const claimId = cr.data.claim_id
        await submitClaim(claimId)
        setResult({ ...data, claim_id: claimId })
        msgApi.success(`申请 #${claimId} 已提交，等待审批`)
      } else {
        setResult(data)
      }
    } catch (e: any) {
      msgApi.error(e.response?.data?.detail ?? '识别失败')
    } finally { setLoading(false) }
  }

  const beforeUpload = (f: File) => {
    setFile(f)
    if (f.type.startsWith('image/')) {
      const url = URL.createObjectURL(f)
      setPreview(url)
    } else {
      setPreview(null)
    }
    return false
  }

  return (
    <div className="page-wrapper">
      {ctx}
      <div className="page-title">📤 提交报销</div>
      <div className="page-subtitle">上传发票，AI 自动识别并完成规则校验</div>

      <Row gutter={24}>
        <Col xs={24} md={12}>
          <div className="card-white">
            <Dragger
              accept=".jpg,.jpeg,.png,.pdf"
              multiple={false}
              beforeUpload={beforeUpload}
              showUploadList={false}
              style={{ background: '#F8FAFC' }}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined style={{ fontSize: 40, color: '#1D4ED8' }} />
              </p>
              <p style={{ fontWeight: 600, color: '#0F172A', margin: '8px 0 4px' }}>
                点击或拖拽发票到此处
              </p>
              <p style={{ color: '#94A3B8', fontSize: 13 }}>
                支持 JPG、PNG、PDF，最大 20MB
              </p>
            </Dragger>

            {file && (
              <div style={{ marginTop: 12, padding: '8px 12px', background: '#EFF6FF',
                borderRadius: 8, fontSize: 13, color: '#1D4ED8' }}>
                已选择：<b>{file.name}</b>
              </div>
            )}

            <div style={{ marginTop: 16 }}>
              <Text type="secondary" style={{ fontSize: 13 }}>报销说明（可选）</Text>
              <TextArea
                value={desc}
                onChange={(e) => setDesc(e.target.value)}
                placeholder="简要描述报销用途，如：5月研发部团队餐饮"
                rows={3}
                style={{ marginTop: 6 }}
              />
            </div>

            <Button
              type="primary" size="large" block
              icon={<SearchOutlined />}
              disabled={!file} loading={loading}
              onClick={handleSubmit}
              style={{ marginTop: 16 }}
            >
              识别并提交
            </Button>
          </div>
        </Col>

        <Col xs={24} md={12}>
          {preview && (
            <div className="card-white" style={{ textAlign: 'center' }}>
              <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>发票预览</Text>
              <img src={preview} alt="invoice" style={{
                maxWidth: '100%', maxHeight: 320, borderRadius: 8, objectFit: 'contain',
              }} />
            </div>
          )}

          {loading && (
            <div className="card-white" style={{ textAlign: 'center', padding: '40px 0' }}>
              <Spin size="large" tip="AI 正在识别发票..." />
            </div>
          )}

          {result && (
            <Space direction="vertical" style={{ width: '100%' }} size={12}>
              <Row gutter={12}>
                {[
                  ['价税合计', `¥${result.info['价税合计'] ?? '—'}`],
                  ['费用类别', result.info['费用类别'] ?? '—'],
                  ['开票日期', result.info['开票日期'] ?? '—'],
                  ['供应商',   result.info['供应商名称'] ?? '—'],
                ].map(([label, val]) => (
                  <Col span={12} key={label}>
                    <Card size="small" className="stat-card" style={{ marginBottom: 8 }}>
                      <Statistic title={label} value={val} valueStyle={{ fontSize: 15, fontWeight: 700, color: '#0F172A' }} />
                    </Card>
                  </Col>
                ))}
              </Row>

              {result.validation['通过'] ? (
                <Alert type="success"
                  message={`✅ 规则校验通过 — 申请 #${result.claim_id} 已提交`}
                  description={result.validation['建议']} showIcon />
              ) : (
                <Alert type="error" message="规则校验未通过" showIcon
                  description={
                    <ul style={{ margin: '4px 0 0', paddingLeft: 20 }}>
                      {result.validation['问题列表'].map((p: string, i: number) => (
                        <li key={i}>{p}</li>
                      ))}
                    </ul>
                  } />
              )}

              <Collapse size="small" items={[{
                key: '1', label: '查看完整识别数据',
                children: <pre style={{ fontSize: 12, overflow: 'auto', maxHeight: 200 }}>
                  {JSON.stringify(result.info, null, 2)}
                </pre>,
              }]} />
            </Space>
          )}
        </Col>
      </Row>
    </div>
  )
}