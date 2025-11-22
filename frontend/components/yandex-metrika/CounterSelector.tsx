"use client"

import { useState, useEffect } from "react"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Loader2 } from "lucide-react"

interface Counter {
  id: number
  name: string
  site: string
  status: string
  type: string
}

interface CounterSelectorProps {
  onCounterSelect?: (counterId: number) => void
  selectedCounterId?: number | null
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export function CounterSelector({ onCounterSelect, selectedCounterId }: CounterSelectorProps) {
  const [counters, setCounters] = useState<Counter[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<number | null>(selectedCounterId || null)

  useEffect(() => {
    loadCounters()
  }, [])

  useEffect(() => {
    if (selectedCounterId !== undefined) {
      setSelectedId(selectedCounterId)
    }
  }, [selectedCounterId])

  const loadCounters = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`${API_URL}/api/yandex-metrika/counters`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'omit',
      })
      
      if (!response.ok) {
        let errorMessage = `Ошибка ${response.status}`
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail?.message || errorData.message || errorData.error || errorMessage
        } catch (e) {
          const text = await response.text()
          errorMessage = text || errorMessage
        }
        throw new Error(errorMessage)
      }
      
      const data = await response.json()
      setCounters(data.counters || [])
      
      // Если счетчики загружены и есть сохраненный ID, выбираем его
      if (selectedId && data.counters?.some((c: Counter) => c.id === selectedId)) {
        // ID уже выбран
      } else if (data.counters?.length > 0 && !selectedId) {
        // Автоматически выбираем первый счетчик, если ничего не выбрано
        const firstCounter = data.counters[0]
        setSelectedId(firstCounter.id)
        onCounterSelect?.(firstCounter.id)
        saveCounterId(firstCounter.id)
      }
    } catch (err) {
      let errorMessage = "Не удалось загрузить счетчики"
      
      if (err instanceof TypeError && err.message.includes('fetch')) {
        errorMessage = `Не удалось подключиться к серверу. Проверьте, что бэкенд запущен на ${API_URL}`
      } else if (err instanceof Error) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const saveCounterId = (counterId: number) => {
    // Сохраняем в localStorage
    if (typeof window !== "undefined") {
      localStorage.setItem("yandex_metrika_counter_id", counterId.toString())
    }
  }

  const handleCounterChange = (value: string) => {
    const counterId = parseInt(value, 10)
    setSelectedId(counterId)
    saveCounterId(counterId)
    onCounterSelect?.(counterId)
  }

  // Загружаем сохраненный ID при монтировании
  useEffect(() => {
    if (typeof window !== "undefined" && !selectedId) {
      const savedId = localStorage.getItem("yandex_metrika_counter_id")
      if (savedId) {
        const id = parseInt(savedId, 10)
        setSelectedId(id)
        onCounterSelect?.(id)
      }
    }
  }, [])

  if (loading) {
    return (
      <div className="flex items-center gap-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-sm text-muted-foreground">Загрузка счетчиков...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-2">
        <div className="text-sm text-destructive">{error}</div>
        <Button
          variant="outline"
          size="sm"
          onClick={loadCounters}
        >
          Повторить
        </Button>
      </div>
    )
  }

  if (counters.length === 0) {
    return (
      <div className="text-sm text-muted-foreground">
        Счетчики не найдены
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <Select
        value={selectedId?.toString() || ""}
        onValueChange={handleCounterChange}
      >
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Выберите счетчик" />
        </SelectTrigger>
        <SelectContent>
          {counters.map((counter) => (
            <SelectItem key={counter.id} value={counter.id.toString()}>
              <div className="flex flex-col">
                <span className="font-medium">{counter.name}</span>
                {counter.site && (
                  <span className="text-xs text-muted-foreground">
                    {counter.site}
                  </span>
                )}
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {selectedId && (
        <div className="text-xs text-muted-foreground">
          Выбран счетчик: {counters.find(c => c.id === selectedId)?.name}
        </div>
      )}
    </div>
  )
}

