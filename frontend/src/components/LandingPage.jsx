import { useState } from 'react';
import { Play, Heart, MessageCircle, Share2, CheckCircle, AlertTriangle, TrendingUp, Bookmark, MoreHorizontal, Shield, Eye, BarChart3, Zap, Activity, Users, Target, Trophy, Cpu, AlertCircle, Clock, CheckSquare, ArrowRight } from 'lucide-react';
import BenchmarkModal from './BenchmarkModal';
import Header from './Header';

// Minimal monochrome icon components
const IconActivity = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M22 12h-4l-3 9L9 3l-3 9H2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const IconBarChart = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M12 20V10M18 20V4M6 20v-4" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const IconZap = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const IconUsers = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const IconTrophy = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M6 9H4.5a2.5 2.5 0 010-5H6M6 9l3 3M6 9l-3 3M19 9h1.5a2.5 2.5 0 000-5H19M19 9l-3 3m3-3l3 3M2 21h20M2 21l3-3m-3 3l-3-3" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const LLMLogos = () => (
  <>
    {/* OpenAI */}
    <div className="flex items-center gap-3 opacity-70 hover:opacity-100 transition">
      <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none">
        <path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z" fill="currentColor"/>
      </svg>
    </div>

    {/* Google */}
    <div className="flex items-center gap-3 opacity-70 hover:opacity-100 transition">
      <svg className="w-10 h-10" viewBox="0 0 24 24">
        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
      </svg>
    </div>

    {/* Anthropic */}
    <div className="flex items-center gap-3 opacity-70 hover:opacity-100 transition">
      <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none">
        <path d="M12 2L2 22h4l6-12 6 12h4L12 2z" fill="#D4A574"/>
        <path d="M12 2L8 10h8L12 2z" fill="#C89968"/>
      </svg>
    </div>

    {/* Meta */}
    <div className="flex items-center gap-3 opacity-70 hover:opacity-100 transition">
      <svg className="w-10 h-10" viewBox="0 0 24 24" fill="url(#metaGradient)">
        <defs>
          <linearGradient id="metaGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#0081FB"/>
            <stop offset="100%" stopColor="#0064E0"/>
          </linearGradient>
        </defs>
        <path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm4.5 13.5c-1.5 2-3.5 3-6 3s-4.5-1-6-3c0 0 1.5 1.5 6 1.5s6-1.5 6-1.5zm-12-6c0-1.5 1-3 3-3s3 1.5 3 3-1 3-3 3-3-1.5-3-3zm9 0c0-1.5 1-3 3-3s3 1.5 3 3-1 3-3 3-3-1.5-3-3z"/>
      </svg>
    </div>

    {/* Mistral AI */}
    <div className="flex items-center gap-3 opacity-70 hover:opacity-100 transition">
      <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none">
        <rect x="4" y="4" width="4" height="4" fill="#F2A73B"/>
        <rect x="10" y="4" width="4" height="4" fill="#F2A73B"/>
        <rect x="16" y="4" width="4" height="4" fill="#F2A73B"/>
        <rect x="4" y="10" width="4" height="4" fill="#F2A73B"/>
        <rect x="10" y="10" width="4" height="4" fill="#F2A73B"/>
        <rect x="4" y="16" width="4" height="4" fill="#F2A73B"/>
      </svg>
    </div>

    {/* Cohere */}
    <div className="flex items-center gap-3 opacity-70 hover:opacity-100 transition">
      <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="10" fill="#39594D"/>
        <path d="M8 8h8v2H8zm0 3h8v2H8zm0 3h6v2H8z" fill="white"/>
      </svg>
    </div>

    {/* Stability AI */}
    <div className="flex items-center gap-3 opacity-70 hover:opacity-100 transition">
      <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none">
        <path d="M12 2L4 7v10l8 5 8-5V7l-8-5z" fill="#8B5CF6"/>
        <path d="M12 8l-4 2.5v5l4 2.5 4-2.5v-5L12 8z" fill="#A78BFA"/>
      </svg>
    </div>

    {/* Hugging Face */}
    <div className="flex items-center gap-3 opacity-70 hover:opacity-100 transition">
      <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="10" fill="#FFD21E"/>
        <circle cx="9" cy="10" r="1.5" fill="#000"/>
        <circle cx="15" cy="10" r="1.5" fill="#000"/>
        <path d="M8 14c0 2.5 1.5 4 4 4s4-1.5 4-4" stroke="#000" strokeWidth="1.5" fill="none"/>
      </svg>
    </div>
  </>
);

export default function LandingPage({ onEnterApp, onEnterDashboard, onEnterTraining }) {
  const [showBenchmarkModal, setShowBenchmarkModal] = useState(false);
  const [activeFeature, setActiveFeature] = useState(null);

  const featureDetails = {
    'Home Streamspage': {
      title: 'Live Moderation Feed',
      content: 'The Live Moderation Feed provides an Instagram-style scrolling interface where posts appear in real-time with AI-powered moderation decisions. Each post is automatically analyzed and marked as APPROVED, FLAGGED, or ESCALATED based on risk severity.\n\nKey features:\n• Real-time content analysis\n• AI-based risk severity detection\n• Human override controls',
      bullets: [
        'Real-time content analysis',
        'AI-based risk severity detection',
        'Human override controls'
      ]
    },
    'Technical Depth': {
      title: 'Model Comparison',
      content: 'The Model Comparison dashboard offers interactive visualizations comparing performance across multiple LLMs. View accuracy metrics, confusion matrices, precision-recall curves, and trust score leaderboards.\n\nKey features:\n• Accuracy vs difficulty graphs\n• Confusion matrix visualizations\n• Trust score rankings',
      bullets: [
        'Accuracy vs difficulty graphs',
        'Confusion matrix visualizations',
        'Trust score rankings'
      ]
    },
    'Advanced + Unique': {
      title: 'Attack Lab',
      content: 'The Attack Lab is an adversarial testing environment that generates challenging content in multiple languages, including Hinglish, sarcasm, and obfuscated text.\n\nKey features:\n• Multi-language content generation\n• Adversarial attack scoring\n• Robustness testing',
      bullets: [
        'Multi-language content generation',
        'Adversarial attack scoring',
        'Robustness testing'
      ]
    },
    'Meta-Style System': {
      title: 'Human-in-the-Loop System',
      content: 'Our Human-in-the-Loop system mirrors Meta\'s production moderation workflow. Content flagged by AI is routed to escalation queues where human reviewers make final decisions.\n\nKey features:\n• Escalation queue\n• Human vs AI decision comparison\n• Disagreement tracking',
      bullets: [
        'escalation queue',
        'human vs AI decision comparison',
        'disagreement tracking'
      ]
    },
    'Main Highlight': {
      title: 'Trust Score (Single Killer Metric)',
      content: 'The Trust Score is a comprehensive single metric combining accuracy, robustness, confidence, and bias.\n\nKey features:\n• Single comprehensive metric for model reliability\n• Combines accuracy, robustness, confidence, and bias\n• Ultimate benchmark for model performance',
      bullets: [
        'Single comprehensive metric for model reliability',
        'Combines accuracy, robustness, confidence, and bias',
        'Ultimate benchmark for model performance'
      ]
    }
  };

  const features = [
    {
      title: 'Live Moderation Feed',
      description: 'Instagram-style scrolling feed with real-time AI moderation and automated decisions.',
      icon: Activity,
      bullets: [
        'Real-time content analysis',
        'AI-based risk severity detection',
        'Human override controls'
      ],
      link: 'Home Streamspage'
    },
    {
      title: 'Model Comparison',
      description: 'Interactive graphs comparing accuracy across different LLMs with confusion matrices and trust scores.',
      icon: BarChart3,
      bullets: [
        'Accuracy vs difficulty graphs',
        'Confusion matrix visualizations',
        'Trust score rankings'
      ],
      link: 'Technical Depth'
    },
    {
      title: 'Attack Lab',
      description: 'Adversarial testing environment for stress-testing model robustness and exposing edge cases.',
      icon: Zap,
      bullets: [
        'Multi-language content generation',
        'Adversarial attack scoring',
        'Robustness testing'
      ],
      link: 'Advanced + Unique'
    },
    {
      title: 'Human-in-the-Loop System',
      description: 'Escalation queues for human review with AI vs human decision comparison tracking.',
      icon: Shield,
      bullets: [
        'escalation queue',
        'human vs AI decision comparison',
        'disagreement tracking'
      ],
      link: 'Meta-Style System'
    },
    {
      title: 'Trust Score (Single Killer Metric)',
      description: 'Single comprehensive metric combining accuracy, robustness, confidence, and bias.',
      icon: Trophy,
      bullets: [
        'Single comprehensive metric for model reliability',
        'Combines accuracy, robustness, confidence, and bias',
        'Ultimate benchmark for model performance'
      ],
      link: 'Main Highlight'
    }
  ];
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Header */}
      <Header
        onAnalyzeModels={() => setShowBenchmarkModal(true)}
        onNavigate={(dest) => {
          if (dest === 'features') window.scrollTo({ top: document.getElementById('features-section')?.offsetTop || 800, behavior: 'smooth' });
        }}
        onEnterApp={onEnterApp}
        onEnterDashboard={onEnterDashboard}
        onEnterTraining={onEnterTraining}
      />

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-6 py-32">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-6xl md:text-7xl font-normal font-serif leading-tight mb-8 text-gray-900">
            AI-Driven Content<br />Moderation Right Away
          </h1>
          <p className="text-lg md:text-xl text-gray-500 max-w-2xl mx-auto leading-relaxed mb-10">
            Protect your community with our state-of-the-art AI content moderation system. Explore the interactive OpenEnv RL dashboard or test the AI Moderator in real-time.
          </p>
          <div className="flex items-center justify-center gap-4 mb-6">
            <button
              onClick={onEnterDashboard}
              className="inline-flex items-center gap-2 bg-gray-900 text-white px-8 py-3.5 rounded-2xl text-sm font-semibold hover:bg-gray-700 transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              Launch Dashboard
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={onEnterApp}
              className="inline-flex items-center gap-2 border border-gray-300 text-gray-700 px-6 py-3.5 rounded-2xl text-sm font-semibold hover:border-gray-400 hover:bg-gray-50 transition-all duration-200"
            >
              Try AI Moderator
            </button>
            <button
              onClick={onEnterTraining}
              className="inline-flex items-center gap-2 border border-indigo-300 text-indigo-700 px-6 py-3.5 rounded-2xl text-sm font-semibold hover:border-indigo-400 hover:bg-indigo-50 transition-all duration-200"
            >
              TRL Training Demo
            </button>
          </div>
        </div>

          {/* Visual Showcase */}
          <div className="relative max-w-5xl mx-auto flex justify-center">
            {/* Mobile Mockup - Real Instagram Style */}
            <div className="relative inline-block">
              {/* iPhone Frame */}
              <div className="relative bg-gray-900 rounded-[3.5rem] p-3 shadow-2xl ring-1 ring-gray-800">
                {/* Notch with camera */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-7 bg-gray-900 rounded-b-3xl z-10 flex items-center justify-center">
                  <div className="w-2 h-2 bg-gray-700 rounded-full"></div>
                </div>

                <div className="bg-white rounded-[3rem] overflow-hidden w-[360px] h-[720px] relative">
                  {/* Status Bar */}
                  <div className="absolute top-0 left-0 right-0 h-12 bg-white/80 backdrop-blur-md z-20 flex items-center justify-between px-6 pt-2">
                    <div className="text-xs font-semibold text-gray-900">9:41</div>
                    <div className="flex items-center gap-1">
                      <svg className="w-4 h-4 text-gray-900" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M1 9l2 2c4.97-4.97 13.03-4.97 18 0l2-2C16.93 2.93 7.08 2.93 1 9zm8 8l3 3 3-3c-1.65-1.66-4.34-1.66-6 0zm-4-4l2 2c2.76-2.76 7.24-2.76 10 0l2-2C15.14 9.14 8.87 9.14 5 13z"/>
                      </svg>
                      <svg className="w-4 h-4 text-gray-900" viewBox="0 0 24 24" fill="currentColor">
                        <rect x="2" y="7" width="20" height="10" rx="2" fill="none" stroke="currentColor" strokeWidth="1.5"/>
                        <path d="M22 13v-1.5a1.5 1.5 0 00-1.5-1.5h-1"/>
                        <rect x="5" y="10" width="11" height="3" fill="currentColor"/>
                      </svg>
                    </div>
                  </div>

                   {/* Instagram Header */}
                   <div className="bg-white border-b border-gray-100 px-4 pt-14 pb-2 sticky top-0 z-10">
                     <div className="flex items-center justify-between mb-2">
                       {/* Instagram Logo - Left */}
                       <div className="flex-shrink-0">
                         <svg className="h-7" viewBox="0 0 120 36" fill="none">
                           <defs>
                             <linearGradient id="ig-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                               <stop offset="0%" stopColor="#833AB4"/>
                               <stop offset="50%" stopColor="#FD1D1D"/>
                               <stop offset="100%" stopColor="#F77737"/>
                             </linearGradient>
                           </defs>
                           <rect x="2" y="2" width="32" height="32" rx="8" fill="url(#ig-grad)"/>
                           <path d="M22 12c-2.2 0-4 1.8-4 4s1.8 4 4 4 4-1.8 4-4-1.8-4-4-4zm-8 7c0-2.2 1.8-4 4-4s4 1.8 4 4-1.8 4-4 4-4-1.8-4-4z" fill="white"/>
                           <circle cx="18" cy="18" r="4" fill="white"/>
                         </svg>
                       </div>
                      <div className="flex items-center gap-3">
                        <svg className="w-6 h-6 text-gray-800" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"/>
                        </svg>
                      </div>
                    </div>
                    {/* Stories row */}
                    <div className="flex gap-3 mt-3 overflow-x-auto py-1">
                      {[
                        { name: 'Your Story', color: 'from-purple-500 to-pink-500', added: true },
                        { name: 'sarah_j', color: 'from-yellow-400 to-orange-500', added: false },
                        { name: 'mike_dev', color: 'from-blue-400 to-blue-600', added: false },
                        { name: 'foodie_', color: 'from-green-400 to-emerald-600', added: false },
                        { name: 'travel', color: 'from-cyan-400 to-blue-500', added: false },
                        { name: 'tech_guru', color: 'from-violet-400 to-purple-600', added: false },
                      ].map((story, i) => (
                        <div key={i} className="flex flex-col items-center gap-1 min-w-fit">
                          <div className={`w-14 h-14 rounded-full p-[2px] ${story.added ? 'bg-gradient-to-br from-yellow-400 via-red-500 to-purple-600' : 'bg-gray-200'}`}>
                            <div className="w-full h-full rounded-full bg-white p-[2px]">
                              <div className={`w-full h-full rounded-full bg-gradient-to-br ${story.color} flex items-center justify-center text-white text-xs font-bold`}>
                                {story.name[0].toUpperCase()}
                              </div>
                            </div>
                          </div>
                          <span className="text-[10px] text-gray-700 truncate max-w-14">{story.name}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Posts Feed */}
                  <div className="overflow-y-auto h-full bg-white pb-20">
                       {/* Post 1 - Approved - Real photo style */}
                     <div className="border-b border-gray-100">
                       <div className="px-3 py-2.5 flex items-center justify-between">
                         <div className="flex items-center gap-2.5">
                           <div className="w-8 h-8 rounded-full bg-gradient-to-br from-pink-400 to-purple-600 p-[2px]">
                              <img
                                src="/avatar-1.svg"
                               alt="profile"
                               className="w-full h-full rounded-full object-cover border-2 border-white"
                             />
                           </div>
                          <div>
                            <div className="flex items-center gap-1">
                              <span className="font-semibold text-sm text-gray-900">sarah_journal</span>
                              <span className="text-gray-400 text-xs">•</span>
                              <span className="text-xs text-gray-500">2h</span>
                            </div>
                            <div className="text-xs text-gray-500">Brooklyn, NY</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="bg-green-100 text-green-700 px-2 py-0.5 rounded-md text-[10px] font-semibold flex items-center gap-1">
                            <CheckCircle className="w-3 h-3" strokeWidth={2.5} />
                            AI APPROVED
                          </div>
                          <MoreHorizontal className="w-5 h-5 text-gray-500" />
                        </div>
                      </div>
                       {/* Real image */}
                       <div className="relative aspect-square bg-gradient-to-br from-rose-100 via-orange-100 to-amber-100">
                         <img
                           src="/photo-1.svg"
                           alt="Mountain sunset"
                           className="w-full h-full object-cover"
                           onLoad={() => console.log('Image 1 loaded successfully')}
                           onError={(e) => console.log('Image 1 failed to load', e)}
                         />
                        <div className="absolute top-3 left-3 bg-black/50 backdrop-blur-sm px-2 py-1 rounded-lg flex items-center gap-1.5">
                          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                          <span className="text-white text-xs font-medium">Safe</span>
                        </div>
                      </div>
                      <div className="px-3 py-2.5">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-4">
                            <svg className="w-6 h-6 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/></svg>
                            <svg className="w-6 h-6 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
                            <svg className="w-6 h-6 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg>
                          </div>
                          <svg className="w-5 h-5 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/></svg>
                        </div>
                        <div className="text-sm font-semibold text-gray-900 mb-1">12,847 likes</div>
                        <div className="text-sm text-gray-900">
                          <span className="font-semibold">sarah_journal</span> Chasing sunsets in the mountains 🌄 #nature #travel #mountains
                        </div>
                        <div className="text-xs text-gray-500 mt-1">View all 342 comments</div>
                        <div className="text-xs text-gray-400 mt-0.5">2 HOURS AGO</div>
                      </div>
                    </div>

                      {/* Post 2 - Flagged - Real photo */}
                     <div className="border-b border-gray-100">
                       <div className="px-3 py-2.5 flex items-center justify-between">
                         <div className="flex items-center gap-2.5">
                           <div className="w-8 h-8 rounded-full bg-gradient-to-br from-red-400 to-orange-600 p-[2px]">
                             <img
                               src="/avatar-2.svg"
                               alt="profile"
                               className="w-full h-full rounded-full object-cover border-2 border-white"
                             />
                           </div>
                          <div>
                            <div className="flex items-center gap-1">
                              <span className="font-semibold text-sm text-gray-900">user_unknown</span>
                              <span className="text-gray-400 text-xs">•</span>
                              <span className="text-xs text-gray-500">5h</span>
                            </div>
                            <div className="text-xs text-gray-500">Los Angeles, CA</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="bg-red-100 text-red-700 px-2 py-0.5 rounded-md text-[10px] font-semibold flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3" strokeWidth={2.5} />
                            FLAGGED
                          </div>
                          <MoreHorizontal className="w-5 h-5 text-gray-500" />
                        </div>
                      </div>
                      <div className="relative aspect-square bg-gray-100">
                         <img
                           src="/photo-2.svg"
                           alt="Content"
                           className="w-full h-full object-cover blur-xl"
                         />
                        <div className="absolute inset-0 bg-black/40 backdrop-blur-md flex items-center justify-center">
                          <div className="bg-white/95 backdrop-blur-sm rounded-2xl p-6 shadow-2xl text-center mx-6 border border-red-200">
                            <div className="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-3">
                              <Shield className="w-7 h-7 text-red-600" strokeWidth={2.5} />
                            </div>
                            <div className="font-semibold text-sm mb-1 text-gray-900">Content Flagged</div>
                            <div className="text-xs text-gray-600 leading-relaxed">This post contains potentially harmful content and is pending review by our moderation team.</div>
                          </div>
                        </div>
                      </div>
                      <div className="px-3 py-2.5">
                        <div className="text-xs text-gray-400">5 HOURS AGO</div>
                      </div>
                    </div>

                      {/* Post 3 - Analyzing - Real photo */}
                     <div className="border-b border-gray-100">
                       <div className="px-3 py-2.5 flex items-center justify-between">
                         <div className="flex items-center gap-2.5">
                           <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-400 to-blue-600 p-[2px]">
                             <img
                               src="/avatar-1.svg"
                               alt="profile"
                               className="w-full h-full rounded-full object-cover border-2 border-white"
                             />
                           </div>
                          <div>
                            <div className="flex items-center gap-1">
                              <span className="font-semibold text-sm text-gray-900">wanderlust_</span>
                              <span className="text-gray-400 text-xs">•</span>
                              <span className="text-xs text-gray-500">1h</span>
                            </div>
                            <div className="text-xs text-gray-500">Bali, Indonesia</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded-md text-[10px] font-semibold flex items-center gap-1.5">
                            <div className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-pulse"></div>
                            ANALYZING
                          </div>
                          <MoreHorizontal className="w-5 h-5 text-gray-500" />
                        </div>
                      </div>
                      <div className="relative aspect-square bg-gray-100">
                         <img
                           src="/photo-1.svg"
                           alt="Beach"
                           className="w-full h-full object-cover"
                         />
                        <div className="absolute bottom-3 left-3 right-3">
                          <div className="bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-lg border border-blue-100">
                            <div className="flex items-center gap-2 mb-2">
                              <div className="w-6 h-6 bg-blue-100 rounded-lg flex items-center justify-center">
                                <Eye className="w-3.5 h-3.5 text-blue-600" />
                              </div>
                              <span className="text-xs font-semibold text-gray-900">AI Analysis</span>
                              <span className="ml-auto text-xs text-blue-600 font-medium">65%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-1.5">
                              <div className="bg-gradient-to-r from-blue-500 to-cyan-500 h-1.5 rounded-full" style={{width: '65%'}}></div>
                            </div>
                            <div className="flex justify-between mt-1.5 text-[10px] text-gray-500">
                              <span>Scanning...</span>
                              <span>Safety Check</span>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="px-3 py-2.5">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-4">
                            <svg className="w-6 h-6 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/></svg>
                            <svg className="w-6 h-6 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
                            <svg className="w-6 h-6 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg>
                          </div>
                          <svg className="w-5 h-5 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/></svg>
                        </div>
                        <div className="text-sm font-semibold text-gray-900 mb-1">3,291 likes</div>
                        <div className="text-sm text-gray-900">
                          <span className="font-semibold">wanderlust_</span> Found paradise 🏝️ #bali #travel #beach #vacation
                        </div>
                        <div className="text-xs text-gray-500 mt-1">View all 89 comments</div>
                        <div className="text-xs text-gray-400 mt-0.5">1 HOUR AGO</div>
                      </div>
                    </div>


                  </div>
                </div>
              </div>
            </div>
          </div>
        {/* Animated Partner Logos */}
        <div className="mt-32 overflow-hidden">
          <div className="text-center mb-10">
            <span className="text-sm text-gray-500 uppercase tracking-wider font-medium">Powered by Leading AI Models</span>
          </div>
          <div className="relative">
            <div className="absolute left-0 top-0 bottom-0 w-32 bg-gradient-to-r from-white to-transparent z-10"></div>
            <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-white to-transparent z-10"></div>

            <div className="flex animate-scroll-left">
              <div className="flex items-center gap-16 px-8 whitespace-nowrap">
                <LLMLogos />
              </div>
              <div className="flex items-center gap-16 px-8 whitespace-nowrap">
                <LLMLogos />
              </div>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-32 mb-20">
          <div className="mb-6">
            <h2 className="text-6xl font-bold mb-4 text-gray-900" style={{ fontFamily: 'Georgia, serif' }}>
              Advanced AI Moderation Platform
            </h2>
            <p className="text-gray-600 text-lg max-w-3xl">
              Comprehensive content moderation powered by cutting-edge AI technology, designed for modern platforms and communities.
            </p>
          </div>

           <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 mt-16">
             {/* All 5 features first */}
             {features.map((feature, index) => {
               const Icon = feature.icon;
               return (
                 <div key={index} className="text-left flex flex-col h-full">
                   {Icon && (
                     <div className="mb-4">
                       <Icon className="w-6 h-6" strokeWidth={1.5} />
                     </div>
                   )}

                   <h3 className={`font-semibold text-lg mb-3 ${feature.title === 'Trust Score (Single Killer Metric)' ? 'text-black' : ''}`}>{feature.title}</h3>

                   <p className={`text-sm mb-4 leading-relaxed ${feature.title === 'Trust Score (Single Killer Metric)' ? 'text-black' : 'text-gray-600'}`}>
                     {feature.description}
                   </p>

                   <div className="flex-grow"></div>

                   <button
                     onClick={() => setActiveFeature(feature.link)}
                     className="text-sm text-indigo-600 hover:underline mt-auto text-left flex items-center gap-1"
                   >
                     Learn More <ArrowRight className="w-3.5 h-3.5" />
                   </button>
                 </div>
               );
             })}
           </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {/* Company Info */}
            <div className="col-span-1 md:col-span-2">
              <h3 className="text-xl font-bold mb-4">AI Content Moderation</h3>
              <p className="text-gray-400 leading-relaxed max-w-md">
                Advanced AI-powered content moderation platform for modern communities.
                Protect your users with cutting-edge technology.
              </p>
            </div>
            
            {/* Quick Links */}
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400">
                <li><button onClick={() => window.scrollTo({top: 0, behavior: 'smooth'})} className="hover:text-white transition">Features</button></li>
                <li><button onClick={() => window.scrollTo({top: 0, behavior: 'smooth'})} className="hover:text-white transition">Pricing</button></li>
                <li><button onClick={() => window.scrollTo({top: 0, behavior: 'smooth'})} className="hover:text-white transition">API</button></li>
                <li><button onClick={() => window.scrollTo({top: 0, behavior: 'smooth'})} className="hover:text-white transition">Documentation</button></li>
              </ul>
            </div>
            
            {/* Company Links */}
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-gray-400">
                <li><button onClick={() => window.scrollTo({top: 0, behavior: 'smooth'})} className="hover:text-white transition">About</button></li>
                <li><button onClick={() => window.scrollTo({top: 0, behavior: 'smooth'})} className="hover:text-white transition">Blog</button></li>
                <li><button onClick={() => window.scrollTo({top: 0, behavior: 'smooth'})} className="hover:text-white transition">Careers</button></li>
                <li><button onClick={() => window.scrollTo({top: 0, behavior: 'smooth'})} className="hover:text-white transition">Contact</button></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-500 text-sm">
            <p>&copy; 2024 AI Content Moderation Platform. All rights reserved.</p>
          </div>
        </div>
      </footer>

      <style>{`
        @keyframes scroll-left {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-50%);
          }
        }

        @keyframes float {
          0%, 100% {
            transform: translateY(0px);
          }
          50% {
            transform: translateY(-20px);
          }
        }

        @keyframes float-delayed {
          0%, 100% {
            transform: translateY(0px);
          }
          50% {
            transform: translateY(-15px);
          }
        }

        .animate-scroll-left {
          animation: scroll-left 40s linear infinite;
        }

        .animate-scroll-left:hover {
          animation-play-state: paused;
        }

        .animate-float {
          animation: float 4s ease-in-out infinite;
        }

        .animate-float-delayed {
          animation: float-delayed 4s ease-in-out infinite 0.8s;
        }
      `}</style>
      
      {/* Benchmark Modal */}
      <BenchmarkModal
        isOpen={showBenchmarkModal}
        onClose={() => setShowBenchmarkModal(false)}
      />

     {/* Feature Detail Modal */}
     {activeFeature && featureDetails[activeFeature] && (
       <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-6" onClick={() => setActiveFeature(null)}>
         <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
           <div className="p-8">
             <div className="flex items-start justify-between mb-6">
               <h3 className="text-3xl font-bold text-gray-900">
                 {featureDetails[activeFeature].title}
               </h3>
               <button
                 onClick={() => setActiveFeature(null)}
                 className="text-gray-400 hover:text-gray-600 text-3xl leading-none"
               >
                 ×
               </button>
             </div>
             <div className="text-gray-600 text-lg leading-relaxed whitespace-pre-line mb-6">
               {featureDetails[activeFeature].content}
             </div>
             {featureDetails[activeFeature].bullets && (
               <div className="space-y-3">
                 {featureDetails[activeFeature].bullets.map((bullet, idx) => (
                   <div key={idx} className="flex items-start gap-3">
                     <span className="text-green-600 mt-0.5 text-lg">✓</span>
                     <span className="text-gray-700">{bullet}</span>
                   </div>
                 ))}
               </div>
             )}
           </div>
         </div>
       </div>
     )}
    </div>
  );
}