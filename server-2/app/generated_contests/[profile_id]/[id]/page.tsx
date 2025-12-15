"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ExternalLink } from "lucide-react"
import Link from "next/link"
import { useEffect, useState } from "react"
import { use } from "react"

interface CodeforcesTask {
  contestId: number
  index: string
  name: string
  rating?: number
  tags: string[]
}

function getDifficultyColor(rating?: number) {
  if (!rating) return "text-muted-foreground"
  if (rating <= 1000) return "text-[#84cc16]" // lime-500 (салатовый)
  if (rating <= 1400) return "text-[#a3e635]" // lime-400
  if (rating <= 1900) return "text-[#eab308]" // yellow-500
  if (rating <= 2800) return "text-[#ef4444]" // red-500
  return "text-[#7f1d1d]" // red-900 (бордовый)
}

function getDifficultyLabel(rating?: number) {
  if (!rating) return "Не указана"
  if (rating <= 1000) return "Очень легкая"
  if (rating <= 1400) return "Легкая"
  if (rating <= 1900) return "Средняя"
  if (rating <= 2800) return "Сложная"
  return "Очень сложная"
}

export default function GeneratedContestPage({
  params,
}: {
  params: Promise<{ profile_id: string; id: string }>
}) {
  const { profile_id, id } = use(params)
  const [tasks, setTasks] = useState<CodeforcesTask[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchGeneratedContest() {
      try {
        // Fetch the generated contest data from your backend
        const response = await fetch(`http://localhost:8000/generated-contest/${profile_id}/${id}`)
        const data = await response.json()

        // Assuming the response contains task IDs in format "contestId-index"
        const taskPromises = data.taskIds.map(async (taskId: string) => {
          const [contestId, index] = taskId.split("-")
          // Fetch each task details from Codeforces
          const problemResponse = await fetch("https://codeforces.com/api/problemset.problems")
          const problemData = await problemResponse.json()
          if (problemData.status === "OK") {
            return problemData.result.problems.find(
              (p: CodeforcesTask) => p.contestId === Number.parseInt(contestId) && p.index === index,
            )
          }
          return null
        })

        const fetchedTasks = await Promise.all(taskPromises)
        setTasks(fetchedTasks.filter((t) => t !== null))
      } catch (error) {
        console.error("Error fetching generated contest:", error)
      } finally {
        setLoading(false)
      }
    }
    fetchGeneratedContest()
  }, [profile_id, id])

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-[1600px]">
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-2xl font-bold">Сгенерированный контест #{id}</CardTitle>
            <p className="text-sm text-muted-foreground">Профиль: {profile_id}</p>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex h-[calc(100vh-300px)] items-center justify-center">
                <p className="text-muted-foreground">Загрузка контеста...</p>
              </div>
            ) : (
              <ScrollArea className="h-[calc(100vh-300px)] w-full pr-6">
                <div className="flex flex-col gap-3">
                  {tasks.map((task) => (
                    <div key={`${task.contestId}-${task.index}`} className="flex items-center gap-3">
                      <Link href={`/task/${task.contestId}-${task.index}`} className="flex-1">
                        <div className="flex items-center justify-between rounded-lg border border-border/50 bg-secondary/30 p-4 transition-colors hover:bg-secondary/50">
                          <div className="flex items-center gap-4 flex-1 min-w-0">
                            <span className="text-sm shrink-0 font-bold">
                              {task.contestId}-{task.index}
                            </span>
                            <div className="h-6 w-px bg-border/70" />
                            <h3 className="font-medium truncate">{task.name}</h3>
                          </div>

                          <div className="flex items-center gap-4 shrink-0">
                            <span className={`font-bold min-w-[9rem] text-center ${getDifficultyColor(task.rating)}`}>
                              {getDifficultyLabel(task.rating)}
                            </span>
                            <div className="h-6 w-px bg-border/70" />
                            <span className="font-semibold min-w-[3rem] text-center">{task.rating || "—"}</span>
                            <div className="h-6 w-px bg-border/70" />
                            <Badge variant="outline" className="min-w-[8rem] justify-center">
                              {task.tags[0] || "Без темы"}
                            </Badge>
                          </div>
                        </div>
                      </Link>

                      <div className="flex items-center justify-between rounded-lg border border-border/50 p-2 bg-secondary/30 transition-colors hover:bg-secondary/50">
                        <Button size="icon" variant="outline" className="h-10 w-10 shrink-0 bg-transparent" asChild>
                          <a
                            href={`https://codeforces.com/problemset/problem/${task.contestId}/${task.index}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            title="Открыть на Codeforces"
                          >
                            <ExternalLink className="h-5 w-5" />
                          </a>
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
