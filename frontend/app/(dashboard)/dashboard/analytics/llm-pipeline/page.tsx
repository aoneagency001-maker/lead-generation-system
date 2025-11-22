"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useToast } from "@/hooks/use-toast"
import {
  Brain,
  Sparkles,
  TrendingUp,
  RefreshCw,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  Database,
  BarChart3
} from "lucide-react"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"

interface LLMStatus {
  openai: boolean
  anthropic: boolean
  perplexity: boolean
  overall_status: string
  layers: {
    l2_normalization: LayerStatus
    l3_features: LayerStatus
    l4_analysis: LayerStatus
  }
}

interface LayerStatus {
  model: string
  provider: string
  api_key_configured: boolean
  status: string
  fallback?: string
}

interface Insight {
  id: string
  date_from: string
  date_to: string
  insight_type: string
  executive_summary: string
  model_used: string
  generated_at: string
}

interface QueueStatus {
  pending: number
  processing: number
  completed_today: number
}

export default function LLMPipelinePage() {
  const { toast } = useToast()
  const [status, setStatus] = useState<LLMStatus | null>(null)
  const [insights, setInsights] = useState<Insight[]>([])
  const [queue, setQueue] = useState<QueueStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pipelineProgress, setPipelineProgress] = useState<{
    stage: string
    progress: number
    message: string
  } | null>(null)

  const fetchData = async (showToast = false) => {
    try {
      setLoading(true)
      setError(null)
      
      if (showToast) {
        toast({
          title: "Обновление данных...",
          description: "Загрузка статуса LLM сервисов",
        })
      }

      // Fetch LLM status
      const statusRes = await fetch(`${API_BASE}/api/llm/status`)
      if (statusRes.ok) {
        const statusData = await statusRes.json()
        console.log('LLM Status:', statusData)
        setStatus(statusData)
      } else {
        console.error('Failed to fetch LLM status:', statusRes.status, statusRes.statusText)
        setError(`Failed to fetch status: ${statusRes.statusText}`)
        if (showToast) {
          toast({
            title: "Ошибка загрузки",
            description: `Не удалось загрузить статус: ${statusRes.statusText}`,
            variant: "destructive",
          })
        }
      }

      // Fetch latest insights
      const insightsRes = await fetch(`${API_BASE}/api/llm/insights/latest?limit=5`)
      if (insightsRes.ok) {
        const insightsData = await insightsRes.json()
        setInsights(insightsData.insights || [])
      }

      // Fetch queue status
      const queueRes = await fetch(`${API_BASE}/api/llm/queue`)
      if (queueRes.ok) {
        const queueData = await queueRes.json()
        setQueue(queueData.queue_status)
      }
      
      if (showToast) {
        toast({
          title: "Данные обновлены",
          description: "Статус успешно загружен",
        })
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to fetch LLM pipeline data"
      setError(errorMsg)
      console.error(err)
      if (showToast) {
        toast({
          title: "Ошибка",
          description: errorMsg,
          variant: "destructive",
        })
      }
    } finally {
      setLoading(false)
    }
  }

  const runPipeline = async () => {
    console.log('🚀 runPipeline called!', { API_BASE, status })
    
    try {
      setRunning(true)
      setError(null)
      setPipelineProgress({ stage: "Инициализация", progress: 0, message: "Подготовка к запуску..." })
      
      const today = new Date().toISOString().split('T')[0]
      const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]

      toast({
        title: "Запуск Pipeline",
        description: `Обработка данных с ${weekAgo} по ${today}`,
      })

      setPipelineProgress({ stage: "Загрузка данных", progress: 20, message: "Получение событий из БД..." })

      const url = `${API_BASE}/api/llm/pipeline/run`
      console.log('🌐 Fetching:', url)

      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date_from: weekAgo,
          date_to: today,
          run_l4: true,
          async_mode: false
        })
      })

      console.log('✅ Pipeline response:', res.status, res.statusText)

      if (res.ok) {
        const result = await res.json()
        console.log('📊 Pipeline result:', result)
        
        // Check if no data, needs normalization, or partial completion
        if (result.status === "no_data" || result.status === "needs_normalization") {
          setPipelineProgress(null)

          toast({
            title: result.status === "needs_normalization" ? "Требуется нормализация" : "Нет данных",
            description: result.message || "Не найдено данных для обработки",
            variant: result.status === "needs_normalization" ? "default" : "destructive",
          })

          if (result.suggestion) {
            setTimeout(() => {
              toast({
                title: "Рекомендация",
                description: result.suggestion,
              })
            }, 2000)
          }

          return
        }

        // Handle partial completion (data already normalized)
        if (result.status === "partial") {
          await fetchData()
          setPipelineProgress({ stage: "Частичное завершение", progress: 100, message: "Данные уже обработаны" })

          toast({
            title: "Pipeline частично завершен",
            description: "Данные уже нормализованы. Используйте 'Генерировать Insights' для создания аналитики.",
          })

          setTimeout(() => {
            setPipelineProgress(null)
          }, 3000)
          return
        }

        setPipelineProgress({ stage: "Обработка", progress: 50, message: "Запуск LLM обработки..." })
        setPipelineProgress({ stage: "Завершение", progress: 80, message: "Сохранение результатов..." })
        
        await fetchData()
        
        setPipelineProgress({ stage: "Готово", progress: 100, message: "Pipeline успешно завершен" })
        
        toast({
          title: "Pipeline завершен",
          description: result.message || "Обработка данных успешно завершена",
        })
        
        // Скрыть прогресс через 3 секунды
        setTimeout(() => {
          setPipelineProgress(null)
        }, 3000)
      } else {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}: ${res.statusText}` }))
        console.error('❌ Pipeline error:', err)
        const errorMsg = err.detail || 'Pipeline failed'
        setError(errorMsg)
        setPipelineProgress(null)
        
        toast({
          title: "Ошибка Pipeline",
          description: errorMsg,
          variant: "destructive",
        })
      }
    } catch (err) {
      console.error('💥 Pipeline exception:', err)
      const errorMsg = `Failed to run pipeline: ${err instanceof Error ? err.message : String(err)}`
      setError(errorMsg)
      setPipelineProgress(null)
      
      toast({
        title: "Ошибка",
        description: errorMsg,
        variant: "destructive",
      })
    } finally {
      setRunning(false)
      console.log('🏁 Pipeline finished')
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const getStatusBadge = (isReady: boolean) => (
    <Badge variant={isReady ? "default" : "destructive"} className="ml-2">
      {isReady ? <CheckCircle className="w-3 h-3 mr-1" /> : <XCircle className="w-3 h-3 mr-1" />}
      {isReady ? "Ready" : "Not Configured"}
    </Badge>
  )

  const getLayerIcon = (layer: string) => {
    switch (layer) {
      case 'l2_normalization': return <Database className="w-5 h-5 text-blue-500" />
      case 'l3_features': return <Sparkles className="w-5 h-5 text-purple-500" />
      case 'l4_analysis': return <Brain className="w-5 h-5 text-green-500" />
      default: return <Zap className="w-5 h-5" />
    }
  }

  const getLayerName = (layer: string) => {
    switch (layer) {
      case 'l2_normalization': return 'L2: Normalization'
      case 'l3_features': return 'L3: Feature Engineering'
      case 'l4_analysis': return 'L4: Analysis & Insights'
      default: return layer
    }
  }

  if (loading && !status) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Brain className="w-8 h-8" />
            LLM Pipeline
          </h1>
          <p className="text-muted-foreground mt-1">
            3-layer AI processing: Normalization → Features → Insights
          </p>
        </div>
        <div className="flex gap-2 items-center">
          <Button 
            variant="outline" 
            onClick={() => fetchData(true)} 
            disabled={loading || running}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Обновление...' : 'Обновить'}
          </Button>
          <Button 
            onClick={() => {
              console.log('🖱️ Button clicked!')
              runPipeline()
            }}
            disabled={running || !status}
            title={
              !status 
                ? 'Загрузка статуса...' 
                : status.overall_status === 'ready' 
                  ? 'Все сервисы готовы' 
                  : status.overall_status === 'partial'
                    ? 'Некоторые сервисы не настроены (будут использованы доступные)'
                    : 'Сервисы не настроены'
            }
          >
            <Play className={`w-4 h-4 mr-2 ${running ? 'animate-pulse' : ''}`} />
            {running ? 'Запуск...' : 'Запустить Pipeline'}
          </Button>
          {status && status.overall_status === 'partial' && (
            <span className="text-xs text-muted-foreground ml-2">
              (Частично: некоторые API не настроены)
            </span>
          )}
        </div>
      </div>

      {error && (
        <Card className="border-destructive bg-destructive/10">
          <CardContent className="pt-4">
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Pipeline Progress */}
      {pipelineProgress && (
        <Card className="border-blue-500 bg-blue-50 dark:bg-blue-950/20">
          <CardContent className="pt-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-medium">{pipelineProgress.stage}</span>
                <span className="text-sm text-muted-foreground">{pipelineProgress.progress}%</span>
              </div>
              <Progress value={pipelineProgress.progress} className="h-2" />
              <p className="text-sm text-muted-foreground">{pipelineProgress.message}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* OpenAI */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center">
              <Database className="w-5 h-5 mr-2 text-blue-500" />
              OpenAI (GPT-4)
              {getStatusBadge(status?.openai || false)}
            </CardTitle>
            <CardDescription>L2: Normalization</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Model: {status?.layers?.l2_normalization?.model || 'N/A'}
            </p>
          </CardContent>
        </Card>

        {/* Anthropic */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center">
              <Sparkles className="w-5 h-5 mr-2 text-purple-500" />
              Claude
              {getStatusBadge(status?.anthropic || false)}
            </CardTitle>
            <CardDescription>L3: Feature Engineering</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Model: {status?.layers?.l3_features?.model || 'N/A'}
            </p>
          </CardContent>
        </Card>

        {/* Perplexity */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center">
              <Brain className="w-5 h-5 mr-2 text-green-500" />
              Perplexity
              {getStatusBadge(status?.perplexity || false)}
            </CardTitle>
            <CardDescription>L4: Analysis & Insights</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Model: {status?.layers?.l4_analysis?.model || 'N/A'}
            </p>
            {status?.layers?.l4_analysis?.fallback && (
              <p className="text-xs text-muted-foreground mt-1">
                Fallback: {status.layers.l4_analysis.fallback}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Queue Status */}
      {queue && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Processing Queue
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-yellow-500">{queue.pending}</p>
                <p className="text-sm text-muted-foreground">Pending</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-blue-500">{queue.processing}</p>
                <p className="text-sm text-muted-foreground">Processing</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-green-500">{queue.completed_today}</p>
                <p className="text-sm text-muted-foreground">Completed Today</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pipeline Flow Visualization */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Pipeline Flow
          </CardTitle>
          <CardDescription>
            Data flows through 3 AI layers: Raw → Normalized → Features → Insights
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
            {/* L1 Raw */}
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 rounded-full bg-gray-500/20 flex items-center justify-center">
                <Database className="w-8 h-8 text-gray-500" />
              </div>
              <p className="mt-2 font-medium">L1: Raw</p>
              <p className="text-xs text-muted-foreground">GA4 + Metrika</p>
            </div>

            <div className="flex-1 h-1 bg-blue-500/50 mx-2" />

            {/* L2 Normalized */}
            <div className="flex flex-col items-center">
              <div className={`w-16 h-16 rounded-full flex items-center justify-center ${status?.openai ? 'bg-blue-500/20' : 'bg-gray-300/20'}`}>
                <Database className={`w-8 h-8 ${status?.openai ? 'text-blue-500' : 'text-gray-400'}`} />
              </div>
              <p className="mt-2 font-medium">L2: Normalized</p>
              <p className="text-xs text-muted-foreground">GPT-4</p>
            </div>

            <div className="flex-1 h-1 bg-purple-500/50 mx-2" />

            {/* L3 Features */}
            <div className="flex flex-col items-center">
              <div className={`w-16 h-16 rounded-full flex items-center justify-center ${status?.anthropic ? 'bg-purple-500/20' : 'bg-gray-300/20'}`}>
                <Sparkles className={`w-8 h-8 ${status?.anthropic ? 'text-purple-500' : 'text-gray-400'}`} />
              </div>
              <p className="mt-2 font-medium">L3: Features</p>
              <p className="text-xs text-muted-foreground">Claude</p>
            </div>

            <div className="flex-1 h-1 bg-green-500/50 mx-2" />

            {/* L4 Insights */}
            <div className="flex flex-col items-center">
              <div className={`w-16 h-16 rounded-full flex items-center justify-center ${status?.perplexity ? 'bg-green-500/20' : 'bg-gray-300/20'}`}>
                <Brain className={`w-8 h-8 ${status?.perplexity ? 'text-green-500' : 'text-gray-400'}`} />
              </div>
              <p className="mt-2 font-medium">L4: Insights</p>
              <p className="text-xs text-muted-foreground">Perplexity</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Latest Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Latest Insights
          </CardTitle>
          <CardDescription>
            AI-generated business insights from your analytics data
          </CardDescription>
        </CardHeader>
        <CardContent>
          {insights.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No insights generated yet</p>
              <p className="text-sm mt-1">Run the pipeline to generate insights</p>
            </div>
          ) : (
            <div className="space-y-4">
              {insights.map((insight) => (
                <div key={insight.id} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant="outline">{insight.insight_type}</Badge>
                    <span className="text-xs text-muted-foreground">
                      {new Date(insight.generated_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-sm">
                    {insight.executive_summary || 'No summary available'}
                  </p>
                  <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                    <span>Period: {insight.date_from} - {insight.date_to}</span>
                    <span>|</span>
                    <span>Model: {insight.model_used}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
