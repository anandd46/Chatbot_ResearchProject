import { useState } from 'react'
import { useEvalDatasets, useEvalRuns, useRunEvaluation } from '@/api/hooks'
import { FlaskConical, Play, Loader2, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import toast from 'react-hot-toast'

export default function EvaluationPage() {
  const { data: datasets } = useEvalDatasets()
  const { data: runs } = useEvalRuns()
  const runEval = useRunEvaluation()
  const [selectedDataset, setSelectedDataset] = useState('')
  const [mode, setMode] = useState<'baseline' | 'enhanced'>('enhanced')

  const handleRun = async () => {
    if (!selectedDataset) return toast.error('Select a dataset first')
    try {
      const result = await runEval.mutateAsync({ datasetId: selectedDataset, mode })
      toast.success(`Evaluation complete! Intent accuracy: ${((result.intent_accuracy || 0) * 100).toFixed(1)}%`)
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Evaluation failed')
    }
  }

  const delta = (v1?: number, v2?: number) => {
    if (v1 == null || v2 == null) return null
    return v1 - v2
  }

  const DeltaIcon = ({ val }: { val: number | null }) => {
    if (val == null) return null
    if (val > 0.01) return <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
    if (val < -0.01) return <TrendingDown className="w-3.5 h-3.5 text-red-400" />
    return <Minus className="w-3.5 h-3.5 text-slate-500" />
  }

  // Find latest baseline and enhanced runs for comparison
  const baselineRun = runs?.find((r: any) => r.mode === 'baseline')
  const enhancedRun = runs?.find((r: any) => r.mode === 'enhanced')

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-header">Evaluation Framework</h1>
        <p className="page-subtitle">Benchmark the NLP pipeline — compare baseline TF-IDF vs. enhanced multi-signal scoring</p>
      </div>

      {/* Run Controls */}
      <div className="glass-card p-5">
        <h2 className="font-semibold text-white mb-4">Run Evaluation</h2>
        <div className="flex items-center gap-4 flex-wrap">
          <select value={selectedDataset} onChange={(e) => setSelectedDataset(e.target.value)} className="input-field w-64" id="eval-dataset-select">
            <option value="">Select dataset...</option>
            {datasets?.map((d: any) => (
              <option key={d.id} value={d.id}>{d.name} ({d.case_count} cases)</option>
            ))}
          </select>
          <div className="flex items-center gap-2">
            {(['baseline', 'enhanced'] as const).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`px-4 py-2 rounded-xl border text-sm font-medium transition-colors ${mode === m ? 'bg-brand-600 border-brand-500 text-white' : 'bg-white/5 border-white/10 text-slate-400'}`}
              >
                {m === 'baseline' ? 'Baseline (TF-IDF only)' : 'Enhanced (Multi-signal)'}
              </button>
            ))}
          </div>
          <button
            onClick={handleRun}
            disabled={!selectedDataset || runEval.isPending}
            className="btn-primary"
            id="run-eval-btn"
          >
            {runEval.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Run Evaluation
          </button>
        </div>
      </div>

      {/* Comparison */}
      {baselineRun && enhancedRun && (
        <div className="glass-card p-5">
          <h2 className="font-semibold text-white mb-4">Latest Comparison: Baseline vs. Enhanced</h2>
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Intent Accuracy', base: baselineRun.intent_accuracy, enh: enhancedRun.intent_accuracy, format: (v: number) => `${(v * 100).toFixed(1)}%` },
              { label: 'Retrieval Success', base: baselineRun.retrieval_success_rate, enh: enhancedRun.retrieval_success_rate, format: (v: number) => `${(v * 100).toFixed(1)}%` },
              { label: 'Unknown Rate', base: baselineRun.unknown_rate, enh: enhancedRun.unknown_rate, format: (v: number) => `${(v * 100).toFixed(1)}%`, lowerBetter: true },
            ].map(({ label, base, enh, format, lowerBetter }) => {
              const d = delta(enh, base)
              const isGood = lowerBetter ? (d != null && d < 0) : (d != null && d > 0)
              return (
                <div key={label} className="p-4 bg-white/5 rounded-xl">
                  <div className="text-xs text-slate-500 mb-2">{label}</div>
                  <div className="flex items-end gap-4">
                    <div>
                      <div className="text-xs text-slate-500 mb-1">Baseline</div>
                      <div className="text-xl font-bold text-slate-300 font-mono">{base != null ? format(base) : '—'}</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 mb-1">Enhanced</div>
                      <div className="text-xl font-bold text-white font-mono">{enh != null ? format(enh) : '—'}</div>
                    </div>
                    <div className={`flex items-center gap-1 text-sm font-medium ${isGood ? 'text-emerald-400' : 'text-red-400'}`}>
                      <DeltaIcon val={d} />
                      {d != null ? `${d > 0 ? '+' : ''}${(d * 100).toFixed(1)}%` : ''}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Run History */}
      <div className="glass-card overflow-hidden">
        <div className="p-4 border-b border-white/5">
          <h2 className="font-semibold text-white">Evaluation Run History</h2>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Mode</th>
              <th>Intent Accuracy</th>
              <th>Retrieval Success</th>
              <th>Unknown Rate</th>
              <th>Avg Time</th>
              <th>Cases</th>
              <th>Run At</th>
            </tr>
          </thead>
          <tbody>
            {(runs || []).map((r: any) => (
              <tr key={r.id}>
                <td>
                  <span className={r.mode === 'enhanced' ? 'badge-green' : 'badge-gray'}>{r.mode}</span>
                </td>
                <td><span className="font-mono text-white">{r.intent_accuracy != null ? `${(r.intent_accuracy * 100).toFixed(1)}%` : '—'}</span></td>
                <td><span className="font-mono text-white">{r.retrieval_success_rate != null ? `${(r.retrieval_success_rate * 100).toFixed(1)}%` : '—'}</span></td>
                <td><span className="font-mono text-slate-300">{r.unknown_rate != null ? `${(r.unknown_rate * 100).toFixed(1)}%` : '—'}</span></td>
                <td><span className="font-mono text-slate-300">{r.avg_processing_time_ms != null ? `${r.avg_processing_time_ms.toFixed(0)}ms` : '—'}</span></td>
                <td>{r.total_cases}</td>
                <td className="text-slate-500 text-xs">{new Date(r.run_at).toLocaleString()}</td>
              </tr>
            ))}
            {!runs?.length && <tr><td colSpan={7} className="text-center py-12 text-slate-500">No evaluation runs yet — run an evaluation to see results</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
