import { useState, useEffect } from 'react'
import { X, TrendingUp, CheckCircle, AlertTriangle } from 'lucide-react'

const MODELS = [
  { name: 'GPT-4o', accuracy: 0.94, robustness: 0.91, confidence: 0.89, bias: 0.07 },
  { name: 'Gemini 1.5 Pro', accuracy: 0.92, robustness: 0.88, confidence: 0.87, bias: 0.09 },
  { name: 'Claude 3.5 Sonnet', accuracy: 0.93, robustness: 0.90, confidence: 0.91, bias: 0.06 },
  { name: 'Llama 3.3 70B', accuracy: 0.89, robustness: 0.85, confidence: 0.83, bias: 0.12 },
  { name: 'Mistral Large', accuracy: 0.88, robustness: 0.84, confidence: 0.82, bias: 0.11 },
]

function trustScore(m) {
  return ((m.accuracy * 0.4 + m.robustness * 0.3 + m.confidence * 0.2 + (1 - m.bias) * 0.1) * 100).toFixed(1)
}

export default function BenchmarkModal({ isOpen, onClose }) {
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (isOpen) {
      setLoading(true)
      const t = setTimeout(() => setLoading(false), 600)
      return () => clearTimeout(t)
    }
  }, [isOpen])

  if (!isOpen) return null

  const sorted = [...MODELS].sort((a, b) => parseFloat(trustScore(b)) - parseFloat(trustScore(a)))

  return (
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-6"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[85vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        <div className="p-8">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Model Benchmark</h2>
              <p className="text-gray-500 text-sm mt-1">Trust Score = accuracy × 0.4 + robustness × 0.3 + confidence × 0.2 + (1 − bias) × 0.1</p>
            </div>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-700 transition">
              <X className="w-6 h-6" />
            </button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="w-8 h-8 border-2 border-gray-900 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="space-y-4">
              {sorted.map((model, i) => {
                const score = parseFloat(trustScore(model))
                const isTop = i === 0
                return (
                  <div
                    key={model.name}
                    className={`rounded-xl p-5 border ${isTop ? 'border-gray-900 bg-gray-50' : 'border-gray-100'}`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-bold text-gray-400">#{i + 1}</span>
                        <span className="font-semibold text-gray-900">{model.name}</span>
                        {isTop && (
                          <span className="text-xs bg-gray-900 text-white px-2 py-0.5 rounded-full">Top</span>
                        )}
                      </div>
                      <span className="text-xl font-bold text-gray-900">{score}</span>
                    </div>
                    <div className="grid grid-cols-4 gap-3 text-xs text-gray-500">
                      {[
                        { label: 'Accuracy', value: model.accuracy },
                        { label: 'Robustness', value: model.robustness },
                        { label: 'Confidence', value: model.confidence },
                        { label: 'Bias', value: model.bias, invert: true },
                      ].map(({ label, value, invert }) => (
                        <div key={label}>
                          <div className="flex justify-between mb-1">
                            <span>{label}</span>
                            <span className="font-medium text-gray-700">{invert ? value.toFixed(2) : (value * 100).toFixed(0) + '%'}</span>
                          </div>
                          <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gray-900 rounded-full"
                              style={{ width: `${invert ? (1 - value) * 100 : value * 100}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
