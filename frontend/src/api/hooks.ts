import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from './client'

export const useLogin = () =>
  useMutation({
    mutationFn: (data: { email: string; password: string }) =>
      api.post('/auth/login', data).then((r) => r.data),
  })

export const useRegister = () =>
  useMutation({
    mutationFn: (data: { email: string; password: string; name: string; role?: string }) =>
      api.post('/auth/register', data).then((r) => r.data),
  })

export const useMe = () =>
  useQuery({ queryKey: ['me'], queryFn: () => api.get('/auth/me').then((r) => r.data) })

export const useSendMessage = () =>
  useMutation({
    mutationFn: (data: { message: string; session_id?: string }) =>
      api.post('/chat/send', data).then((r) => r.data),
  })

export const useSessions = () =>
  useQuery({ queryKey: ['sessions'], queryFn: () => api.get('/chat/sessions').then((r) => r.data) })

export const useSessionMessages = (sessionId: string) =>
  useQuery({
    queryKey: ['session-messages', sessionId],
    queryFn: () => api.get(`/chat/sessions/${sessionId}/messages`).then((r) => r.data),
    enabled: !!sessionId,
  })

export const useSubmitFeedback = () =>
  useMutation({
    mutationFn: (data: { message_id: string; rating: number; comment?: string }) =>
      api.post('/feedback/', data).then((r) => r.data),
  })

export const useKnowledgeEntries = (page = 1, pageSize = 20, category?: string) =>
  useQuery({
    queryKey: ['knowledge', page, pageSize, category],
    queryFn: () =>
      api.get('/knowledge/', { params: { page, page_size: pageSize, category } }).then((r) => r.data),
  })

export const useCreateKnowledge = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: object) => api.post('/knowledge/', data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['knowledge'] }),
  })
}

export const useUpdateKnowledge = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: object }) =>
      api.put(`/knowledge/${id}`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['knowledge'] }),
  })
}

export const useDeleteKnowledge = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete(`/knowledge/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['knowledge'] }),
  })
}

export const useReindex = () =>
  useMutation({ mutationFn: () => api.post('/knowledge/reindex').then((r) => r.data) })

export const useKnowledgeVersions = (entryId: string) =>
  useQuery({
    queryKey: ['kb-versions', entryId],
    queryFn: () => api.get(`/knowledge/${entryId}/versions`).then((r) => r.data),
    enabled: !!entryId,
  })

export const useUnresolvedQueries = (status?: string, page = 1) =>
  useQuery({
    queryKey: ['unresolved', status, page],
    queryFn: () =>
      api.get('/unresolved/', { params: { status, page } }).then((r) => r.data),
  })

export const useUpdateUnresolved = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: object }) =>
      api.patch(`/unresolved/${id}`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['unresolved'] }),
  })
}

export const useConvertToKb = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: object }) =>
      api.post(`/unresolved/${id}/convert`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['unresolved'] })
      qc.invalidateQueries({ queryKey: ['knowledge'] })
    },
  })
}

export const useOverviewStats = () =>
  useQuery({
    queryKey: ['admin-overview'],
    queryFn: () => api.get('/admin/analytics/overview').then((r) => r.data),
    refetchInterval: 30_000,
  })

export const useIntentDistribution = () =>
  useQuery({
    queryKey: ['intent-dist'],
    queryFn: () => api.get('/admin/analytics/intents').then((r) => r.data),
  })

export const useDailyStats = (days = 30) =>
  useQuery({
    queryKey: ['daily-stats', days],
    queryFn: () => api.get('/admin/analytics/daily', { params: { days } }).then((r) => r.data),
  })

export const useFeedbackStats = () =>
  useQuery({
    queryKey: ['feedback-stats'],
    queryFn: () => api.get('/admin/analytics/feedback').then((r) => r.data),
  })

export const useAdminUsers = (page = 1) =>
  useQuery({
    queryKey: ['admin-users', page],
    queryFn: () => api.get('/admin/users', { params: { page } }).then((r) => r.data),
  })

export const useAdminConversations = (page = 1) =>
  useQuery({
    queryKey: ['admin-conversations', page],
    queryFn: () => api.get('/admin/conversations', { params: { page } }).then((r) => r.data),
  })

export const useNlpInspect = () =>
  useMutation({
    mutationFn: (query: string) => api.post('/admin/nlp/inspect', { query }).then((r) => r.data),
  })

export const useNlpSettings = () =>
  useQuery({
    queryKey: ['nlp-settings'],
    queryFn: () => api.get('/admin/settings/nlp').then((r) => r.data),
  })

export const useUpdateNlpSettings = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: object) => api.patch('/admin/settings/nlp', data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['nlp-settings'] }),
  })
}

export const useSystemStatus = () =>
  useQuery({
    queryKey: ['system-status'],
    queryFn: () => api.get('/admin/status').then((r) => r.data),
    refetchInterval: 15_000,
  })

export const useEvalDatasets = () =>
  useQuery({
    queryKey: ['eval-datasets'],
    queryFn: () => api.get('/evaluation/datasets').then((r) => r.data),
  })

export const useRunEvaluation = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ datasetId, mode }: { datasetId: string; mode: string }) =>
      api.post(`/evaluation/datasets/${datasetId}/run`, { mode }).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['eval-runs'] }),
  })
}

export const useEvalRuns = () =>
  useQuery({
    queryKey: ['eval-runs'],
    queryFn: () => api.get('/evaluation/runs').then((r) => r.data),
  })

export const useEvalRun = (runId: string) =>
  useQuery({
    queryKey: ['eval-run', runId],
    queryFn: () => api.get(`/evaluation/runs/${runId}`).then((r) => r.data),
    enabled: !!runId,
  })

export const useFeedbackList = (page = 1) =>
  useQuery({
    queryKey: ['admin-feedback', page],
    queryFn: () => api.get('/feedback/', { params: { page } }).then((r) => r.data),
  })
