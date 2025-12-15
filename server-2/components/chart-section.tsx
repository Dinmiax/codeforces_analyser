"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useEffect, useState } from "react"

interface ChartData {
  name: string
  value: number
}

// Цвета для диаграммы
const COLORS = [
  "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
  "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
  "#F8C471", "#82E0AA", "#F1948A", "#85C1E9", "#D7BDE2"
]

export function ChartSection() {
  const [data, setData] = useState<ChartData[]>([])
  const [loading, setLoading] = useState(true)

  // Имитация загрузки данных из API
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Здесь будет реальный API call
        // const response = await fetch('/api/topics')
        // const apiData = await response.json()
        
        // Имитируем задержку API
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // Данные из API (в реальности будут приходить с сервера)
        const apiData: ChartData[] = [
          { name: "Dynamic Programming", value: 35 },
          { name: "Algorithms", value: 25 },
          { name: "Combinatorics", value: 20 },
          { name: "Graphs", value: 12 },
          { name: "Binary Search", value: 8 },
        ]
        
        setData(apiData)
      } catch (error) {
        console.error('Error fetching data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-xl font-semibold">Статистика по темам</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64">
          <p className="text-muted-foreground">Загрузка данных...</p>
        </CardContent>
      </Card>
    )
  }

  if (data.length === 0) {
    return (
      <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-xl font-semibold">Статистика по темам</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64">
          <p className="text-muted-foreground">Нет данных для отображения</p>
        </CardContent>
      </Card>
    )
  }

  const total = data.reduce((sum, item) => sum + item.value, 0)
  let currentAngle = 0

  return (
    <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="text-xl font-semibold">Статистика по темам</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center justify-center">
        <div className="w-full max-w-md">
          <svg viewBox="0 0 100 100" className="w-full h-64">
            {data.map((item, index) => {
              const angle = (item.value / total) * 360
              const largeArcFlag = angle > 180 ? 1 : 0
              
              const startAngle = currentAngle
              const endAngle = currentAngle + angle
              
              const x1 = 50 + 40 * Math.cos(startAngle * Math.PI / 180)
              const y1 = 50 + 40 * Math.sin(startAngle * Math.PI / 180)
              
              const x2 = 50 + 40 * Math.cos(endAngle * Math.PI / 180)
              const y2 = 50 + 40 * Math.sin(endAngle * Math.PI / 180)

              const pathData = [
                `M 50 50`,
                `L ${x1} ${y1}`,
                `A 40 40 0 ${largeArcFlag} 1 ${x2} ${y2}`,
                `L 50 50`
              ].join(' ')

              currentAngle = endAngle

              return (
                <path
                  key={index}
                  d={pathData}
                  fill={COLORS[index % COLORS.length]}
                  stroke="white"
                  strokeWidth="0.5"
                />
              )
            })}
          </svg>
          
          <div className="mt-4 grid grid-cols-1 gap-2">
            {data.map((item, index) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span>{item.name}</span>
                </div>
                <span className="font-medium">
                  {item.value}% ({((item.value / total) * 100).toFixed(1)}%)
                </span>
              </div>
            ))}
          </div>
          
          <div className="mt-4 text-center text-sm text-muted-foreground">
            Всего: {total} задач
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
