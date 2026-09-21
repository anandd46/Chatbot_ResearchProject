import { useAdminUsers } from '@/api/hooks'
import { useState } from 'react'
import { Shield, GraduationCap, Book, UserCheck, UserX } from 'lucide-react'
import api from '@/api/client'
import toast from 'react-hot-toast'

const roleIcon: Record<string, any> = { admin: Shield, faculty: Book, student: GraduationCap }
const roleBadge: Record<string, string> = { admin: 'badge-red', faculty: 'badge-yellow', student: 'badge-blue' }

export default function UsersPage() {
  const [page, setPage] = useState(1)
  const { data: users, isLoading, refetch } = useAdminUsers(page)

  const toggleActive = async (userId: string, current: boolean) => {
    await api.patch(`/admin/users/${userId}`, { is_active: !current })
    toast.success(`User ${current ? 'deactivated' : 'activated'}`)
    refetch()
  }

  const changeRole = async (userId: string, role: string) => {
    await api.patch(`/admin/users/${userId}`, { role })
    toast.success(`Role changed to ${role}`)
    refetch()
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-header">User Management</h1>
        <p className="page-subtitle">Manage user accounts, roles, and access</p>
      </div>
      <div className="glass-card overflow-hidden">
        <table className="data-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Role</th>
              <th>Status</th>
              <th>Last Login</th>
              <th>Joined</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && <tr><td colSpan={6} className="text-center py-12 text-slate-500">Loading...</td></tr>}
            {(users || []).map((u: any) => {
              const RoleIcon = roleIcon[u.role] || GraduationCap
              return (
                <tr key={u.id}>
                  <td>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-brand-600/20 border border-brand-500/30 flex items-center justify-center flex-shrink-0">
                        <span className="text-xs font-bold text-brand-400">{u.name[0]?.toUpperCase()}</span>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-slate-200">{u.name}</div>
                        <div className="text-xs text-slate-500">{u.email}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <div className="flex items-center gap-1.5">
                      <RoleIcon className="w-3.5 h-3.5 text-slate-400" />
                      <span className={`badge ${roleBadge[u.role]} capitalize`}>{u.role}</span>
                    </div>
                  </td>
                  <td>
                    <span className={u.is_active ? 'badge-green' : 'badge-gray'}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="text-xs text-slate-500">
                    {u.last_login ? new Date(u.last_login).toLocaleDateString() : 'Never'}
                  </td>
                  <td className="text-xs text-slate-500">{new Date(u.created_at).toLocaleDateString()}</td>
                  <td>
                    <div className="flex items-center gap-1">
                      <select
                        defaultValue={u.role}
                        onChange={(e) => changeRole(u.id, e.target.value)}
                        className="text-xs bg-white/5 border border-white/10 rounded-lg px-2 py-1 text-slate-300"
                      >
                        <option value="student">Student</option>
                        <option value="faculty">Faculty</option>
                        <option value="admin">Admin</option>
                      </select>
                      <button
                        onClick={() => toggleActive(u.id, u.is_active)}
                        className={`btn-ghost p-1.5 ${u.is_active ? 'text-red-400' : 'text-emerald-400'}`}
                        title={u.is_active ? 'Deactivate' : 'Activate'}
                      >
                        {u.is_active ? <UserX className="w-3.5 h-3.5" /> : <UserCheck className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
