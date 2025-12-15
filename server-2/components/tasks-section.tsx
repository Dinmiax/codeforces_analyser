"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"

export function TasksSection() {
  return (
    <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="text-center text-xl font-semibold">Рекомендации</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[500px] w-full rounded-lg border border-border/50 bg-secondary/30 p-4">
          <div className="flex h-full items-center justify-center">
            <p className="text-center text-sm text-muted-foreground">Задачи будут загружены системой</p>
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
