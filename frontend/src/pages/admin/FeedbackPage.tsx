import { useFeedbackList } from '@/api/hooks'
import { useState } from 'react'
import { Star } from 'lucide-react'

export default function FeedbackPage() {
  const [page, setPage] = useState(1)
  const { data: feedback, isLoading } = useFeedbackList(page)

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-header">User Feedback</h1>
        <p className="page-subtitle">Star ratings and comments submitted on chatbot responses</p>
      </div>
      <div className="glass-card overflow-hidden">
        <table className="data-table">
          <thead>
            <tr>
              <th>Rating</th>
              <th>Comment</th>
              <th>Message ID</th>
              <th>User</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && <tr><td colSpan={5} className="text-center py-12 text-slate-500">Loading...</td></tr>}
            {(feedback || []).map((f: any) => (
              <tr key={f.id}>
                <td>
                  <div className="flex items-center gap-1">
                    {Array.from({ length: 5 }, (_, i) => (
                      <Star key={i} className={`w-4 h-4 ${i < f.rating ? 'text-amber-400 fill-current' : 'text-slate-600'}`} />
                    ))}
                    <span className="text-sm text-slate-400 ml-1">({f.rating}/5)</span>
                  </div>
                </td>
                <td className="text-slate-300">{f.comment || <span className="text-slate-600 italic">No comment</span>}</td>
                <td className="font-mono text-xs text-slate-500">{f.message_id?.slice(0, 8)}...</td>
                <td className="font-mono text-xs text-slate-500">{f.user_id?.slice(0, 8)}...</td>
                <td className="text-xs text-slate-500">{new Date(f.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
            {!isLoading && !(feedback || []).length && (
              <tr><td colSpan={5} className="text-center py-12 text-slate-500">No feedback submitted yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
