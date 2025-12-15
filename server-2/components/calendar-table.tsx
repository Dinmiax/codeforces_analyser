"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle  } from "@/components/ui/card"

const DAYS = ["Mon", "Tue", "Wed", "Thur", "Friday", "Sat", "Sun"]
const WEEKS = 5 // Number of weeks to display

export function CalendarTable() {
  const [calendarData, setCalendarData] = useState<string[][]>(
    Array(WEEKS)
      .fill(null)
      .map(() => Array(DAYS.length).fill("")),
  )

  return (
    <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
    <CardHeader>
          <CardTitle className="text-xl font-semibold">История решений</CardTitle>
        </CardHeader>
      <div className="border-border/50 bg-card/50 backdrop-blur-sm" />

      <div className="relative p-3 space-y-2">
        

        {/* Calendar Grid */}
        <div className="overflow-x-auto">
          <div className="min-w-full">
            {/* Header Row */}
            <div className="grid grid-cols-7 gap-0.5 mb-1">
              {DAYS.map((day) => (
                <div key={day} className="text-center text-[10px] font-medium text-muted-foreground py-0.5">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar Rows */}
            <div className="space-y-0.5">
              {calendarData.map((week, weekIndex) => (
                <div key={weekIndex} className="grid grid-cols-7 gap-0.5">
                  {week.map((cell, dayIndex) => (
                    <div
                      key={`${weekIndex}-${dayIndex}`}
                      className="aspect-square border border-primary/20 rounded bg-background/50 flex items-center justify-center text-[10px] text-foreground"
                    >
                      {cell}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}
