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
import { apiClient } from "@/lib/api-client"
import type { GA4Property } from "@/types/ga4"

interface PropertySelectorProps {
  onPropertySelect?: (propertyId: string) => void
  selectedPropertyId?: string | null
}

export function PropertySelector({ onPropertySelect, selectedPropertyId }: PropertySelectorProps) {
  const [properties, setProperties] = useState<GA4Property[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(selectedPropertyId || null)

  useEffect(() => {
    loadProperties()
  }, [])

  useEffect(() => {
    if (selectedPropertyId !== undefined) {
      setSelectedId(selectedPropertyId)
    }
  }, [selectedPropertyId])

  const loadProperties = async () => {
    setLoading(true)
    setError(null)
    
    try {
      console.log("🔍 Загрузка GA4 Properties...")
      const data = await apiClient.getGA4Properties()
      console.log("✅ Получены данные:", data)
      
      const propertiesList = data.properties || []
      console.log(`📊 Найдено Properties: ${propertiesList.length}`)
      
      setProperties(propertiesList)
      
      // Если Properties загружены и есть сохраненный ID, выбираем его
      if (selectedId && propertiesList.some((p: GA4Property) => p.id === selectedId)) {
        console.log(`✅ Используем сохраненный Property: ${selectedId}`)
        // ID уже выбран
      } else if (propertiesList.length > 0 && !selectedId) {
        // Автоматически выбираем первый Property, если ничего не выбрано
        const firstProperty = propertiesList[0]
        console.log(`🎯 Автоматически выбираем первый Property: ${firstProperty.id}`)
        setSelectedId(firstProperty.id)
        onPropertySelect?.(firstProperty.id)
        savePropertyId(firstProperty.id)
      }
    } catch (err) {
      let errorMessage = "Не удалось загрузить Properties"
      
      if (err instanceof Error) {
        errorMessage = err.message
      }
      
      console.error("❌ Ошибка загрузки Properties:", err)
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const savePropertyId = (propertyId: string) => {
    // Сохраняем в localStorage
    if (typeof window !== "undefined") {
      localStorage.setItem("ga4_property_id", propertyId)
    }
  }

  const handlePropertyChange = (value: string) => {
    setSelectedId(value)
    savePropertyId(value)
    onPropertySelect?.(value)
  }

  // Загружаем сохраненный ID при монтировании
  useEffect(() => {
    if (typeof window !== "undefined" && !selectedId) {
      const savedId = localStorage.getItem("ga4_property_id")
      if (savedId) {
        setSelectedId(savedId)
        onPropertySelect?.(savedId)
      }
    }
  }, [])

  if (loading) {
    return (
      <div className="flex items-center gap-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-sm text-muted-foreground">Загрузка Properties...</span>
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
          onClick={loadProperties}
        >
          Повторить
        </Button>
      </div>
    )
  }

  if (properties.length === 0) {
    return (
      <div className="text-sm text-muted-foreground">
        Properties не найдены. Убедитесь, что GOOGLE_ANALYTICS_PROPERTY_ID установлен в .env
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <Select
        value={selectedId || ""}
        onValueChange={handlePropertyChange}
      >
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Выберите Property" />
        </SelectTrigger>
        <SelectContent>
          {properties.map((property) => (
            <SelectItem key={property.id} value={property.id}>
              <div className="flex flex-col">
                <span className="font-medium">{property.name}</span>
                <span className="text-xs text-muted-foreground">
                  {property.id}
                </span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {selectedId && (
        <div className="text-xs text-muted-foreground">
          Выбран Property: {properties.find(p => p.id === selectedId)?.name}
        </div>
      )}
    </div>
  )
}

