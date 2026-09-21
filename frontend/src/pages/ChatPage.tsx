import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import { Bot, Send, Plus, LogOut, Settings, Star, LayoutDashboard, MessageSquare, ChevronDown, Info } from 'lucide-react'
import toast from 'react-hot-toast'
import { useSendMessage, useSessions, useSubmitFeedback } from '@/api/hooks'
import { useAuthStore } from '@/store/auth'
import api from '@/api/client'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  intent?: string
  confidence?: number
  query_type?: string
  processing_time_ms?: number
  feedback?: number | null
}

function TypingIndicator() {
  return (
    <div className="flex items-end gap-2 animate-fade-in">
      <div className="w-8 h-8 rounded-full bg-brand-600/20 border border-brand-500/30 flex items-center justify-center flex-shrink-0">
        <Bot className="w-4 h-4 text-brand-400" />
      </div>
      <div className="chat-bubble-bot flex items-center gap-1 py-3">
        <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  )
}

function StarRating({ messageId, onRate }: { messageId: string; onRate: (rating: number) => void }) {
  const [hovered, setHovered] = useState(0)
  const [rated, setRated] = useState(0)

  if (rated > 0) return (
    <div className="flex items-center gap-1 text-xs text-slate-500 mt-1">
      <span className="text-amber-400">{'★'.repeat(rated)}</span> Thanks for the feedback!
    </div>
  )

  return (
    <div className="flex items-center gap-0.5 mt-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          onMouseEnter={() => setHovered(star)}
          onMouseLeave={() => setHovered(0)}
          onClick={() => { setRated(star); onRate(star); }}
          className={`transition-colors ${star <= (hovered || rated) ? 'text-amber-400' : 'text-slate-600'}`}
          title={`Rate ${star} star${star > 1 ? 's' : ''}`}
        >
          <Star className="w-3.5 h-3.5 fill-current" />
        </button>
      ))}
    </div>
  )
}

function QueryTypeBadge({ type }: { type?: string }) {
  if (!type) return null
  const map: Record<string, { label: string; cls: string }> = {
    ANSWERED: { label: '✓ Answered', cls: 'badge-green' },
    UNKNOWN_INSTITUTIONAL: { label: '? Needs Review', cls: 'badge-yellow' },
    OUT_OF_DOMAIN: { label: '⊘ Out of Domain', cls: 'badge-gray' },
  }
  const info = map[type]
  if (!info) return null
  return <span className={info.cls}>{info.label}</span>
}

export default function ChatPage() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: `Hello! I'm the **GIT Smart Chatbot**, your AI assistant for Greenfield Institute of Technology. 🎓\n\nI can help you with:\n- Admissions & enrollment\n- Academic schedules & timetables\n- Faculty & staff information\n- Fees & scholarships\n- Events & extracurricular activities\n- Library, hostel & campus facilities\n\nWhat would you like to know?`,
      query_type: 'ANSWERED',
    },
  ])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [showSidebar, setShowSidebar] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const sendMessage = useSendMessage()
  const submitFeedback = useSubmitFeedback()
  const { data: sessions } = useSessions()

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    const text = input.trim()
    if (!text || sendMessage.isPending) return
    setInput('')

    const userMsg: Message = { id: `u-${Date.now()}`, role: 'user', content: text }
    setMessages((prev) => [...prev, userMsg, { id: 'typing', role: 'assistant', content: '' }])

    try {
      const resp = await sendMessage.mutateAsync({ message: text, session_id: sessionId || undefined })
      setSessionId(resp.session_id)
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== 'typing'),
        {
          id: resp.message_id,
          role: 'assistant',
          content: resp.response,
          intent: resp.intent,
          confidence: resp.confidence,
          query_type: resp.query_type,
          processing_time_ms: resp.processing_time_ms,
          feedback: null,
        },
      ])
    } catch {
      setMessages((prev) => prev.filter((m) => m.id !== 'typing'))
      toast.error('Failed to send message. Please try again.')
    }
  }

  const handleFeedback = async (messageId: string, rating: number) => {
    try {
      await submitFeedback.mutateAsync({ message_id: messageId, rating })
      toast.success('Thank you for your feedback!')
    } catch {
      // Already rated or other error
    }
  }

  const handleLogout = async () => {
    const { refreshToken } = useAuthStore.getState()
    if (refreshToken) {
      try { await api.post('/auth/logout', { refresh_token: refreshToken }) } catch {}
    }
    logout()
    navigate('/login')
  }

  const quickQuestions = [
    'What are the admission requirements?',
    'Who is the HOD of Computer Science?',
    'What events are happening this month?',
    'What is the fee structure?',
    'Tell me about the college',
  ]

  return (
    <div className="h-screen flex bg-surface-950">
      {/* Sidebar */}
      <AnimatePresence>
        {showSidebar && (
          <motion.aside
            initial={{ x: -280 }}
            animate={{ x: 0 }}
            exit={{ x: -280 }}
            className="w-72 border-r border-white/5 flex flex-col bg-surface-900/50"
          >
            {/* Logo */}
            <div className="p-4 border-b border-white/5">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-brand-600 flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                  <div className="font-semibold text-white text-sm">GIT Chatbot</div>
                  <div className="text-xs text-slate-500">AI Assistant</div>
                </div>
              </div>
            </div>

            {/* New Chat */}
            <div className="p-3">
              <button
                onClick={() => { setMessages([{ id: 'welcome', role: 'assistant', content: 'Hello! How can I help you today? Ask me anything about Greenfield Institute of Technology.', query_type: 'ANSWERED' }]); setSessionId(null) }}
                className="btn-secondary w-full justify-center"
                id="new-chat-btn"
              >
                <Plus className="w-4 h-4" /> New Chat
              </button>
            </div>

            {/* Quick Questions */}
            <div className="px-3 pb-2">
              <p className="text-xs text-slate-500 uppercase font-semibold mb-2 px-1">Quick Questions</p>
              <div className="space-y-1">
                {quickQuestions.map((q) => (
                  <button
                    key={q}
                    onClick={() => { setInput(q); inputRef.current?.focus() }}
                    className="w-full text-left px-3 py-2 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-white/5 transition-colors truncate"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>

            {/* Recent Sessions */}
            {sessions && sessions.length > 0 && (
              <div className="px-3 py-2 flex-1 overflow-y-auto">
                <p className="text-xs text-slate-500 uppercase font-semibold mb-2 px-1">Recent Chats</p>
                <div className="space-y-1">
                  {sessions.slice(0, 10).map((s: any) => (
                    <button
                      key={s.id}
                      onClick={() => setSessionId(s.id)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors truncate ${s.id === sessionId ? 'bg-brand-600/20 text-brand-300' : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'}`}
                    >
                      <MessageSquare className="inline w-3 h-3 mr-1.5" />
                      {s.title || 'Chat session'}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* User Footer */}
            <div className="p-3 border-t border-white/5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 min-w-0">
                  <div className="w-8 h-8 rounded-full bg-brand-600/20 border border-brand-500/30 flex items-center justify-center flex-shrink-0">
                    <span className="text-xs font-bold text-brand-400">{user?.name[0]?.toUpperCase()}</span>
                  </div>
                  <div className="min-w-0">
                    <div className="text-xs font-medium text-slate-200 truncate">{user?.name}</div>
                    <div className="text-xs text-slate-500 capitalize">{user?.role}</div>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  {user?.role === 'admin' && (
                    <Link to="/admin" className="btn-ghost p-1.5" title="Admin">
                      <LayoutDashboard className="w-4 h-4" />
                    </Link>
                  )}
                  <button onClick={handleLogout} className="btn-ghost p-1.5" title="Logout" id="logout-btn">
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="px-4 py-3 border-b border-white/5 flex items-center gap-3 bg-surface-900/30">
          <button onClick={() => setShowSidebar(!showSidebar)} className="btn-ghost p-1.5">
            <MessageSquare className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-sm font-medium text-slate-200">GIT Smart Chatbot</span>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          <AnimatePresence>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} gap-2 items-end`}
              >
                {msg.role === 'assistant' && msg.id !== 'typing' && (
                  <div className="w-8 h-8 rounded-full bg-brand-600/20 border border-brand-500/30 flex items-center justify-center flex-shrink-0 mb-5">
                    <Bot className="w-4 h-4 text-brand-400" />
                  </div>
                )}

                {msg.id === 'typing' ? (
                  <TypingIndicator />
                ) : (
                  <div className={msg.role === 'user' ? 'text-right' : ''}>
                    <div className={msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-bot'}>
                      {msg.role === 'assistant' ? (
                        <div className="prose-dark">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                      ) : msg.content}
                    </div>
                    {msg.role === 'assistant' && msg.id !== 'welcome' && (
                      <div className="flex items-center gap-2 mt-1 ml-1">
                        <QueryTypeBadge type={msg.query_type} />
                        {msg.intent && msg.intent !== 'unknown' && (
                          <span className="badge-blue">{msg.intent}</span>
                        )}
                        {msg.processing_time_ms !== undefined && (
                          <span className="text-xs text-slate-600">{msg.processing_time_ms}ms</span>
                        )}
                        {msg.id && (
                          <StarRating messageId={msg.id} onRate={(r) => handleFeedback(msg.id, r)} />
                        )}
                      </div>
                    )}
                  </div>
                )}

                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center flex-shrink-0">
                    <span className="text-xs font-bold text-white">{user?.name[0]?.toUpperCase()}</span>
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-white/5">
          <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-2xl px-4 py-2 focus-within:border-brand-500/50 transition-colors">
            <input
              ref={inputRef}
              id="chat-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Ask anything about Greenfield Institute..."
              className="flex-1 bg-transparent text-slate-100 placeholder-slate-500 text-sm outline-none"
              disabled={sendMessage.isPending}
            />
            <button
              id="send-btn"
              onClick={handleSend}
              disabled={!input.trim() || sendMessage.isPending}
              className="w-8 h-8 rounded-xl bg-brand-600 hover:bg-brand-500 flex items-center justify-center transition-colors disabled:opacity-40"
            >
              <Send className="w-4 h-4 text-white" />
            </button>
          </div>
          <p className="text-center text-xs text-slate-600 mt-2">
            AI-generated responses · Verify important information with college administration
          </p>
        </div>
      </div>
    </div>
  )
}
