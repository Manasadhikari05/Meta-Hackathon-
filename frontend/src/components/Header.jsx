import { Shield, LayoutDashboard } from 'lucide-react'

export default function Header({ onAnalyzeModels, onNavigate, onEnterApp }) {
  return (
    <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="w-6 h-6 text-gray-900" strokeWidth={1.5} />
          <span className="font-semibold text-gray-900 text-lg">ModGuard</span>
        </div>

        <nav className="hidden md:flex items-center gap-8 text-sm text-gray-500">
          <button onClick={() => onNavigate?.('features')} className="hover:text-gray-900 transition">Features</button>
          <button onClick={onAnalyzeModels} className="hover:text-gray-900 transition">Benchmarks</button>
        </nav>

        <div className="flex items-center gap-3">
          <button
            onClick={onAnalyzeModels}
            className="text-gray-600 border border-gray-200 text-sm px-4 py-2 rounded-lg hover:bg-gray-50 transition hidden md:block"
          >
            Analyze Models
          </button>
          {onEnterApp && (
            <button
              onClick={onEnterApp}
              className="flex items-center gap-1.5 bg-gray-900 text-white text-sm px-4 py-2 rounded-lg hover:bg-gray-700 transition"
            >
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </button>
          )}
        </div>
      </div>
    </header>
  )
}
