import { useIntentDistribution, useDailyStats, useFeedbackStats } from '@/api/hooks'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid, AreaChart, Area } from 'recharts'
import { useState } from 'react'

export default function AnalyticsPage() {
  const [days, setDays] = useState(30)
  const { data: intents } = useIntentDistribution()
  const { data: daily } = useDailyStats(days)
  const { data: feedback } = useFeedbackStats()

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-header">Analytics</h1>
          <p className="page-subtitle">Conversation trends, intent patterns, and user satisfaction</p>
        </div>
        <select value={days} onChange={(e) => setDays(Number(e.target.value))} className="input-field w-40">
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Daily Volume */}
      <div className="glass-card p-5">
        <h2 className="font-semibold text-white mb-4">Daily Query Volume</h2>
        <ResponsiveContainer width="100%" height={240}>
          <AreaChart data={daily || []}>
            <defs>
              <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b6ef8" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b6ef8" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorAnswered" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} tickFormatter={(v) => v.slice(5)} />
            <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
            <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
            <Area type="monotone" dataKey="total" stroke="#3b6ef8" fill="url(#colorTotal)" name="Total Queries" strokeWidth={2} />
            <Area type="monotone" dataKey="answered" stroke="#10b981" fill="url(#colorAnswered)" name="Answered" strokeWidth={2} />
            <Area type="monotone" dataKey="unresolved" stroke="#f59e0b" fill="none" name="Unresolved" strokeWidth={1.5} strokeDasharray="4 2" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Intent Distribution Bar */}
        <div className="glass-card p-5">
          <h2 className="font-semibold text-white mb-4">Intent Distribution</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={intents || []} layout="vertical">
              <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} />
              <YAxis type="category" dataKey="intent" tick={{ fill: '#94a3b8', fontSize: 11 }} width={80} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} formatter={(v, n, p) => [`${v} (${p?.payload?.percentage}%)`, 'Count']} />
              <Bar dataKey="count" fill="#3b6ef8" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Feedback */}
        <div className="glass-card p-5">
          <h2 className="font-semibold text-white mb-4">User Satisfaction</h2>
          {feedback ? (
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="text-5xl font-bold text-white">{feedback.avg_rating?.toFixed(1) || '—'}</div>
                <div>
                  <div className="text-amber-400 text-xl">{'★'.repeat(Math.round(feedback.avg_rating || 0))}{'☆'.repeat(5 - Math.round(feedback.avg_rating || 0))}</div>
                  <div className="text-sm text-slate-400">{feedback.total_feedback} total ratings</div>
                </div>
              </div>
              <div className="space-y-2">
                {[5, 4, 3, 2, 1].map((star) => {
                  const count = feedback.rating_distribution?.[star] || 0
                  const total = feedback.total_feedback || 1
                  return (
                    <div key={star} className="flex items-center gap-3 text-sm">
                      <span className="text-slate-400 w-8">{star}★</span>
                      <div className="flex-1 bg-white/5 rounded-full h-2">
                        <div className="h-2 bg-gradient-to-r from-brand-500 to-accent-500 rounded-full transition-all duration-700" style={{ width: `${Math.round(count / total * 100)}%` }} />
                      </div>
                      <span className="text-slate-500 w-8 text-right">{count}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          ) : <div className="h-40 flex items-center justify-center text-slate-500">No feedback data yet</div>}
        </div>
      </div>
    </div>
  )
}
