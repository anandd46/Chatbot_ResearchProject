import { useUnresolvedQueries, useConvertToKb } from '@/api/hooks'
import { useState } from 'react'
import { Lightbulb, ArrowRight, Plus } from 'lucide-react'
import toast from 'react-hot-toast'

export default function ImprovementPage() {
  const { data: openQueries } = useUnresolvedQueries('OPEN', 1)
  const { data: inReview } = useUnresolvedQueries('IN_REVIEW', 1)
  const convertMutation = useConvertToKb()

  const totalActionable = (openQueries?.length || 0) + (inReview?.length || 0)

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-header">Knowledge Improvement Center</h1>
        <p className="page-subtitle">Transform unresolved queries into knowledge entries to continuously improve the chatbot</p>
      </div>

      {/* Workflow Diagram */}
      <div className="glass-card p-6">
        <h2 className="font-semibold text-white mb-4">Knowledge Improvement Workflow</h2>
        <div className="flex items-center gap-2 flex-wrap">
          {[
            { step: '1', label: 'Unknown Query', desc: 'User asks something the bot can\'t answer', color: 'badge-red' },
            { label: '→', color: '' },
            { step: '2', label: 'Unresolved Queue', desc: 'Auto-logged to admin dashboard', color: 'badge-yellow' },
            { label: '→', color: '' },
            { step: '3', label: 'Admin Review', desc: 'You review and assess the query', color: 'badge-blue' },
            { label: '→', color: '' },
            { step: '4', label: 'Create KB Entry', desc: '"Convert to Knowledge Entry"', color: 'badge-purple' },
            { label: '→', color: '' },
            { step: '5', label: 'Index Rebuild', desc: 'Auto-triggered after creation', color: 'badge-green' },
            { label: '→', color: '' },
            { step: '6', label: 'Future Retrieval', desc: 'Bot answers similar queries correctly', color: 'badge-green' },
          ].map((item, i) => (
            item.label === '→' ? (
              <ArrowRight key={i} className="w-5 h-5 text-slate-600 flex-shrink-0" />
            ) : (
              <div key={i} className="text-center">
                <div className={`badge ${item.color} mb-1`}>Step {item.step}</div>
                <div className="text-xs font-medium text-white">{item.label}</div>
                <div className="text-xs text-slate-500 max-w-[100px]">{item.desc}</div>
              </div>
            )
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="stat-card">
          <div className="text-3xl font-bold text-red-400">{openQueries?.length || 0}</div>
          <div className="text-sm text-slate-400">Open Queries</div>
        </div>
        <div className="stat-card">
          <div className="text-3xl font-bold text-amber-400">{inReview?.length || 0}</div>
          <div className="text-sm text-slate-400">In Review</div>
        </div>
        <div className="stat-card">
          <div className="text-3xl font-bold text-brand-400">{totalActionable}</div>
          <div className="text-sm text-slate-400">Actionable</div>
        </div>
        <div className="stat-card">
          <Lightbulb className="w-6 h-6 text-amber-400" />
          <div className="text-sm text-slate-300 font-medium">Each resolved query improves future responses</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="glass-card p-5">
        <h2 className="font-semibold text-white mb-4">Quick Actions</h2>
        <div className="space-y-3">
          {(openQueries || []).slice(0, 5).map((q: any) => (
            <div key={q.id} className="flex items-center gap-3 p-3 bg-white/3 rounded-xl">
              <div className="flex-1 min-w-0">
                <div className="text-sm text-slate-200 truncate">{q.query}</div>
                <div className="text-xs text-slate-500">{new Date(q.created_at).toLocaleDateString()}</div>
              </div>
              <a href="/admin/unresolved" className="btn-primary text-xs py-1.5 px-3">
                <Plus className="w-3 h-3" /> Convert
              </a>
            </div>
          ))}
          {!openQueries?.length && (
            <div className="text-center py-8 text-slate-500">
              <Lightbulb className="w-8 h-8 mx-auto mb-2 text-slate-600" />
              No open queries — great work!
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
