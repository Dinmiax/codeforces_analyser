"use client"

export default async function ProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const { id: handle } = await params

  return <ProfilePageClient handle={handle} />
}

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Target, Lightbulb, ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ChartSection } from "@/components/chart-section"

function getRankColor(rank: string): string {
  const rankLower = rank.toLowerCase()
  if (rankLower.includes("легендарный гроссмейстер")) return "#aa0000"
  if (rankLower.includes("международный гроссмейстер")) return "#ff0000"
  if (rankLower.includes("гроссмейстер")) return "#ff8c00"
  if (rankLower.includes("международный мастер")) return "#ff8c00"
  if (rankLower.includes("мастер")) return "#ff8c00"
  if (rankLower.includes("кандидат в мастера")) return "#aa00aa"
  if (rankLower.includes("эксперт")) return "#0000ff"
  if (rankLower.includes("специалист")) return "#03a89e"
  if (rankLower.includes("ученик")) return "#008000"
  return "#808080"
}

const demoData = {
  handle: "tourist",
  rating: 3858,
  rank: "легендарный гроссмейстер",
  maxRating: 3979,
  currentRank: 1,
  problemsSolved: 1247,
  contestParticipations: 234,
  contribution: 156,
  friendsCount: 892,
  weakAreas: ["Динамическое программирование", "Графы", "Геометрия"],
  goals: [
    { name: "Рейтинг 4000", progress: 96, current: 3858, target: 4000 },
    { name: "Решить 1500 задач", progress: 83, current: 1247, target: 1500 },
    { name: "Участие в 250 контестах", progress: 93, current: 234, target: 250 },
  ],
  recentProblems: [
    { id: 1, name: "A. Beautiful Matrix", rating: 800, date: "2 часа назад" },
    { id: 2, name: "B. Two Buttons", rating: 1400, date: "1 день назад" },
    { id: 3, name: "C. Number of Ways", rating: 1700, date: "2 дня назад" },
  ],
  recommendations: [
    "Практикуйте задачи на динамическое программирование уровня 2800-3000",
    "Участвуйте в еженедельных контестах для поддержания формы",
    "Разберите темы: деревья отрезков и система непересекающихся множеств",
  ],
  submissionCalendar: generateDemoSubmissions(),
}

function generateDemoSubmissions() {
  const submissions: Record<string, number> = {}
  const now = new Date()
  for (let i = 0; i < 365; i++) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    const dateStr = date.toISOString().split("T")[0]
    submissions[dateStr] = Math.floor(Math.random() * 15)
  }
  return submissions
}

function ProfilePageClient({ handle }: { handle: string }) {
  const [userData, setUserData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear())
  const [currentMonth, setCurrentMonth] = useState(new Date().getMonth())

  useEffect(() => {
    async function fetchUserData() {
      if (handle === "0") {
        setUserData(demoData)
        setLoading(false)
      } else {
        try {
          const [userResponse, submissionsResponse] = await Promise.all([
            fetch(`https://codeforces.com/api/user.info?handles=${handle}`),
            fetch(`https://codeforces.com/api/user.status?handle=${handle}&from=1&count=10000`),
          ])

          const userData = await userResponse.json()
          const submissionsData = await submissionsResponse.json()

          if (userData.status === "OK" && userData.result.length > 0) {
            const cfUser = userData.result[0]

            const solvedProblems = new Set()
            const submissionCalendar: Record<string, number> = {}
            const recentProblems: any[] = []

            if (submissionsData.status === "OK") {
              submissionsData.result.forEach((submission: any) => {
                if (submission.verdict === "OK") {
                  const problemId = `${submission.problem.contestId}-${submission.problem.index}`

                  if (!solvedProblems.has(problemId) && recentProblems.length < 3) {
                    recentProblems.push({
                      id: submission.problem.contestId + submission.problem.index,
                      name: `${submission.problem.contestId}-${submission.problem.index}. ${submission.problem.name}`,
                      rating: submission.problem.rating || 0,
                      date: new Date(submission.creationTimeSeconds * 1000).toLocaleDateString("ru-RU"),
                    })
                  }

                  solvedProblems.add(problemId)

                  const date = new Date(submission.creationTimeSeconds * 1000)
                  const dateStr = date.toISOString().split("T")[0]
                  submissionCalendar[dateStr] = (submissionCalendar[dateStr] || 0) + 1
                }
              })
            }

            const ratingResponse = await fetch(`https://codeforces.com/api/user.rating?handle=${handle}`)
            const ratingData = await ratingResponse.json()

            let maxRating = cfUser.rating || 0
            let contestCount = 0
            if (ratingData.status === "OK") {
              contestCount = ratingData.result.length
              maxRating = Math.max(cfUser.rating || 0, ...ratingData.result.map((r: any) => r.newRating))
            }

            const currentRank = cfUser.rank || "Newbie"
            const currentRating = cfUser.rating || 0

            setUserData({
              handle: cfUser.handle,
              rating: currentRating,
              rank: currentRank,
              maxRating: maxRating,
              currentRank: cfUser.rating ? 1 : 0,
              problemsSolved: solvedProblems.size,
              contestParticipations: contestCount,
              contribution: cfUser.contribution || 0,
              friendsCount: cfUser.friendOfCount || 0,
              weakAreas: ["Динамическое программирование", "Графы"],
              goals: [
                {
                  name: "Рейтинг выше",
                  progress: Math.min(100, (currentRating / (currentRating + 200)) * 100),
                  current: currentRating,
                  target: currentRating + 200,
                },
                {
                  name: "Решить больше задач",
                  progress: Math.min(100, (solvedProblems.size / (solvedProblems.size + 100)) * 100),
                  current: solvedProblems.size,
                  target: solvedProblems.size + 100,
                },
                {
                  name: "Участие в контестах",
                  progress: Math.min(100, (contestCount / (contestCount + 10)) * 100),
                  current: contestCount,
                  target: contestCount + 10,
                },
              ],
              recentProblems,
              recommendations: [
                "Участвуйте в контестах регулярно",
                "Решайте задачи вашего уровня",
                "Практикуйте слабые темы",
              ],
              submissionCalendar,
            })
          } else {
            throw new Error("User not found")
          }
        } catch (error) {
          console.error("Failed to fetch user data:", error)
          setUserData(null)
        } finally {
          setLoading(false)
        }
      }
    }

    fetchUserData()
  }, [handle])

  const getDaysInMonth = (year: number, month: number) => new Date(year, month + 1, 0).getDate()
  const getFirstDayOfMonth = (year: number, month: number) => {
    const day = new Date(year, month, 1).getDay()
    return day === 0 ? 6 : day - 1 // Convert Sunday (0) to 6, others shift by -1
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-6 lg:p-12">
        <div className="mx-auto max-w-7xl">
          <Card className="border-0 bg-card/50">
            <CardContent className="p-12 text-center">
              <div className="text-lg text-muted-foreground">Загрузка данных профиля...</div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  if (!userData) {
    return (
      <div className="min-h-screen bg-background p-6 lg:p-12">
        <div className="mx-auto max-w-7xl">
          <Card className="border-0 bg-card/50">
            <CardContent className="p-12 text-center">
              <div className="text-lg text-foreground mb-2">Пользователь не найден</div>
              <div className="text-muted-foreground">Пользователь с хендлом "{handle}" не найден на Codeforces</div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  const daysInMonth = getDaysInMonth(currentYear, currentMonth)
  const firstDay = getFirstDayOfMonth(currentYear, currentMonth)
  const monthNames = [
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
  ]

  const calendarDays = []
  for (let i = 0; i < firstDay; i++) {
    calendarDays.push(null)
  }
  for (let day = 1; day <= daysInMonth; day++) {
    calendarDays.push(day)
  }

  const getSubmissionCount = (day: number) => {
    const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`
    return userData.submissionCalendar?.[dateStr] || 0
  }

  const getColorForCount = (count: number) => {
    if (count === 0) return "bg-muted/30"
    if (count <= 2) return "bg-[#0e4429]"
    if (count <= 5) return "bg-[#006d32]"
    if (count <= 10) return "bg-[#26a641]"
    return "bg-[#39d353]"
  }

  const handlePrevMonth = () => {
    if (currentMonth === 0) {
      setCurrentMonth(11)
      setCurrentYear(currentYear - 1)
    } else {
      setCurrentMonth(currentMonth - 1)
    }
  }

  const handleNextMonth = () => {
    const now = new Date()
    if (currentYear === now.getFullYear() && currentMonth === now.getMonth()) return

    if (currentMonth === 11) {
      setCurrentMonth(0)
      setCurrentYear(currentYear + 1)
    } else {
      setCurrentMonth(currentMonth + 1)
    }
  }

  return (
    <div className="min-h-screen bg-background p-6 lg:p-12">
      <div className="mx-auto max-w-7xl space-y-8">
        <div className="flex items-center justify-between p-6 bg-card/50 rounded-lg">
          <div className="flex-1 mr-8">
            <h1 className="text-3xl font-bold text-foreground">{userData.handle}</h1>
            <div className="flex items-center gap-4 mt-2">
              <Badge
                variant="outline"
                style={{ color: getRankColor(userData.rank), borderColor: getRankColor(userData.rank) }}
              >
                {userData.rank}
              </Badge>
              <span className="text-muted-foreground">Рейтинг: {userData.rating}</span>
              <span className="text-muted-foreground">Макс: {userData.maxRating}</span>
              <span className="text-muted-foreground">Ранг: #{userData.currentRank}</span>
            </div>
          </div>
          <div className="flex gap-8 text-center">
            <div>
              <div className="text-2xl font-bold text-foreground">{userData.problemsSolved}</div>
              <div className="text-sm text-muted-foreground">Задач решено</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-foreground">{userData.contestParticipations}</div>
              <div className="text-sm text-muted-foreground">Контестов</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-foreground">{userData.contribution}</div>
              <div className="text-sm text-muted-foreground">Вклад</div>
            </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            {/* Мои цели - первый блок */}
            <Card className="border-0 bg-card/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Мои цели
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {userData.goals.map((goal: any, index: number) => (
                  <div key={index} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium">{goal.name}</span>
                      <span className="text-muted-foreground">
                        {goal.current} / {goal.target}
                      </span>
                    </div>
                    <Progress value={goal.progress} className="h-2" />
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Чарт - второй блок */}
            <ChartSection />

            {/* Недавно решенные задачи - третий блок */}
            <Card className="border-0 bg-card/50">
              <CardHeader>
                <CardTitle>Недавно решенные задачи</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {userData.recentProblems.map((problem: any) => (
                  <div key={problem.id} className="flex justify-between items-center p-3 rounded-lg bg-card/50">
                    <div>
                      <div className="font-medium text-foreground">{problem.name}</div>
                      <div className="text-sm text-muted-foreground">{problem.date}</div>
                    </div>
                    <Badge variant="outline">★ {problem.rating}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="border-0 bg-card/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>История решений</CardTitle>
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="icon" onClick={handlePrevMonth}>
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-sm font-medium min-w-[140px] text-center">
                      {monthNames[currentMonth]} {currentYear}
                    </span>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={handleNextMonth}
                      disabled={currentYear === new Date().getFullYear() && currentMonth === new Date().getMonth()}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-7 gap-1">
                  {["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"].map((day) => (
                    <div key={day} className="text-xs text-center text-muted-foreground py-1">
                      {day}
                    </div>
                  ))}
                  {calendarDays.map((day, index) => {
                    if (day === null) {
                      return <div key={`empty-${index}`} className="aspect-square" />
                    }
                    const count = getSubmissionCount(day)
                    return (
                      <div
                        key={day}
                        className={`aspect-square rounded ${getColorForCount(count)} flex items-center justify-center text-xs font-medium relative group cursor-pointer`}
                        title={`${day} ${monthNames[currentMonth]}: ${count} задач`}
                      >
                        <span className="text-white/80">{count > 0 ? count : ""}</span>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>

            <Card className="border-0 bg-card/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="h-5 w-5" />
                  Рекомендации
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {userData.recommendations.map((rec: string, index: number) => (
                  <div key={index} className="flex items-start gap-2 text-sm">
                    <div className="h-2 w-2 rounded-full bg-[#06b6d4] mt-1.5 flex-shrink-0" />
                    <span className="text-muted-foreground">{rec}</span>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="border-0 bg-card/50">
              <CardHeader>
                <CardTitle>Области для улучшения</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {userData.weakAreas.map((area: string, index: number) => (
                    <Badge key={index} variant="secondary" className="px-3 py-1">
                      {area}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
