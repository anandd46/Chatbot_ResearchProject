import { useState } from 'react'
import { useNlpInspect } from '@/api/hooks'
import { Search, Loader2, ChevronDown, ChevronUp } from 'lucide-react'

function ScoreBar({ value, label, color = '#3b6ef8' }: { value: number; label: string; color?: string }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className="text-slate-200 font-medium font-mono">{value.toFixed(4)}</span>
      </div>
      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${Math.min(value * 100, 100)}%`, background: color }} />
      </div>
    </div>
  )
}

export default function NlpInspectorPage() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<any>(null)
  const [expandCandidates, setExpandCandidates] = useState(false)
  const inspect = useNlpInspect()

  const handleInspect = async () => {
    if (!query.trim()) return
    const data = await inspect.mutateAsync(query.trim())
    setResult(data)
  }

  const posTagColor = (tag: string) => {
    if (tag.startsWith('N')) return 'badge-blue'
    if (tag.startsWith('V')) return 'badge-green'
    if (tag.startsWith('J')) return 'badge-yellow'
    if (tag.startsWith('R')) return 'badge-purple'
    return 'badge-gray'
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-header">NLP Inspector</h1>
        <p className="page-subtitle">Step-by-step pipeline trace for any query — for research and debugging</p>
      </div>

      {/* Input */}
      <div className="glass-card p-5">
        <div className="flex gap-3">
          <input
            id="nlp-inspector-input"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleInspect()}
            placeholder="Enter any query to inspect the NLP pipeline..."
            className="input-field flex-1"
          />
          <button
            id="nlp-inspect-btn"
            onClick={handleInspect}
            disabled={inspect.isPending || !query.trim()}
            className="btn-primary"
          >
            {inspect.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            Inspect
          </button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {['Who is the HOD of CSE?', 'What is the fee structure?', 'Tell me about the cricket match', 'When does semester begin?'].map((q) => (
            <button key={q} onClick={() => setQuery(q)} className="text-xs px-3 py-1 rounded-full bg-white/5 border border-white/10 text-slate-400 hover:text-slate-200 transition-colors">
              {q}
            </button>
          ))}
        </div>
      </div>

      {result && (
        <div className="space-y-4 animate-fade-in">
          {/* Step 1: Preprocessing */}
          <div className="glass-card p-5">
            <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-brand-600 text-white text-xs flex items-center justify-center font-bold">1</span>
              Preprocessing
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-xs text-slate-500 mb-1">Original Query</div>
                <div className="font-mono text-slate-200 bg-white/5 rounded-lg p-2">{result.original_query}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Normalized</div>
                <div className="font-mono text-slate-200 bg-white/5 rounded-lg p-2">{result.normalized_query}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Tokens ({result.tokens?.length})</div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {result.tokens?.map((t: string, i: number) => (
                    <span key={i} className="badge-gray font-mono">{t}</span>
                  ))}
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Filtered Tokens ({result.filtered_tokens?.length})</div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {result.filtered_tokens?.map((t: string, i: number) => (
                    <span key={i} className="badge-blue font-mono">{t}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Step 2: Lemmas + POS */}
          <div className="glass-card p-5">
            <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-brand-600 text-white text-xs flex items-center justify-center font-bold">2</span>
              Lemmatization & POS Tagging
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-slate-500 mb-2">Lemmas</div>
                <div className="flex flex-wrap gap-1">
                  {result.lemmas?.map((l: string, i: number) => (
                    <span key={i} className="badge-green font-mono">{l}</span>
                  ))}
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-2">POS Tags</div>
                <div className="flex flex-wrap gap-1">
                  {result.pos_tags?.map(([word, tag]: [string, string], i: number) => (
                    <div key={i} className="flex flex-col items-center">
                      <span className={`${posTagColor(tag)} font-mono text-xs`}>{word}</span>
                      <span className="text-xs text-slate-600">{tag}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Step 3: WordNet */}
          <div className="glass-card p-5">
            <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-brand-600 text-white text-xs flex items-center justify-center font-bold">3</span>
              WordNet Expansion
            </h2>
            <div className="flex flex-wrap gap-1">
              {result.wordnet_expanded?.map((w: string, i: number) => (
                <span key={i} className={`font-mono text-xs ${result.lemmas?.includes(w) ? 'badge-blue' : 'badge-purple'}`}>{w}</span>
              ))}
            </div>
            <p className="text-xs text-slate-500 mt-2">Blue = original lemmas · Purple = WordNet synonyms added</p>
          </div>

          {/* Step 4: Intent */}
          <div className="glass-card p-5">
            <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-brand-600 text-white text-xs flex items-center justify-center font-bold">4</span>
              Intent Classification
            </h2>
            <div className="flex items-center gap-4 flex-wrap">
              <div>
                <div className="text-xs text-slate-500 mb-1">Detected Intent</div>
                <span className="badge-blue text-sm capitalize font-semibold">{result.intent}</span>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Intent Score</div>
                <span className="text-white font-mono font-bold">{result.intent_score?.toFixed(4)}</span>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Method</div>
                <span className="badge-gray">{result.intent_method}</span>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Query Type</div>
                <span className={`badge ${result.query_type === 'ANSWERED' ? 'badge-green' : result.query_type === 'OUT_OF_DOMAIN' ? 'badge-gray' : 'badge-yellow'}`}>
                  {result.query_type}
                </span>
              </div>
            </div>
          </div>

          {/* Step 5: Score Fusion */}
          <div className="glass-card p-5">
            <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-brand-600 text-white text-xs flex items-center justify-center font-bold">5</span>
              Score Fusion Weights Used
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              {result.weights_used && Object.entries(result.weights_used).map(([k, v]: [string, any]) => (
                <div key={k} className="text-center p-3 bg-white/5 rounded-xl">
                  <div className="text-xl font-bold text-white font-mono">{v.toFixed(2)}</div>
                  <div className="text-xs text-slate-400 mt-1">{k.replace('_', ' ')}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Step 6: Top Candidates */}
          <div className="glass-card p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-white flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-brand-600 text-white text-xs flex items-center justify-center font-bold">6</span>
                Retrieved Candidates ({result.top_candidates?.length})
              </h2>
              <button onClick={() => setExpandCandidates(!expandCandidates)} className="btn-ghost text-xs">
                {expandCandidates ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                {expandCandidates ? 'Collapse' : 'Expand'}
              </button>
            </div>
            <div className="space-y-3">
              {result.top_candidates?.slice(0, expandCandidates ? 10 : 3).map((c: any) => (
                <div key={c.rank} className={`p-3 rounded-xl border ${c.rank === 1 ? 'border-brand-500/30 bg-brand-500/5' : 'border-white/5 bg-white/3'}`}>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`w-5 h-5 rounded-full text-xs flex items-center justify-center font-bold ${c.rank === 1 ? 'bg-brand-600 text-white' : 'bg-white/10 text-slate-400'}`}>{c.rank}</span>
                      <span className="text-sm text-slate-200 font-medium">{c.question}</span>
                    </div>
                    <span className="badge-blue flex-shrink-0">{c.category}</span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-2">
                    <ScoreBar value={c.tfidf_score} label="TF-IDF" color="#3b6ef8" />
                    <ScoreBar value={c.word_order_score} label="Word Order" color="#8b5cf6" />
                    <ScoreBar value={c.intent_score} label="Intent" color="#10b981" />
                    <ScoreBar value={c.final_score} label="Final Score" color="#f59e0b" />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Step 7: Selected */}
          <div className="glass-card p-5">
            <h2 className="font-semibold text-white mb-3 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-brand-600 text-white text-xs flex items-center justify-center font-bold">7</span>
              Selected KB Entry
            </h2>
            {result.selected_kb_id ? (
              <div className="flex items-center gap-3">
                <div className="badge-green">✓ Selected</div>
                <span className="text-slate-300 font-mono text-sm">{result.selected_kb_id}</span>
              </div>
            ) : (
              <div className="badge-yellow">No entry selected — below confidence threshold or out of domain</div>
            )}
            <div className="mt-2 text-xs text-slate-500">Processing time: {result.processing_time_ms}ms</div>
          </div>
        </div>
      )}
    </div>
  )
}
