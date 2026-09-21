import { useState } from 'react'
import { useKnowledgeEntries, useCreateKnowledge, useUpdateKnowledge, useDeleteKnowledge, useReindex, useKnowledgeVersions } from '@/api/hooks'
import { Plus, Search, Trash2, Edit3, RefreshCw, History, Download, Upload, ExternalLink } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '@/api/client'

function EntryModal({ entry, onClose, onSave }: any) {
  const [form, setForm] = useState({
    category: entry?.category || '',
    question: entry?.question || '',
    answer: entry?.answer || '',
    keywords: (entry?.keywords || []).join(', '),
    source_title: entry?.source_title || '',
    source_url: entry?.source_url || '',
    source_type: entry?.source_type || '',
    reason: '',
  })
  const isEdit = !!entry?.id
  const categories = ['admissions', 'schedule', 'staff', 'fees', 'events', 'library', 'hostel', 'exam', 'facilities', 'contact', 'general']

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="glass-card w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto animate-fade-in">
        <h2 className="font-bold text-white text-lg mb-5">{isEdit ? 'Edit Knowledge Entry' : 'New Knowledge Entry'}</h2>
        <div className="space-y-4">
          <div>
            <label className="input-label">Category *</label>
            <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="input-field">
              <option value="">Select category</option>
              {categories.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="input-label">Question *</label>
            <input type="text" value={form.question} onChange={(e) => setForm({ ...form, question: e.target.value })} className="input-field" placeholder="What is...?" />
          </div>
          <div>
            <label className="input-label">Answer *</label>
            <textarea rows={4} value={form.answer} onChange={(e) => setForm({ ...form, answer: e.target.value })} className="input-field resize-none" placeholder="Answer text (supports Markdown)" />
          </div>
          <div>
            <label className="input-label">Keywords (comma-separated)</label>
            <input type="text" value={form.keywords} onChange={(e) => setForm({ ...form, keywords: e.target.value })} className="input-field" placeholder="admission, apply, enrollment" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="input-label">Source Title</label>
              <input type="text" value={form.source_title} onChange={(e) => setForm({ ...form, source_title: e.target.value })} className="input-field" />
            </div>
            <div>
              <label className="input-label">Source URL</label>
              <input type="url" value={form.source_url} onChange={(e) => setForm({ ...form, source_url: e.target.value })} className="input-field" />
            </div>
          </div>
          <div>
            <label className="input-label">Reason for change</label>
            <input type="text" value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} className="input-field" placeholder="e.g., Updated fee structure for 2024-25" />
          </div>
        </div>
        <div className="flex justify-end gap-3 mt-6">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button
            onClick={() => {
              const payload = {
                ...form,
                keywords: form.keywords.split(',').map((k: string) => k.trim()).filter(Boolean),
              }
              onSave(payload)
            }}
            className="btn-primary"
            id="kb-save-btn"
          >
            {isEdit ? 'Save Changes' : 'Create Entry'}
          </button>
        </div>
      </div>
    </div>
  )
}

function VersionHistory({ entryId, onClose }: { entryId: string; onClose: () => void }) {
  const { data: versions } = useKnowledgeVersions(entryId)
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="glass-card w-full max-w-2xl p-6 max-h-[80vh] overflow-y-auto animate-fade-in">
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-bold text-white">Version History</h2>
          <button onClick={onClose} className="btn-ghost">Close</button>
        </div>
        <div className="space-y-3">
          {versions?.map((v: any) => (
            <div key={v.id} className="glass-card p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="badge-blue">v{v.version}</span>
                <span className="text-xs text-slate-500">{new Date(v.created_at).toLocaleString()}</span>
                {v.reason && <span className="text-xs text-slate-400 italic">{v.reason}</span>}
              </div>
              <div className="text-sm text-slate-300 mb-1">{v.question}</div>
              <div className="text-xs text-slate-500 truncate">{v.answer.slice(0, 100)}...</div>
            </div>
          ))}
          {!versions?.length && <div className="text-center text-slate-500 py-8">No versions found</div>}
        </div>
      </div>
    </div>
  )
}

export default function KnowledgePage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [modalEntry, setModalEntry] = useState<any>(null)
  const [showVersions, setShowVersions] = useState<string | null>(null)

  const { data, isLoading } = useKnowledgeEntries(page, 20)
  const createMutation = useCreateKnowledge()
  const updateMutation = useUpdateKnowledge()
  const deleteMutation = useDeleteKnowledge()
  const reindexMutation = useReindex()

  const handleSave = async (form: any) => {
    try {
      if (modalEntry?.id) {
        await updateMutation.mutateAsync({ id: modalEntry.id, data: form })
        toast.success('Entry updated and index rebuilt')
      } else {
        await createMutation.mutateAsync(form)
        toast.success('Entry created and index rebuilt')
      }
      setModalEntry(null)
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to save entry')
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Soft-delete this entry? It will be removed from the search index.')) return
    try {
      await deleteMutation.mutateAsync(id)
      toast.success('Entry deleted')
    } catch {
      toast.error('Failed to delete')
    }
  }

  const handleReindex = async () => {
    const result = await reindexMutation.mutateAsync()
    toast.success(`Index rebuilt with ${result.count} entries`)
  }

  const handleExport = async (format: 'json' | 'csv') => {
    const resp = await api.get(`/knowledge/export/${format}`, { responseType: 'blob' })
    const url = URL.createObjectURL(resp.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `knowledge_export.${format}`
    a.click()
    URL.revokeObjectURL(url)
    toast.success(`Exported as ${format.toUpperCase()}`)
  }

  const entries = data?.items || []
  const total = data?.total || 0

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-header">Knowledge Base</h1>
          <p className="page-subtitle">{total} active entries in the NLP retrieval index</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => handleExport('csv')} className="btn-ghost" id="export-csv-btn"><Download className="w-4 h-4" /> CSV</button>
          <button onClick={() => handleExport('json')} className="btn-ghost" id="export-json-btn"><Download className="w-4 h-4" /> JSON</button>
          <button onClick={handleReindex} disabled={reindexMutation.isPending} className="btn-secondary" id="reindex-btn">
            <RefreshCw className={`w-4 h-4 ${reindexMutation.isPending ? 'animate-spin' : ''}`} /> Reindex
          </button>
          <button onClick={() => setModalEntry({})} className="btn-primary" id="new-kb-btn">
            <Plus className="w-4 h-4" /> New Entry
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input
          type="text"
          placeholder="Search entries by question or category..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-field pl-9"
          id="kb-search"
        />
      </div>

      {/* Table */}
      <div className="glass-card overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-slate-500">Loading knowledge base...</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Question</th>
                <th>Category</th>
                <th>Keywords</th>
                <th>Source</th>
                <th>Version</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {entries
                .filter((e: any) => !search || e.question.toLowerCase().includes(search.toLowerCase()) || e.category.includes(search.toLowerCase()))
                .map((e: any) => (
                  <tr key={e.id}>
                    <td className="max-w-xs">
                      <div className="truncate text-slate-200 font-medium">{e.question}</div>
                      <div className="truncate text-slate-500 text-xs mt-0.5">{e.answer.slice(0, 60)}...</div>
                    </td>
                    <td><span className="badge-blue capitalize">{e.category}</span></td>
                    <td>
                      <div className="flex flex-wrap gap-1 max-w-[120px]">
                        {e.keywords?.slice(0, 3).map((k: string) => (
                          <span key={k} className="badge-gray text-xs">{k}</span>
                        ))}
                        {e.keywords?.length > 3 && <span className="text-slate-500 text-xs">+{e.keywords.length - 3}</span>}
                      </div>
                    </td>
                    <td>
                      {e.source_url ? (
                        <a href={e.source_url} target="_blank" rel="noopener noreferrer" className="text-brand-400 hover:text-brand-300 text-xs flex items-center gap-1">
                          <ExternalLink className="w-3 h-3" /> {e.source_title || 'Source'}
                        </a>
                      ) : <span className="text-slate-600 text-xs">—</span>}
                    </td>
                    <td><span className="badge-purple">v{e.version_count}</span></td>
                    <td>
                      <div className="flex items-center gap-1">
                        <button onClick={() => setShowVersions(e.id)} className="btn-ghost p-1.5" title="Version history"><History className="w-3.5 h-3.5" /></button>
                        <button onClick={() => setModalEntry(e)} className="btn-ghost p-1.5" title="Edit"><Edit3 className="w-3.5 h-3.5" /></button>
                        <button onClick={() => handleDelete(e.id)} className="btn-ghost p-1.5 text-red-400 hover:text-red-300" title="Delete"><Trash2 className="w-3.5 h-3.5" /></button>
                      </div>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        )}

        {/* Pagination */}
        <div className="px-4 py-3 border-t border-white/5 flex items-center justify-between text-sm text-slate-400">
          <span>Showing {(page - 1) * 20 + 1}–{Math.min(page * 20, total)} of {total}</span>
          <div className="flex gap-2">
            <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="btn-secondary py-1 px-3 disabled:opacity-40">Prev</button>
            <button disabled={page * 20 >= total} onClick={() => setPage(page + 1)} className="btn-secondary py-1 px-3 disabled:opacity-40">Next</button>
          </div>
        </div>
      </div>

      {modalEntry && (
        <EntryModal entry={modalEntry?.id ? modalEntry : null} onClose={() => setModalEntry(null)} onSave={handleSave} />
      )}
      {showVersions && (
        <VersionHistory entryId={showVersions} onClose={() => setShowVersions(null)} />
      )}
    </div>
  )
}
