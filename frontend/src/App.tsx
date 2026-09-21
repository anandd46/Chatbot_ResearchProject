import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import LandingPage from '@/pages/LandingPage'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import ChatPage from '@/pages/ChatPage'
import AdminLayout from '@/components/layout/AdminLayout'
import DashboardPage from '@/pages/admin/DashboardPage'
import KnowledgePage from '@/pages/admin/KnowledgePage'
import UnresolvedPage from '@/pages/admin/UnresolvedPage'
import ConversationsPage from '@/pages/admin/ConversationsPage'
import AnalyticsPage from '@/pages/admin/AnalyticsPage'
import NlpInspectorPage from '@/pages/admin/NlpInspectorPage'
import EvaluationPage from '@/pages/admin/EvaluationPage'
import FeedbackPage from '@/pages/admin/FeedbackPage'
import UsersPage from '@/pages/admin/UsersPage'
import SettingsPage from '@/pages/admin/SettingsPage'
import ImprovementPage from '@/pages/admin/ImprovementPage'
import StatusPage from '@/pages/admin/StatusPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuthStore()
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== 'admin') return <Navigate to="/chat" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <ChatPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <AdminRoute>
              <AdminLayout />
            </AdminRoute>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="knowledge" element={<KnowledgePage />} />
          <Route path="unresolved" element={<UnresolvedPage />} />
          <Route path="conversations" element={<ConversationsPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="nlp-inspector" element={<NlpInspectorPage />} />
          <Route path="evaluation" element={<EvaluationPage />} />
          <Route path="feedback" element={<FeedbackPage />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="improvement" element={<ImprovementPage />} />
          <Route path="status" element={<StatusPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
