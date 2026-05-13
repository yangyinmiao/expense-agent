import { useState, useRef, useEffect } from 'react'
import { Input, Button, Spin, message, Typography, Avatar } from 'antd'
import { SendOutlined, RobotOutlined, UserOutlined, DeleteOutlined } from '@ant-design/icons'
import { chatWithAgent } from '../api/agent'

const { Text } = Typography

interface Msg { role: 'user' | 'assistant'; content: string }

const EXAMPLES = [
  '我这个月报销了多少？',
  '现在有几条待审批？',
  '报销规则是什么？',
  '帮我看看我的申请状态',
]

export default function AgentChat() {
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const [msgApi, ctx] = message.useMessage()

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [msgs])

  const send = async (text: string) => {
    if (!text.trim()) return
    setMsgs((p) => [...p, { role: 'user', content: text }])
    setInput('')
    setLoading(true)
    try {
      const { data } = await chatWithAgent(text)
      setMsgs((p) => [...p, { role: 'assistant', content: data.answer ?? '暂无回答' }])
    } catch (e: any) {
      const ans = `⚠️ 服务暂不可用（${e.response?.status ?? '网络错误'}）`
      setMsgs((p) => [...p, { role: 'assistant', content: ans }])
    } finally { setLoading(false) }
  }

  return (
    <div className="page-wrapper" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 56px)' }}>
      {ctx}
      <div className="page-title">🤖 智能问答</div>
      <div className="page-subtitle">用自然语言查询报销数据，无需手动翻表格</div>

      {/* 示例提示 */}
      {msgs.length === 0 && (
        <div style={{ marginBottom: 16 }}>
          <Text type="secondary" style={{ fontSize: 13 }}>💡 你可以这样问：</Text>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
            {EXAMPLES.map((e) => (
              <span key={e}
                onClick={() => send(e)}
                style={{
                  cursor: 'pointer', padding: '5px 12px',
                  background: '#EFF6FF', border: '1px solid #BFDBFE',
                  borderRadius: 20, fontSize: 13, color: '#1D4ED8',
                  transition: 'all .15s',
                }}
              >{e}</span>
            ))}
          </div>
        </div>
      )}

      {/* 对话区 */}
      <div style={{
        flex: 1, overflowY: 'auto', padding: '8px 0', marginBottom: 12,
      }}>
        {msgs.map((m, i) => (
          <div key={i} style={{
            display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
            marginBottom: 12, gap: 8, alignItems: 'flex-start',
          }}>
            {m.role === 'assistant' && (
              <Avatar icon={<RobotOutlined />} style={{ background: '#1D4ED8', flexShrink: 0 }} />
            )}
            <div style={{
              maxWidth: '72%', padding: '10px 14px', borderRadius: 12,
              background: m.role === 'user' ? '#1D4ED8' : '#fff',
              color: m.role === 'user' ? '#fff' : '#0F172A',
              boxShadow: '0 1px 3px rgba(0,0,0,.07)',
              whiteSpace: 'pre-wrap', lineHeight: 1.6, fontSize: 14,
              borderTopRightRadius: m.role === 'user' ? 2 : 12,
              borderTopLeftRadius: m.role === 'assistant' ? 2 : 12,
            }}>
              {m.content}
            </div>
            {m.role === 'user' && (
              <Avatar icon={<UserOutlined />} style={{ background: '#475569', flexShrink: 0 }} />
            )}
          </div>
        ))}
        {loading && (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 12 }}>
            <Avatar icon={<RobotOutlined />} style={{ background: '#1D4ED8' }} />
            <div style={{
              padding: '10px 14px', background: '#fff', borderRadius: 12,
              boxShadow: '0 1px 3px rgba(0,0,0,.07)',
            }}>
              <Spin size="small" /> <Text type="secondary" style={{ marginLeft: 8, fontSize: 13 }}>思考中...</Text>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* 输入框 */}
      <div style={{
        display: 'flex', gap: 8,
        padding: '12px 16px', background: '#fff',
        borderRadius: 12, boxShadow: '0 -1px 6px rgba(0,0,0,.05)',
      }}>
        <Input
          value={input} onChange={(e) => setInput(e.target.value)}
          onPressEnter={() => send(input)}
          placeholder="请输入您的问题，如：我上个月餐饮报销了多少？"
          size="large"
          style={{ border: 'none', boxShadow: 'none', background: 'transparent' }}
        />
        {msgs.length > 0 && (
          <Button icon={<DeleteOutlined />} type="text"
            onClick={() => setMsgs([])} style={{ color: '#94A3B8' }} />
        )}
        <Button type="primary" icon={<SendOutlined />} size="large"
          disabled={!input.trim() || loading}
          onClick={() => send(input)}>
          发送
        </Button>
      </div>
    </div>
  )
}