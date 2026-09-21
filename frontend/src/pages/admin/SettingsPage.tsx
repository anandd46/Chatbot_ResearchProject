import { useNlpSettings, useUpdateNlpSettings } from '@/api/hooks'
import { useState, useEffect } from 'react'
import { Save, RotateCcw, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

function WeightSlider({ label, name, value, onChange, description }: any) {
  return (
    <div className="glass-card p-4">
      <div className="flex items-center justify-between mb-2">
        <div>
          <div className="font-medium text-white text-sm">{label}</div>
          <div className="text-xs text-slate-500">{description}</div>
        </div>
        <div className="w-16 h-8 bg-white/10 rounded-lg flex items-center justify-center">
          <span className="text-white font-mono text-sm font-bold">{value.toFixed(2)}</span>
        </div>
      </div>
      <input
        type="range"
        min="0"
        max="1"
        step="0.05"
        value={value}
        onChange={(e) => onChange(name, parseFloat(e.target.value))}
        className="w-full h-1.5 bg-white/10 rounded-full appearance-none cursor-pointer accent-brand-500"
        id={`slider-${name}`}
      />
    </div>
  )
}

export default function SettingsPage() {
  const { data: settings, isLoading } = useNlpSettings()
  const updateSettings = useUpdateNlpSettings()
  const [values, setValues] = useState<Record<string, number>>({})
  const [dirty, setDirty] = useState(false)

  useEffect(() => {
    if (settings) {
      setValues({
        alpha_tfidf: settings.alpha_tfidf,
        beta_word_order: settings.beta_word_order,
        gamma_intent: settings.gamma_intent,
        delta_keyword: settings.delta_keyword,
        confidence_threshold: settings.confidence_threshold,
        ood_threshold: settings.ood_threshold,
      })
    }
  }, [settings])

  const handleChange = (name: string, value: number) => {
    setValues((prev) => ({ ...prev, [name]: value }))
    setDirty(true)
  }

  const handleSave = async () => {
    try {
      await updateSettings.mutateAsync(values)
      toast.success('NLP settings updated')
      setDirty(false)
    } catch {
      toast.error('Failed to save settings')
    }
  }

  const handleReset = () => {
    if (settings) {
      setValues({
        alpha_tfidf: settings.alpha_tfidf,
        beta_word_order: settings.beta_word_order,
        gamma_intent: settings.gamma_intent,
        delta_keyword: settings.delta_keyword,
        confidence_threshold: settings.confidence_threshold,
        ood_threshold: settings.ood_threshold,
      })
      setDirty(false)
    }
  }

  const total = (values.alpha_tfidf || 0) + (values.beta_word_order || 0) + (values.gamma_intent || 0) + (values.delta_keyword || 0)

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-header">NLP Settings</h1>
          <p className="page-subtitle">Configure score fusion weights — affects all future chatbot responses</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleReset} disabled={!dirty} className="btn-secondary">
            <RotateCcw className="w-4 h-4" /> Reset
          </button>
          <button onClick={handleSave} disabled={!dirty || updateSettings.isPending} className="btn-primary" id="save-settings-btn">
            {updateSettings.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Save Settings
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-slate-500">Loading settings...</div>
      ) : (
        <div className="space-y-6">
          {/* Score Fusion Weights */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold text-white">Score Fusion Weights (α, β, γ, δ)</h2>
              <div className={`badge ${Math.abs(total - 1.0) < 0.01 ? 'badge-green' : 'badge-red'}`}>
                Total: {total.toFixed(2)} {Math.abs(total - 1.0) < 0.01 ? '✓' : '≠ 1.0'}
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <WeightSlider
                label="α — TF-IDF Score"
                name="alpha_tfidf"
                value={values.alpha_tfidf || 0}
                onChange={handleChange}
                description="TF-IDF cosine similarity with expanded query vector"
              />
              <WeightSlider
                label="β — Word Order Vector"
                name="beta_word_order"
                value={values.beta_word_order || 0}
                onChange={handleChange}
                description="Structural similarity via word position matching"
              />
              <WeightSlider
                label="γ — Intent Score"
                name="gamma_intent"
                value={values.gamma_intent || 0}
                onChange={handleChange}
                description="Intent match bonus when query intent matches KB category"
              />
              <WeightSlider
                label="δ — Keyword Overlap"
                name="delta_keyword"
                value={values.delta_keyword || 0}
                onChange={handleChange}
                description="Jaccard similarity between expanded tokens and KB keywords"
              />
            </div>
          </div>

          {/* Thresholds */}
          <div>
            <h2 className="font-semibold text-white mb-3">Detection Thresholds</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <WeightSlider
                label="Confidence Threshold"
                name="confidence_threshold"
                value={values.confidence_threshold || 0}
                onChange={handleChange}
                description="Min score to return an answer vs. marking as UNKNOWN_INSTITUTIONAL"
              />
              <WeightSlider
                label="Out-of-Domain Threshold"
                name="ood_threshold"
                value={values.ood_threshold || 0}
                onChange={handleChange}
                description="Score below this marks as OUT_OF_DOMAIN (non-institutional query)"
              />
            </div>
          </div>

          {/* Research Note */}
          <div className="glass-card p-4 border border-brand-500/20">
            <p className="text-xs text-slate-400">
              <strong className="text-brand-400">Research Paper Reference:</strong> The weight parameters α, β, γ, δ implement the score fusion formula from
              "AI Chatbot for Smart Communities" — S = α·TF-IDF + β·WOV + γ·Intent + δ·Keyword.
              Use the NLP Inspector to evaluate changes in real-time before saving.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
