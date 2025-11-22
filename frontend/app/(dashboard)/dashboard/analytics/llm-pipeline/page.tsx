"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
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
  const [status, setStatus] = useState<LLMStatus | null>(null)
  const [insights, setInsights] = useState<Insight[]>([])
  const [queue, setQueue] = useState<QueueStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch LLM status
      const statusRes = await fetch(`${API_BASE}/api/llm/status`)
      if (statusRes.ok) {
        const statusData = await statusRes.json()
        setStatus(statusData)
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
    } catch (err) {
      setError("Failed to fetch LLM pipeline data")
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const runPipeline = async () => {
    try {
      setRunning(true)
      const today = new Date().toISOString().split('T')[0]
      const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]

      const res = await fetch(`${API_BASE}/api/llm/pipeline/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date_from: weekAgo,
          date_to: today,
          run_l4: true,
          async_mode: false
        })
      })

      if (res.ok) {
        await fetchData()
      } else {
        const err = await res.json()
        setError(err.detail || 'Pipeline failed')
      }
    } catch (err) {
      setError('Failed to run pipeline')
      console.error(err)
    } finally {
      setRunning(false)
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
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={runPipeline} disabled={running || status?.overall_status !== 'ready'}>
            <Play className={`w-4 h-4 mr-2 ${running ? 'animate-pulse' : ''}`} />
            {running ? 'Running...' : 'Run Pipeline'}
          </Button>
        </div>
      </div>

      {error && (
        <Card className="border-destructive bg-destructive/10">
          <CardContent className="pt-4">
            <p className="text-destructive">{error}</p>
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
