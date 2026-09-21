import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Bot, Eye, EyeOff, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { useLogin } from '@/api/hooks'
import { useAuthStore } from '@/store/auth'
import api from '@/api/client'

const schema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
})
type FormData = z.infer<typeof schema>

export default function LoginPage() {
  const [showPass, setShowPass] = useState(false)
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const loginMutation = useLogin()

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    try {
      const tokens = await loginMutation.mutateAsync(data)
      // Fetch user info
      const userResp = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${tokens.access_token}` },
      })
      login(userResp.data, tokens.access_token, tokens.refresh_token)
      toast.success(`Welcome back, ${userResp.data.name}!`)
      if (userResp.data.role === 'admin') navigate('/admin')
      else navigate('/chat')
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Login failed. Please check your credentials.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-hero-gradient px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-6">
            <div className="w-10 h-10 rounded-xl bg-brand-600 flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-white">GIT Smart Chatbot</span>
          </Link>
          <h1 className="text-2xl font-bold text-white">Welcome back</h1>
          <p className="text-slate-400 mt-1">Sign in to your account</p>
        </div>

        <div className="glass-card p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" id="login-form">
            <div>
              <label className="input-label">Email address</label>
              <input {...register('email')} id="login-email" type="email" className="input-field" placeholder="you@college.edu" />
              {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>}
            </div>
            <div>
              <label className="input-label">Password</label>
              <div className="relative">
                <input
                  {...register('password')}
                  id="login-password"
                  type={showPass ? 'text' : 'password'}
                  className="input-field pr-10"
                  placeholder="Your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 p-1"
                >
                  {showPass ? <EyeOff className="w-6 h-6" /> : <Eye className="w-6 h-6" />}
                </button>
              </div>
              {errors.password && <p className="text-red-400 text-xs mt-1">{errors.password.message}</p>}
            </div>
            <button
              id="login-submit"
              type="submit"
              disabled={loginMutation.isPending}
              className="btn-primary w-full h-[50px]"
            >
              {loginMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              {loginMutation.isPending ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-white/10 text-center">
            <p className="text-slate-400 text-sm">
              Don't have an account?{' '}
              <Link to="/register" className="text-brand-400 hover:text-brand-300 font-medium">
                Create one
              </Link>
            </p>
          </div>

          {/* Demo credentials hint */}
          <div className="mt-4 p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
            <p className="text-xs text-slate-400 text-center">
              Demo admin: <strong className="text-slate-300">admin@college.edu</strong> / <strong className="text-slate-300">Admin@1234</strong>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
