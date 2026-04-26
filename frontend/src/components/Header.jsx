import { Shield, LayoutDashboard, Radio, Image as ImageIcon } from 'lucide-react'

export default function Header({
  onAnalyzeModels,
  onNavigate,
  onEnterApp,
  onEnterDashboard,
  onEnterLiveDiscord,
  onEnterMemeMod,
}) {
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
          {onEnterDashboard && (
            <button
              onClick={onEnterDashboard}
              className="text-gray-600 border border-gray-200 text-sm px-4 py-2 rounded-lg hover:bg-gray-50 transition hidden md:block"
            >
              <LayoutDashboard className="w-4 h-4 inline-block mr-1 mb-0.5" />
              Dashboard
            </button>
          )}
          {onEnterLiveDiscord && (
            <button
              type="button"
              onClick={onEnterLiveDiscord}
              className="hidden md:inline-flex items-center gap-2 text-gray-800 border border-emerald-200 bg-emerald-50/80 text-sm px-4 py-2 rounded-lg hover:bg-emerald-100 transition"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <Radio className="w-4 h-4 text-emerald-700" />
              LIVE DISCORD
            </button>
          )}
          {onEnterMemeMod && (
            <button
              type="button"
              onClick={onEnterMemeMod}
              className="hidden md:inline-flex items-center gap-2 text-violet-900 border border-violet-200 bg-violet-50/80 text-sm px-4 py-2 rounded-lg hover:bg-violet-100 transition"
            >
              <ImageIcon className="w-4 h-4 text-violet-700" />
              JPEG/PNG MEMES
            </button>
          )}
          {onEnterApp && (
            <button
              onClick={onEnterApp}
              className="flex items-center gap-1.5 bg-gray-900 text-white text-sm px-4 py-2 rounded-lg hover:bg-gray-700 transition"
            >
              <Shield className="w-4 h-4" />
              AI Moderator
            </button>
          )}
        </div>
      </div>
    </header>
  )
}
