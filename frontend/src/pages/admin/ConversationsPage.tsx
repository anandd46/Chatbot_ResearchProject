import { useAdminConversations } from '@/api/hooks'
import { useState } from 'react'
import { MessageSquare } from 'lucide-react'
import api from '@/api/client'

export default function ConversationsPage() {
  const [page, setPage] = useState(1)
  const { data: conversations, isLoading } = useAdminConversations(page)
  const [selectedConv, setSelectedConv] = useState<string | null>(null)
  const [messages, setMessages] = useState<any[]>([])

  const loadMessages = async (convId: string) => {
    setSelectedConv(convId)
    const resp = await api.get(`/admin/conversations/${convId}/messages`)
    setMessages(resp.data)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-header">All Conversations</h1>
        <p className="page-subtitle">Review user conversations across the platform</p>
      </div>
      <div className="flex gap-4">
        {/* Conversation List */}
        <div className="w-80 glass-card overflow-hidden flex-shrink-0">
          <div className="p-3 border-b border-white/5 text-sm font-medium text-slate-300">Conversations</div>
          <div className="overflow-y-auto max-h-[60vh]">
            {isLoading ? (
              <div className="p-8 text-center text-slate-500">Loading...</div>
            ) : (
              (conversations || []).map((c: any) => (
                <button
                  key={c.id}
                  onClick={() => loadMessages(c.id)}
                  className={`w-full text-left p-3 border-b border-white/5 hover:bg-white/5 transition-colors ${selectedConv === c.id ? 'bg-brand-600/10' : ''}`}
                >
                  <div className="flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 text-slate-500 flex-shrink-0" />
                    <div className="min-w-0">
                      <div className="text-sm text-slate-200 truncate">{c.title || 'Untitled'}</div>
                      <div className="text-xs text-slate-500">{new Date(c.started_at).toLocaleDateString()}</div>
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 glass-card p-4 overflow-y-auto max-h-[60vh]">
          {selectedConv ? (
            <div className="space-y-3">
              {messages.map((m: any) => (
                <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[75%] ${m.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-bot'}`}>
                    <div className="text-sm">{m.content}</div>
                    {m.role === 'assistant' && (
                      <div className="flex items-center gap-2 mt-1">
                        {m.query_type && <span className={`badge text-xs ${m.query_type === 'ANSWERED' ? 'badge-green' : 'badge-yellow'}`}>{m.query_type}</span>}
                        {m.intent && <span className="badge-blue text-xs">{m.intent}</span>}
                        {m.processing_time_ms && <span className="text-xs text-slate-500">{m.processing_time_ms}ms</span>}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-500">
              Select a conversation to view messages
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
