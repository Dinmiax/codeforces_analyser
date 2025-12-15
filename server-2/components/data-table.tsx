"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Pencil, Check, X } from "lucide-react"

interface TableRow {
  id: number
  name: string
  value?: string
  placeholder?: string
  editable?: boolean
}

export function DataTable() {
  const [data, setData] = useState<TableRow[]>([
    { id: 1, name: "Хэндл", value: "", placeholder: "", editable: false },
    { id: 2, name: "Рейтинг", value: "", placeholder: "", editable: false },
    { id: 3, name: "Сегодня решено", value: "", placeholder: "", editable: false },
    { id: 4, name: "Решено за все время", value: "", placeholder: "", editable: false },
    { id: 5, name: "Любимая тема", value: "", placeholder: "", editable: false },
  ])

  const [editingId, setEditingId] = useState<number | null>(null)
  const [editValue, setEditValue] = useState("")

  const startEdit = (row: TableRow) => {
    setEditingId(row.id)
    setEditValue(row.value || "")
  }

  const saveEdit = (id: number) => {
    setData(data.map((row) => (row.id === id ? { ...row, value: editValue } : row)))
    setEditingId(null)
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditValue("")
  }

  return (
    <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="text-xl font-semibold">Информация о пользователе</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {data.map((row) => (
            <div
              key={row.id}
              className="flex items-center justify-between rounded-lg border border-border/50 bg-secondary/30 p-4 transition-colors hover:bg-secondary/50"
            >
              <div className="flex-1">
                <p className="text-sm text-muted-foreground">{row.name}</p>
                {editingId === row.id ? (
                  <Input
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    placeholder={row.placeholder}
                    className="mt-1 h-8 bg-background"
                    autoFocus
                  />
                ) : (
                  <p className="mt-1 text-foreground">
                    {row.value ? (
                      row.value
                    ) : (
                      <span className="text-muted-foreground/60">{row.placeholder || "—"}</span>
                    )}
                  </p>
                )}
              </div>
              {row.editable && (
                <div className="ml-4 flex gap-2">
                  {editingId === row.id ? (
                    <>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8 text-primary hover:bg-primary/20"
                        onClick={() => saveEdit(row.id)}
                      >
                        <Check className="h-4 w-4" />
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8 text-muted-foreground hover:bg-secondary"
                        onClick={cancelEdit}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </>
                  ) : (
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-8 w-8 text-muted-foreground hover:bg-secondary hover:text-primary"
                      onClick={() => startEdit(row)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
