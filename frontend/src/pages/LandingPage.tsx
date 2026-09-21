import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Bot, Brain, Shield, Zap, BarChart2, BookOpen, Users, ArrowRight, Sparkles, CheckCircle } from 'lucide-react'
import { useAuthStore } from '@/store/auth'

const features = [
  { icon: Brain, title: 'NLP Intelligence', desc: 'TF-IDF + WordNet + Word Order Vector multi-signal scoring as per research paper.' },
  { icon: Zap, title: 'Instant Answers', desc: 'Sub-second response to questions on admissions, schedules, fees, events, and more.' },
  { icon: Shield, title: 'Secure & Private', desc: 'JWT authentication, RBAC, encrypted tokens, and rate-limited APIs.' },
  { icon: BarChart2, title: 'Admin Analytics', desc: 'Real-time dashboard with intent distribution, satisfaction metrics, and NLP inspector.' },
  { icon: BookOpen, title: 'Knowledge Manager', desc: 'Full CRUD with versioning, source traceability, and JSON/CSV import-export.' },
  { icon: Users, title: 'Multi-Role System', desc: 'Student, Faculty, and Admin roles with tailored access and features.' },
]

const categories = [
  '📋 Admissions & Enrollment', '📅 Academic Schedule', '🎓 Faculty & Staff',
  '💰 Fees & Scholarships', '🏆 Events & Activities', '📚 Library', '🏠 Hostel',
  '📝 Examinations', '🏫 Facilities', '📞 Contact Info',
]

export default function LandingPage() {
  const { isAuthenticated, user } = useAuthStore()

  return (
    <div className="min-h-screen bg-hero-gradient overflow-hidden">
      {/* Animated background orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl animate-pulse-soft" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent-500/10 rounded-full blur-3xl animate-pulse-soft" style={{ animationDelay: '1s' }} />
        <div className="absolute top-3/4 left-1/2 w-64 h-64 bg-brand-400/8 rounded-full blur-2xl animate-pulse-soft" style={{ animationDelay: '2s' }} />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-5 max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-600 flex items-center justify-center shadow-lg shadow-brand-600/30">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-bold text-white text-sm">GIT Smart Chatbot</div>
            <div className="text-xs text-slate-400">Greenfield Institute of Technology</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <>
              {user?.role === 'admin' && (
                <Link to="/admin" className="btn-secondary">Admin Dashboard</Link>
              )}
              <Link to="/chat" className="btn-primary">
                Open Chatbot <ArrowRight className="w-4 h-4" />
              </Link>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-secondary">Sign In</Link>
              <Link to="/register" className="btn-primary">Get Started</Link>
            </>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <main className="relative z-10 max-w-7xl mx-auto px-6 pt-20 pb-32 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-300 text-sm font-medium mb-8">
            <Sparkles className="w-4 h-4" />
            Research-Based AI — WordNet + TF-IDF + Word Order Vector
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold text-white mb-6 leading-tight tracking-tight">
            Your College's
            <br />
            <span className="text-gradient">AI Assistant</span>
          </h1>

          <p className="text-xl text-slate-400 max-w-3xl mx-auto mb-10 leading-relaxed">
            Ask anything about Greenfield Institute of Technology — admissions, schedules,
            fees, faculty, events, or facilities — and get instant, accurate answers powered
            by a multi-signal NLP retrieval pipeline.
          </p>

          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link to={isAuthenticated ? '/chat' : '/register'} className="btn-primary text-base px-8 py-3.5">
              <Bot className="w-5 h-5" />
              {isAuthenticated ? 'Open Chatbot' : 'Try It Free'}
            </Link>
            {!isAuthenticated && (
              <Link to="/login" className="btn-secondary text-base px-8 py-3.5">
                Sign In
              </Link>
            )}
          </div>
        </motion.div>

        {/* Chat Demo Preview */}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.3 }}
          className="mt-20 max-w-2xl mx-auto"
        >
          <div className="glass-card p-6 text-left shadow-2xl glow-brand">
            <div className="flex items-center gap-2 mb-4 pb-4 border-b border-white/10">
              <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <span className="font-semibold text-white text-sm">GIT Assistant</span>
              <div className="ml-auto flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs text-emerald-400">Online</span>
              </div>
            </div>
            {[
              { role: 'user', text: 'Who is the HOD of Computer Science?' },
              { role: 'bot', text: 'The Head of the Department (HOD) of Computer Science Engineering is Dr. Priya Sharma, PhD (IIT Delhi). Office: Room 201, CSE Block. Email: hod.cse@git.edu.in | Consultation hours: Mon–Fri, 10 AM–12 PM.' },
              { role: 'user', text: 'What are the admission requirements for BTech?' },
              { role: 'bot', text: 'For BTech admission, you need: 10+2 with Physics, Chemistry, Mathematics (min. 60% aggregate) + JEE Main score or state entrance examination result. Apply online at admissions.git.edu.in.' },
            ].map((msg, i) => (
              <div key={i} className={`mb-3 flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-bot'}>
                  {msg.text}
                </div>
              </div>
            ))}
            <div className="flex items-center gap-2 mt-4 pt-4 border-t border-white/10">
              <input className="input-field flex-1 py-2 text-sm" placeholder="Ask a question..." readOnly />
              <button className="btn-primary py-2">Send</button>
            </div>
          </div>
        </motion.div>
      </main>

      {/* Knowledge Categories */}
      <section className="relative z-10 bg-surface-900/50 py-20">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">I can answer questions about</h2>
          <p className="text-slate-400 mb-10">10 institutional knowledge categories covering the complete college experience</p>
          <div className="flex flex-wrap justify-center gap-3">
            {categories.map((cat) => (
              <span key={cat} className="px-4 py-2 rounded-full bg-white/5 border border-white/10 text-slate-300 text-sm font-medium hover:bg-white/10 transition-colors">
                {cat}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="relative z-10 py-20 max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-white mb-4">Built for Research & Production</h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            Implements the research paper's NLP methodology with additional engineering for security, analytics, evaluation, and admin tooling.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="glass-card-hover p-6"
            >
              <div className="w-12 h-12 rounded-xl bg-brand-600/20 border border-brand-500/20 flex items-center justify-center mb-4">
                <f.icon className="w-6 h-6 text-brand-400" />
              </div>
              <h3 className="font-semibold text-white mb-2">{f.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="relative z-10 py-20 text-center">
        <div className="max-w-2xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to get started?</h2>
          <p className="text-slate-400 mb-8">Create your account and start asking questions instantly.</p>
          <div className="flex items-center justify-center gap-4">
            <Link to="/register" className="btn-primary text-base px-8 py-3">
              Create Account <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to="/login" className="btn-secondary text-base px-8 py-3">Sign In</Link>
          </div>
          <div className="mt-6 flex items-center justify-center gap-6 text-sm text-slate-500">
            {['Free to use', 'No credit card', 'Instant access'].map((t) => (
              <div key={t} className="flex items-center gap-1.5">
                <CheckCircle className="w-4 h-4 text-emerald-500" />
                {t}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 py-8 text-center text-slate-500 text-sm">
        <p>© 2024 Greenfield Institute of Technology · Smart College AI Chatbot</p>
        <p className="mt-1">Research-based implementation of NLP-driven institutional information retrieval</p>
      </footer>
    </div>
  )
}
