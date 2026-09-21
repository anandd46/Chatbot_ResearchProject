import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { Bot, LayoutDashboard, BookOpen, AlertCircle, MessageSquare, BarChart2, Search, FlaskConical, ThumbsUp, Users, Settings, Lightbulb, Activity, LogOut } from 'lucide-react'
import { useAuthStore } from '@/store/auth'
import api from '@/api/client'
import toast from 'react-hot-toast'

const navGroups = [
  {
    label: 'Overview',
    items: [
      { to: '/admin', label: 'Dashboard', icon: LayoutDashboard, end: true },
      { to: '/admin/analytics', label: 'Analytics', icon: BarChart2 },
      { to: '/admin/improvement', label: 'Improvement Center', icon: Lightbulb },
    ]
  },
  {
    label: 'Management',
    items: [
      { to: '/admin/knowledge', label: 'Knowledge Base', icon: BookOpen },
      { to: '/admin/unresolved', label: 'Unresolved Queries', icon: AlertCircle },
      { to: '/admin/conversations', label: 'Conversations', icon: MessageSquare },
      { to: '/admin/feedback', label: 'Feedback', icon: ThumbsUp },
    ]
  },
  {
    label: 'System',
    items: [
      { to: '/admin/nlp-inspector', label: 'NLP Inspector', icon: Search },
      { to: '/admin/evaluation', label: 'Evaluation', icon: FlaskConical },
      { to: '/admin/users', label: 'Users', icon: Users },
      { to: '/admin/status', label: 'System Status', icon: Activity },
      { to: '/admin/settings', label: 'Settings', icon: Settings },
    ]
  }
]

export default function AdminLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    const { refreshToken } = useAuthStore.getState()
    if (refreshToken) {
      try { await api.post('/auth/logout', { refresh_token: refreshToken }) } catch {}
    }
    logout()
    navigate('/login')
    toast.success('Logged out')
  }

  return (
    <div className="h-screen flex bg-surface-950">
      {/* Sidebar */}
      <aside className="w-64 border-r border-white/5 flex flex-col bg-surface-900/60 overflow-y-auto">
        {/* Logo */}
        <div className="p-4 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-brand-600 flex items-center justify-center shadow-lg shadow-brand-600/30">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-bold text-white text-sm">GIT Admin</div>
              <div className="text-xs text-slate-500">Research Dashboard</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-4">
          {navGroups.map((group) => (
            <div key={group.label}>
              <div className="px-3 mb-1 text-[10px] font-bold text-slate-500 uppercase tracking-wider">{group.label}</div>
              <div className="space-y-0.5">
                {group.items.map(({ to, label, icon: Icon, end }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={end}
                    className={({ isActive }) =>
                      `sidebar-link ${isActive ? 'active' : ''}`
                    }
                  >
                    <Icon className="w-4 h-4 flex-shrink-0" />
                    <span className="truncate">{label}</span>
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* User */}
        <div className="p-3 border-t border-white/5">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-full bg-brand-600/20 border border-brand-500/30 flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-bold text-brand-400">{user?.name[0]?.toUpperCase()}</span>
            </div>
            <div className="min-w-0">
              <div className="text-xs font-medium text-slate-200 truncate">{user?.name}</div>
              <div className="text-xs text-slate-500">Administrator</div>
            </div>
          </div>
          <NavLink to="/chat" className="sidebar-link text-xs mb-1">
            <Bot className="w-3.5 h-3.5" /> Open Chatbot
          </NavLink>
          <button onClick={handleLogout} className="sidebar-link text-xs w-full text-left" id="admin-logout-btn">
            <LogOut className="w-3.5 h-3.5" /> Logout
          </button>
        </div>
      </aside>

      {/* Content */}
      <main className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}
