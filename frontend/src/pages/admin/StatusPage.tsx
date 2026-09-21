import { useSystemStatus } from '@/api/hooks'
import { CheckCircle, AlertTriangle, XCircle, RefreshCw, Database, Brain } from 'lucide-react'

export default function StatusPage() {
  const { data: status, refetch, isFetching } = useSystemStatus()

  const StatusIcon = ({ s }: { s: string }) => {
    if (s === 'ok' || s === 'ready') return <CheckCircle className="w-5 h-5 text-emerald-400" />
    if (s === 'error') return <XCircle className="w-5 h-5 text-red-400" />
    return <AlertTriangle className="w-5 h-5 text-amber-400" />
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-header">System Status</h1>
          <p className="page-subtitle">Health checks for all system components</p>
        </div>
        <button onClick={() => refetch()} className="btn-secondary" id="refresh-status-btn">
          <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {status && (
        <div className="space-y-4">
          {/* Overall Status */}
          <div className={`glass-card p-5 border ${status.status === 'ok' ? 'border-emerald-500/20' : 'border-amber-500/20'}`}>
            <div className="flex items-center gap-3">
              <StatusIcon s={status.status} />
              <div>
                <div className="font-semibold text-white">Overall System Status</div>
                <div className={`text-sm capitalize ${status.status === 'ok' ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {status.status}
                </div>
              </div>
              <div className="ml-auto text-xs text-slate-500">v{status.version}</div>
            </div>
          </div>

          {/* Component Checks */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="glass-card p-5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center">
                  <Database className="w-5 h-5 text-brand-400" />
                </div>
                <div>
                  <div className="font-medium text-white">PostgreSQL Database</div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <StatusIcon s={status.database} />
                    <span className={`text-sm capitalize ${status.database === 'ok' ? 'text-emerald-400' : 'text-red-400'}`}>{status.database}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="glass-card p-5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center">
                  <Brain className="w-5 h-5 text-brand-400" />
                </div>
                <div>
                  <div className="font-medium text-white">NLP TF-IDF Index</div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <StatusIcon s={status.nlp_index} />
                    <span className={`text-sm ${status.nlp_index === 'ready' ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {status.nlp_index} — {status.index_size} entries
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* API Endpoints */}
          <div className="glass-card p-5">
            <h2 className="font-semibold text-white mb-4">Key API Endpoints</h2>
            <div className="space-y-2">
              {[
                { path: 'GET /health/live', desc: 'Liveness probe' },
                { path: 'GET /health/ready', desc: 'Readiness probe (DB + NLP)' },
                { path: 'GET /api/docs', desc: 'Interactive API documentation (Swagger UI)' },
                { path: 'GET /api/v1', desc: 'API info endpoint' },
              ].map(({ path, desc }) => (
                <div key={path} className="flex items-center gap-3 text-sm p-2 bg-white/3 rounded-lg">
                  <span className="font-mono text-brand-300 flex-shrink-0">{path}</span>
                  <span className="text-slate-500">{desc}</span>
                  <span className="ml-auto badge-green">online</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
