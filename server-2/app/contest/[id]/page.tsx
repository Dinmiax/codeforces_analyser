"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ExternalLink } from "lucide-react"
import Link from "next/link"
import { useEffect, useState, useMemo } from "react"

interface CodeforcesTask {
  contestId: number
  index: string
  name: string
  rating?: number
  tags: string[]
}

interface ContestInfo {
  id: number
  name: string
  type: string
  phase: string
  durationSeconds: number
  startTimeSeconds: number
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

function getDivision(name: string): string {
  if (name.includes("Div. 1")) return "Div. 1"
  if (name.includes("Div. 2")) return "Div. 2"
  if (name.includes("Div. 3")) return "Div. 3"
  if (name.includes("Div. 4")) return "Div. 4"
  return "Other"
}

export default async function ContestPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params

  return <ContestPageClient id={id} />
}

function ContestPageClient({ id }: { id: string }) {
  const [tasks, setTasks] = useState<CodeforcesTask[]>([])
  const [contestInfo, setContestInfo] = useState<ContestInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc")
  const [tagFilter, setTagFilter] = useState<string>("all")

  useEffect(() => {
    async function fetchContestData() {
      try {
        // Fetch contest info
        const contestResponse = await fetch("https://codeforces.com/api/contest.list")
        const contestData = await contestResponse.json()
        if (contestData.status === "OK") {
          const contest = contestData.result.find((c: ContestInfo) => c.id === Number.parseInt(id))
          setContestInfo(contest || null)
        }

        // Fetch contest problems
        const problemsResponse = await fetch(
          `https://codeforces.com/api/contest.standings?contestId=${id}&from=1&count=1`,
        )
        const problemsData = await problemsResponse.json()
        if (problemsData.status === "OK") {
          setTasks(problemsData.result.problems)
        }
      } catch (error) {
        console.error("Error fetching contest data:", error)
      } finally {
        setLoading(false)
      }
    }
    fetchContestData()
  }, [id])

  const uniqueTags = useMemo(() => {
    const tags = new Set<string>()
    tasks.forEach((task) => {
      task.tags.forEach((tag) => tags.add(tag))
    })
    return Array.from(tags).sort()
  }, [tasks])

  const averageRating = useMemo(() => {
    const ratingsSum = tasks.reduce((sum, task) => sum + (task.rating || 0), 0)
    const ratingsCount = tasks.filter((task) => task.rating).length
    return ratingsCount > 0 ? Math.round(ratingsSum / ratingsCount) : 0
  }, [tasks])

  const filteredAndSortedTasks = useMemo(() => {
    let result = [...tasks]

    // Tag filter
    if (tagFilter !== "all") {
      result = result.filter((task) => task.tags.includes(tagFilter))
    }

    // Sort by rating
    result.sort((a, b) => {
      const ratingA = a.rating || 0
      const ratingB = b.rating || 0
      return sortOrder === "asc" ? ratingA - ratingB : ratingB - ratingA
    })

    return result
  }, [tasks, sortOrder, tagFilter])

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-[1600px]">
        <Link href="/contests">
          <Button variant="outline" className="mb-4 bg-transparent">
            ← Назад к контестам
          </Button>
        </Link>

        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <div className="space-y-2">
              <CardTitle className="text-2xl font-bold">{contestInfo?.name || `Контест ${id}`}</CardTitle>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <Badge variant="outline">{contestInfo ? getDivision(contestInfo.name) : "—"}</Badge>
                <div className="h-4 w-px bg-border/70" />
                <span>
                  Дата завершения:{" "}
                  {contestInfo
                    ? new Date((contestInfo.startTimeSeconds + contestInfo.durationSeconds) * 1000).toLocaleDateString(
                        "ru-RU",
                      )
                    : "—"}
                </span>
                <div className="h-4 w-px bg-border/70" />
                <span>Средний рейтинг: {averageRating || "—"}</span>
              </div>
            </div>
            <div className="flex flex-col gap-4 pt-4">
              <div className="flex flex-wrap gap-3">
                <Select value={sortOrder} onValueChange={(value: "asc" | "desc") => setSortOrder(value)}>
                  <SelectTrigger className="w-[200px] font-bold">
                    <SelectValue placeholder="Сортировка" />
                  </SelectTrigger>
                  <SelectContent className="bg-card font-bold">
                    <SelectItem value="asc">По возрастанию</SelectItem>
                    <SelectItem value="desc">По убыванию</SelectItem>
                  </SelectContent>
                </Select>

                <Select value={tagFilter} onValueChange={setTagFilter}>
                  <SelectTrigger className="w-[200px] font-bold">
                    <SelectValue placeholder="Тег" />
                  </SelectTrigger>
                  <SelectContent className="bg-card font-bold">
                    <SelectItem value="all">Все теги</SelectItem>
                    {uniqueTags.map((tag) => (
                      <SelectItem key={tag} value={tag}>
                        {tag}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex h-[calc(100vh-400px)] items-center justify-center">
                <p className="text-muted-foreground">Загрузка задач...</p>
              </div>
            ) : (
              <ScrollArea className="h-[calc(100vh-400px)] w-full pr-6">
                <div className="flex flex-col gap-3">
                  {filteredAndSortedTasks.map((task) => (
                    <div key={`${task.contestId}-${task.index}`} className="flex items-center gap-3">
                      <Link
                        href={`/task/${task.contestId}-${task.index}?from=contest&contestId=${id}`}
                        className="flex-1"
                      >
                        <div className="flex items-center justify-between rounded-lg border border-border/50 bg-secondary/30 p-4 transition-colors hover:bg-secondary/50">
                          <div className="flex items-center gap-4 flex-1 min-w-0">
                            <span className="text-sm shrink-0 font-bold">
                              {task.contestId}-{task.index}
                            </span>
                            <div className="h-6 w-px bg-border/70" />
                            <h3 className="font-medium truncate">{task.name}</h3>
                          </div>

                          <div className="flex items-center gap-4 shrink-0 w-[450px] justify-end">
                            <span className={`font-bold min-w-[9rem] text-center ${getDifficultyColor(task.rating)}`}>
                              {getDifficultyLabel(task.rating)}
                            </span>
                            <div className="h-6 w-px bg-border/70" />
                            <span className="font-semibold min-w-[3rem] text-center">{task.rating || "—"}</span>
                            <div className="h-6 w-px bg-border/70" />
                            <div className="flex-1 max-w-[300px] flex justify-center">
                              <Badge variant="outline" className="justify-center truncate max-w-full">
                                {task.tags[0] || "Без темы"}
                              </Badge>
                            </div>
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
