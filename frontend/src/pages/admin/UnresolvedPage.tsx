import { useState } from 'react'
import { useUnresolvedQueries, useUpdateUnresolved, useConvertToKb } from '@/api/hooks'
import { AlertCircle, CheckCircle, Clock, XCircle, Plus } from 'lucide-react'
import toast from 'react-hot-toast'

const STATUS_CONFIG: Record<string, { label: string; badge: string; icon: any }> = {
  OPEN: { label: 'Open', badge: 'badge-red', icon: AlertCircle },
  IN_REVIEW: { label: 'In Review', badge: 'badge-yellow', icon: Clock },
  RESOLVED: { label: 'Resolved', badge: 'badge-green', icon: CheckCircle },
  IGNORED: { label: 'Ignored', badge: 'badge-gray', icon: XCircle },
}

function ConvertModal({ query, onClose, onSave }: any) {
  const [form, setForm] = useState({
    category: '',
    question: query?.query || '',
    answer: '',
    keywords: '',
    source_title: '',
    source_url: '',
    source_type: 'manual',
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="glass-card w-full max-w-xl p-6 animate-fade-in">
        <h2 className="font-bold text-white text-lg mb-2">Convert to Knowledge Entry</h2>
        <p className="text-sm text-slate-400 mb-5">Create a KB entry from this unresolved query to improve future responses.</p>
        <div className="space-y-4">
          <div>
            <label className="input-label">Original Query</label>
            <div className="p-2 bg-white/5 rounded-lg text-sm text-slate-300 italic">"{query?.query}"</div>
          </div>
          <div>
            <label className="input-label">Category *</label>
            <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="input-field">
              <option value="">Select</option>
              {['admissions', 'schedule', 'staff', 'fees', 'events', 'library', 'hostel', 'exam', 'facilities', 'contact', 'general'].map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="input-label">Canonical Question *</label>
            <input type="text" value={form.question} onChange={(e) => setForm({ ...form, question: e.target.value })} className="input-field" />
          </div>
          <div>
            <label className="input-label">Answer *</label>
            <textarea rows={3} value={form.answer} onChange={(e) => setForm({ ...form, answer: e.target.value })} className="input-field resize-none" placeholder="Correct answer for this query..." />
          </div>
          <div>
            <label className="input-label">Keywords</label>
            <input type="text" value={form.keywords} onChange={(e) => setForm({ ...form, keywords: e.target.value })} className="input-field" placeholder="comma,separated" />
          </div>
        </div>
        <div className="flex justify-end gap-3 mt-6">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={() => onSave({ ...form, keywords: form.keywords.split(',').map((k: string) => k.trim()).filter(Boolean) })} className="btn-primary" id="convert-kb-btn">
            <Plus className="w-4 h-4" /> Create Knowledge Entry
          </button>
        </div>
      </div>
    </div>
  )
}

export default function UnresolvedPage() {
  const [status, setStatus] = useState<string | undefined>('OPEN')
  const [convertQuery, setConvertQuery] = useState<any>(null)
  const [page, setPage] = useState(1)

  const { data: queries, isLoading } = useUnresolvedQueries(status, page)
  const updateMutation = useUpdateUnresolved()
  const convertMutation = useConvertToKb()

  const updateStatus = async (id: string, newStatus: string) => {
    try {
      await updateMutation.mutateAsync({ id, data: { status: newStatus } })
      toast.success(`Status updated to ${newStatus}`)
    } catch {
      toast.error('Failed to update status')
    }
  }

  const handleConvert = async (form: any) => {
    try {
      await convertMutation.mutateAsync({ id: convertQuery.id, data: form })
      toast.success('Knowledge entry created! Index rebuilt.')
      setConvertQuery(null)
    } catch {
      toast.error('Failed to convert')
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-header">Unresolved Queries</h1>
        <p className="page-subtitle">Queries the chatbot could not answer — review and convert to knowledge entries</p>
      </div>

      {/* Status Filter */}
      <div className="flex gap-2 flex-wrap">
        {[undefined, 'OPEN', 'IN_REVIEW', 'RESOLVED', 'IGNORED'].map((s) => (
          <button
            key={s || 'all'}
            onClick={() => setStatus(s)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors ${status === s ? 'bg-brand-600 border-brand-500 text-white' : 'bg-white/5 border-white/10 text-slate-400 hover:text-slate-200'}`}
          >
            {s ? STATUS_CONFIG[s].label : 'All'}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="glass-card overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-slate-500">Loading...</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Query</th>
                <th>Intent</th>
                <th>Confidence</th>
                <th>Status</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {(queries || []).map((q: any) => {
                const sc = STATUS_CONFIG[q.status]
                return (
                  <tr key={q.id}>
                    <td className="max-w-xs">
                      <div className="text-slate-200">{q.query}</div>
                      {q.admin_notes && <div className="text-xs text-slate-500 mt-0.5 italic">{q.admin_notes}</div>}
                    </td>
                    <td>
                      {q.intent ? <span className="badge-blue capitalize">{q.intent}</span> : '—'}
                    </td>
                    <td>
                      {q.confidence ? (
                        <div className="w-16">
                          <div className="text-xs text-slate-300 mb-0.5">{(q.confidence * 100).toFixed(0)}%</div>
                          <div className="h-1 bg-white/5 rounded-full">
                            <div className="h-1 bg-red-500 rounded-full" style={{ width: `${q.confidence * 100}%` }} />
                          </div>
                        </div>
                      ) : '—'}
                    </td>
                    <td>
                      <span className={sc.badge}>{sc.label}</span>
                    </td>
                    <td className="text-xs text-slate-500">{new Date(q.created_at).toLocaleDateString()}</td>
                    <td>
                      <div className="flex items-center gap-1 flex-wrap">
                        {q.status === 'OPEN' && (
                          <button onClick={() => updateStatus(q.id, 'IN_REVIEW')} className="btn-ghost text-xs py-1 px-2">Review</button>
                        )}
                        {q.status !== 'RESOLVED' && q.status !== 'IGNORED' && (
                          <>
                            <button onClick={() => setConvertQuery(q)} className="btn-ghost text-xs py-1 px-2 text-brand-400" id={`convert-btn-${q.id}`}>
                              <Plus className="w-3 h-3" /> Convert
                            </button>
                            <button onClick={() => updateStatus(q.id, 'IGNORED')} className="btn-ghost text-xs py-1 px-2 text-slate-500">Ignore</button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
              {!isLoading && (!queries || queries.length === 0) && (
                <tr><td colSpan={6} className="text-center py-12 text-slate-500">No queries found for this status</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {convertQuery && <ConvertModal query={convertQuery} onClose={() => setConvertQuery(null)} onSave={handleConvert} />}
    </div>
  )
}
