import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Bot, Eye, EyeOff, Loader2, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { useRegister } from '@/api/hooks'
import { useAuthStore } from '@/store/auth'
import api from '@/api/client'

const schema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Enter a valid email'),
  password: z
    .string()
    .min(8, 'Min 8 characters')
    .regex(/[A-Z]/, 'Must contain uppercase letter')
    .regex(/\d/, 'Must contain a digit')
    .regex(/[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'\/`~]/, 'Must contain a special character'),
  role: z.enum(['student', 'faculty']),
})
type FormData = z.infer<typeof schema>

const policyChecks = (password: string) => [
  { label: 'At least 8 characters', ok: password.length >= 8 },
  { label: 'Uppercase letter', ok: /[A-Z]/.test(password) },
  { label: 'Number', ok: /\d/.test(password) },
  { label: 'Special character', ok: /[!@#$%^&*]/.test(password) },
]

export default function RegisterPage() {
  const [showPass, setShowPass] = useState(false)
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const registerMutation = useRegister()
  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { role: 'student' },
  })

  const password = watch('password', '')

  const onSubmit = async (data: FormData) => {
    try {
      const tokens = await registerMutation.mutateAsync(data)
      const userResp = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${tokens.access_token}` },
      })
      login(userResp.data, tokens.access_token, tokens.refresh_token)
      toast.success('Account created! Welcome aboard!')
      navigate('/chat')
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Registration failed.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-hero-gradient px-4 py-8">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-6">
            <div className="w-10 h-10 rounded-xl bg-brand-600 flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-white">GIT Smart Chatbot</span>
          </Link>
          <h1 className="text-2xl font-bold text-white">Create your account</h1>
          <p className="text-slate-400 mt-1">Get instant access to the college AI assistant</p>
        </div>

        <div className="glass-card p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" id="register-form">
            <div>
              <label className="input-label">Full Name</label>
              <input {...register('name')} id="register-name" type="text" className="input-field" placeholder="Your full name" />
              {errors.name && <p className="text-red-400 text-xs mt-1">{errors.name.message}</p>}
            </div>
            <div>
              <label className="input-label">Email address</label>
              <input {...register('email')} id="register-email" type="email" className="input-field" placeholder="you@college.edu" />
              {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>}
            </div>
            <div>
              <label className="input-label">Role</label>
              <select {...register('role')} id="register-role" className="input-field">
                <option value="student">Student</option>
                <option value="faculty">Faculty</option>
              </select>
            </div>
            <div>
              <label className="input-label">Password</label>
              <div className="relative">
                <input
                  {...register('password')}
                  id="register-password"
                  type={showPass ? 'text' : 'password'}
                  className="input-field pr-10"
                  placeholder="Create a strong password"
                />
                <button type="button" onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {password && (
                <div className="mt-2 space-y-1">
                  {policyChecks(password).map(({ label, ok }) => (
                    <div key={label} className={`flex items-center gap-1.5 text-xs ${ok ? 'text-emerald-400' : 'text-slate-500'}`}>
                      <CheckCircle className={`w-3 h-3 ${ok ? 'text-emerald-400' : 'text-slate-600'}`} />
                      {label}
                    </div>
                  ))}
                </div>
              )}
              {errors.password && <p className="text-red-400 text-xs mt-1">{errors.password.message}</p>}
            </div>
            <button
              id="register-submit"
              type="submit"
              disabled={registerMutation.isPending}
              className="btn-primary w-full py-3"
            >
              {registerMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              {registerMutation.isPending ? 'Creating account...' : 'Create Account'}
            </button>
          </form>
          <div className="mt-6 pt-6 border-t border-white/10 text-center">
            <p className="text-slate-400 text-sm">
              Already have an account?{' '}
              <Link to="/login" className="text-brand-400 hover:text-brand-300 font-medium">Sign in</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
