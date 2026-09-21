import { useOverviewStats, useIntentDistribution, useDailyStats, useFeedbackStats } from '@/api/hooks'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, CartesianGrid } from 'recharts'
import { MessageSquare, BookOpen, AlertCircle, Users, Star, Database, TrendingUp, CheckCircle } from 'lucide-react'

const COLORS = ['#3b6ef8', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899']

function StatCard({ icon: Icon, label, value, color = 'brand', sub }: any) {
  const colorMap: Record<string, string> = {
    brand: 'bg-brand-500/10 text-brand-400 border-brand-500/20',
    green: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    yellow: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    red: 'bg-red-500/10 text-red-400 border-red-500/20',
    purple: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  }
  return (
    <div className="stat-card">
      <div className={`w-10 h-10 rounded-xl border flex items-center justify-center ${colorMap[color]}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <div className="text-2xl font-bold text-white">{value ?? '—'}</div>
        <div className="text-sm text-slate-400">{label}</div>
        {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { data: overview, isLoading: overviewLoading } = useOverviewStats()
  const { data: intents } = useIntentDistribution()
  const { data: daily } = useDailyStats(14)
  const { data: feedback } = useFeedbackStats()

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="page-header">Research Dashboard</h1>
        <p className="page-subtitle">Real-time metrics and analytics for the Smart College AI Chatbot</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard icon={Users} label="Total Users" value={overview?.total_users} />
        <StatCard icon={MessageSquare} label="Conversations" value={overview?.total_conversations} />
        <StatCard icon={TrendingUp} label="Messages" value={overview?.total_messages} />
        <StatCard icon={BookOpen} label="KB Entries" value={overview?.total_kb_entries} color="green" />
        <StatCard icon={AlertCircle} label="Open Unresolved" value={overview?.unresolved_open} color="yellow" />
        <StatCard icon={Star} label="Avg Satisfaction" value={overview?.avg_satisfaction ? `${overview.avg_satisfaction}/5` : 'N/A'} color="purple" />
      </div>

      {/* Index Status */}
      <div className="glass-card p-4 flex items-center gap-3">
        <Database className="w-5 h-5 text-brand-400" />
        <span className="text-sm text-slate-300">NLP Index:</span>
        <span className={`badge ${overview?.index_ready ? 'badge-green' : 'badge-red'}`}>
          {overview?.index_ready ? `Ready — ${overview?.index_size} entries` : 'Not Ready'}
        </span>
        {overview?.avg_satisfaction && (
          <div className="ml-auto flex items-center gap-1.5">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            <span className="text-sm text-slate-400">System operational</span>
          </div>
        )}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Volume */}
        <div className="glass-card p-5">
          <h2 className="font-semibold text-white mb-4">Daily Query Volume (14 days)</h2>
          {daily && daily.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={daily}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} tickFormatter={(v) => v.slice(5)} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
                <Line type="monotone" dataKey="total" stroke="#3b6ef8" strokeWidth={2} dot={false} name="Total" />
                <Line type="monotone" dataKey="answered" stroke="#10b981" strokeWidth={2} dot={false} name="Answered" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[200px] flex items-center justify-center text-slate-500 text-sm">
              No data yet — wait for queries to accumulate
            </div>
          )}
        </div>

        {/* Intent Distribution */}
        <div className="glass-card p-5">
          <h2 className="font-semibold text-white mb-4">Intent Distribution</h2>
          {intents && intents.length > 0 ? (
            <div className="flex items-center gap-4">
              <PieChart width={160} height={160}>
                <Pie data={intents} cx={75} cy={75} innerRadius={45} outerRadius={75} dataKey="count">
                  {intents.map((_: any, i: number) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: any, n: any, p: any) => [v, p?.payload?.intent]} contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
              </PieChart>
              <div className="flex-1 space-y-1.5">
                {intents.slice(0, 7).map((item: any, i: number) => (
                  <div key={item.intent} className="flex items-center gap-2 text-xs">
                    <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: COLORS[i % COLORS.length] }} />
                    <span className="text-slate-400 capitalize truncate flex-1">{item.intent}</span>
                    <span className="text-slate-300 font-medium">{item.percentage}%</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-40 flex items-center justify-center text-slate-500 text-sm">
              No data yet — start a conversation to see intent distribution
            </div>
          )}
        </div>
      </div>

      {/* Feedback Stats */}
      {feedback && (
        <div className="glass-card p-5">
          <h2 className="font-semibold text-white mb-4">Feedback Summary</h2>
          <div className="flex items-center gap-8">
            <div className="text-center">
              <div className="text-4xl font-bold text-white">{feedback.avg_rating?.toFixed(1) || '—'}</div>
              <div className="text-amber-400 text-lg">{'★'.repeat(Math.round(feedback.avg_rating || 0))}</div>
              <div className="text-xs text-slate-500">{feedback.total_feedback} ratings</div>
            </div>
            <div className="flex-1 max-w-sm space-y-2">
              {[5, 4, 3, 2, 1].map((star) => {
                const count = feedback.rating_distribution?.[star] || 0
                const total = feedback.total_feedback || 1
                const pct = Math.round((count / total) * 100)
                return (
                  <div key={star} className="flex items-center gap-2 text-xs">
                    <span className="text-slate-400 w-4">{star}★</span>
                    <div className="flex-1 bg-white/5 rounded-full h-1.5">
                      <div className="score-bar-fill h-1.5" style={{ width: `${pct}%` }} />
                    </div>
                    <span className="text-slate-500 w-6">{count}</span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
