"use client"

import type React from "react"

import { Card, CardContent } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ScrollBar } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Search, ChevronDown, ChevronUp, Trophy, GitCompare, Loader2 } from "lucide-react"
import Link from "next/link"
import { useEffect, useState, useMemo, useRef, useCallback } from "react"

interface UserProfile {
  handle: string
  rating?: number
  rank?: string
  contribution?: number
  maxRating?: number
  maxRank?: string
  country?: string
  organization?: string
}

function getRankColor(rank?: string): string {
  if (!rank) return "#808080"

  const rankLower = rank.toLowerCase()
  if (rankLower.includes("легендарный гроссмейстер") || rankLower.includes("legendary grandmaster")) return "#aa0000"
  if (rankLower.includes("международный гроссмейстер") || rankLower.includes("international grandmaster"))
    return "#ff0000"
  if (rankLower.includes("гроссмейстер") || rankLower.includes("grandmaster")) return "#ff8c00"
  if (rankLower.includes("международный мастер") || rankLower.includes("international master")) return "#ff8c00"
  if (rankLower.includes("мастер") || rankLower.includes("master")) return "#ff8c00"
  if (rankLower.includes("кандидат в мастера") || rankLower.includes("candidate master")) return "#aa00aa"
  if (rankLower.includes("эксперт") || rankLower.includes("expert")) return "#0000ff"
  if (rankLower.includes("специалист") || rankLower.includes("specialist")) return "#03a89e"
  if (rankLower.includes("ученик") || rankLower.includes("pupil")) return "#008000"
  if (rankLower.includes("новобранец") || rankLower.includes("newbie")) return "#808080"
  return "#808080"
}

function getRankLabel(rank?: string): string {
  if (!rank) return "Без ранга"

  const rankLower = rank.toLowerCase()
  if (rankLower.includes("легендарный гроссмейстер") || rankLower.includes("legendary grandmaster"))
    return "Legendary Grandmaster"
  if (rankLower.includes("международный гроссмейстер") || rankLower.includes("international grandmaster"))
    return "International Grandmaster"
  if (rankLower.includes("гроссмейстер") || rankLower.includes("grandmaster")) return "Grandmaster"
  if (rankLower.includes("международный мастер") || rankLower.includes("international master"))
    return "International Master"
  if (rankLower.includes("мастер") || rankLower.includes("master")) return "Master"
  if (rankLower.includes("кандидат в мастера") || rankLower.includes("candidate master")) return "Candidate Master"
  if (rankLower.includes("эксперт") || rankLower.includes("expert")) return "Expert"
  if (rankLower.includes("специалист") || rankLower.includes("specialist")) return "Specialist"
  if (rankLower.includes("ученик") || rankLower.includes("pupil")) return "Pupil"
  if (rankLower.includes("новобранец") || rankLower.includes("newbie")) return "Newbie"
  return rank
}

function getContributionColor(contribution?: number): string {
  if (!contribution) return "#808080" // серый для 0 или undefined
  if (contribution > 0) return "#10b981" // зеленый для положительного
  if (contribution < 0) return "#ef4444" // красный для отрицательного
  return "#808080" // серый для 0
}

function formatContribution(contribution?: number): string {
  if (!contribution) return "0"
  if (contribution > 0) return `+${contribution}`
  return contribution.toString()
}

// Демо данные на случай если API не работает
const demoUsers: UserProfile[] = [
  {
    handle: "tourist",
    rating: 3858,
    rank: "legendary grandmaster",
    contribution: 0,
    maxRating: 4009,
    maxRank: "legendary grandmaster",
    country: "Belarus",
    organization: "ITMO University",
  },
  {
    handle: "Benq",
    rating: 3738,
    rank: "legendary grandmaster",
    contribution: 0,
    maxRating: 3833,
    maxRank: "legendary grandmaster",
    country: "United States",
    organization: "MIT",
  },
  {
    handle: "jiangly",
    rating: 3705,
    rank: "legendary grandmaster",
    contribution: 0,
    maxRating: 4039,
    maxRank: "legendary grandmaster",
    country: "China",
    organization: "Jiangly Fan Club",
  },
  {
    handle: "Um_nik",
    rating: 3189,
    rank: "grandmaster",
    contribution: 45,
    maxRating: 3289,
    maxRank: "grandmaster",
    country: "Russia",
    organization: "University of Warsaw",
  },
  {
    handle: "Errichto",
    rating: 3156,
    rank: "grandmaster",
    contribution: 189,
    maxRating: 3256,
    maxRank: "grandmaster",
    country: "Poland",
    organization: "Google",
  },
  {
    handle: "SecondThread",
    rating: 3123,
    rank: "grandmaster",
    contribution: 78,
    maxRating: 3199,
    maxRank: "grandmaster",
    country: "United States",
    organization: "MIT",
  },
]

export default function ProfilesPage() {
  const [users, setUsers] = useState<UserProfile[]>(demoUsers)
  const [loading, setLoading] = useState(false) // Start with demo data, no loading
  const [searchQuery, setSearchQuery] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [sortBy, setSortBy] = useState<"rating" | "alphabetical" | "contribution">("rating")
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc")
  const [rankFilter, setRankFilter] = useState<string>("all")
  const [apiFailed, setApiFailed] = useState(false)

  // Состояния для выпадающих меню
  const [showSortMenu, setShowSortMenu] = useState(false)
  const [showRankMenu, setShowRankMenu] = useState(false)

  // Рефы для отслеживания кликов вне меню
  const sortRef = useRef<HTMLDivElement>(null)
  const rankRef = useRef<HTMLDivElement>(null)

  // Debounce для поиска
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchQuery)
    }, 150)

    return () => {
      clearTimeout(handler)
    }
  }, [searchQuery])

  // Загрузка пользователей с Codeforces
  useEffect(() => {
    async function fetchUsers() {
      try {
        setLoading(true)
        setApiFailed(false)
        console.log("Начинаем загрузку пользователей с Codeforces...")

        const apiUrl = "https://codeforces.com/api/user.ratedList?activeOnly=true"

        const response = await fetch(apiUrl, {
          signal: AbortSignal.timeout(10000), // 10 second timeout
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()
        console.log("Получены данные от Codeforces, статус:", data.status)

        if (data.status === "OK") {
          console.log(`Всего пользователей в ответе: ${data.result.length}`)

          // Ограничиваем количество для производительности, как в контестах
          const topUsers = data.result
            .filter((user: any) => user.rating && user.rank)
            .slice(0, 200) // Берем только топ 200 как в контестах
            .map((user: any) => ({
              handle: user.handle,
              rating: user.rating,
              rank: user.rank,
              contribution: user.contribution,
              maxRating: user.maxRating,
              maxRank: user.maxRank,
              country: user.country,
              organization: user.organization,
            }))

          console.log(`Загружено ${topUsers.length} пользователей с рейтингом`)
          setUsers(topUsers)
        } else {
          // Keep demo data on API error
          setApiFailed(true)
        }
      } catch (error) {
        // Silently fail and keep demo data
        setApiFailed(true)
      } finally {
        setLoading(false)
      }
    }

    fetchUsers()
  }, [])

  // Мемоизированные уникальные ранги
  const uniqueRanks = useMemo(() => {
    const ranks = new Set<string>()
    users.forEach((user) => {
      if (user.rank) {
        ranks.add(user.rank.toLowerCase())
      }
    })
    return Array.from(ranks).sort()
  }, [users])

  // Оптимизированная фильтрация и сортировка
  const filteredAndSortedUsers = useMemo(() => {
    let result = [...users]

    // Search filter
    if (debouncedSearch) {
      const query = debouncedSearch.toLowerCase()
      result = result.filter((user) => {
        const userName = user.handle.toLowerCase()
        const userOrg = user.organization?.toLowerCase() || ""
        const userCountry = user.country?.toLowerCase() || ""
        return userName.includes(query) || userOrg.includes(query) || userCountry.includes(query)
      })
    }

    // Rank filter
    if (rankFilter !== "all") {
      result = result.filter((user) => {
        if (!user.rank) return false
        return user.rank.toLowerCase() === rankFilter.toLowerCase()
      })
    }

    // Sorting
    if (sortBy === "rating") {
      result.sort((a, b) => {
        const ratingA = a.rating || 0
        const ratingB = b.rating || 0
        return sortOrder === "desc" ? ratingB - ratingA : ratingA - ratingB
      })
    } else if (sortBy === "alphabetical") {
      result.sort((a, b) => {
        const nameA = a.handle.toLowerCase()
        const nameB = b.handle.toLowerCase()
        const comparison = nameA.localeCompare(nameB)
        return sortOrder === "desc" ? -comparison : comparison
      })
    } else if (sortBy === "contribution") {
      result.sort((a, b) => {
        const contribA = a.contribution || 0
        const contribB = b.contribution || 0
        return sortOrder === "desc" ? contribB - contribA : contribA - contribB
      })
    }

    return result
  }, [users, debouncedSearch, sortBy, sortOrder, rankFilter])

  // Получаем отображаемый текст для фильтров
  const getSortText = useCallback(() => {
    if (sortBy === "rating") return "По рейтингу"
    if (sortBy === "alphabetical") return "По алфавиту"
    return "По вкладу"
  }, [sortBy])

  const getRankText = useCallback(() => {
    if (rankFilter === "all") return "Звание"
    return getRankLabel(rankFilter)
  }, [rankFilter])

  // Закрываем все выпадающие меню при клике вне их
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (sortRef.current && !sortRef.current.contains(event.target as Node)) {
        setShowSortMenu(false)
      }
      if (rankRef.current && !rankRef.current.contains(event.target as Node)) {
        setShowRankMenu(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  // Функции для переключения меню
  const toggleSortMenu = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    setShowSortMenu((prev) => !prev)
    setShowRankMenu(false)
  }, [])

  const toggleRankMenu = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    setShowRankMenu((prev) => !prev)
    setShowSortMenu(false)
  }, [])

  // Функции для выбора пунктов меню
  const selectSortOption = useCallback((value: "rating" | "alphabetical" | "contribution") => {
    setSortBy(value)
    setShowSortMenu(false)
  }, [])

  const selectRankOption = useCallback((value: string) => {
    setRankFilter(value)
    setShowRankMenu(false)
  }, [])

  // Функция для очистки фильтра ранга
  const clearRankFilter = useCallback(() => {
    setRankFilter("all")
  }, [])

  // Функция для обработки поиска
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value)
  }, [])

  // Функция для переключения порядка сортировки
  const toggleSortOrder = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    setSortOrder((prev) => (prev === "desc" ? "asc" : "desc"))
  }, [])

  return (
    <>
      <style jsx global>{`
        /* Убираем все обводки и тени у фокусируемых элементов */
        *:focus,
        *:focus-visible,
        *:focus-within {
          outline: none !important;
          box-shadow: none !important;
          border-color: transparent !important;
        }
        
        /* Стили для текстовых фильтров */
        .text-filter {
          position: relative;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 10px 20px;
          font-size: 16px;
          font-weight: 500;
          color: hsl(var(--foreground));
          cursor: pointer;
          user-select: none;
          transition: all 0.15s ease;
          background: transparent;
          border: none;
          border-radius: 8px;
        }
        
        .text-filter:hover {
          color: hsl(var(--primary));
          background: rgba(0, 0, 0, 0.05);
        }
        
        .dark .text-filter:hover {
          background: rgba(255, 255, 255, 0.05);
        }
        
        .text-filter.active {
          color: hsl(var(--primary));
        }
        
        /* Выпадающее меню */
        .dropdown-menu {
          position: absolute;
          top: 100%;
          left: 0;
          z-index: 50;
          margin-top: 4px;
          border-radius: 8px;
          background-color: rgba(var(--card-rgb), 0.95);
          backdrop-filter: blur(12px);
          border: 1px solid rgba(var(--border-rgb), 0.3);
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
          animation: fadeIn 0.15s ease-out;
          transform-origin: top center;
          min-width: 180px;
        }
        
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(-10px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
        
        .dark .dropdown-menu {
          background-color: rgba(var(--card-rgb), 0.95);
          border-color: rgba(var(--border-rgb), 0.3);
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
        }
        
        .menu-item {
          width: 100%;
          padding: 10px 16px;
          text-align: left;
          font-size: 14px;
          color: hsl(var(--foreground));
          cursor: pointer;
          transition: all 0.15s ease;
          border: none;
          background: transparent;
        }
        
        .menu-item:hover {
          background-color: rgba(var(--accent-rgb), 0.2);
        }
        
        .menu-item.active {
          background-color: rgba(var(--accent-rgb), 0.3);
          color: hsl(var(--accent-foreground));
          font-weight: 500;
        }
        
        /* Иконка стрелки */
        .chevron-icon {
          transition: transform 0.15s ease;
        }
        
        .chevron-icon.open {
          transform: rotate(180deg);
        }
      `}</style>

      <div className="min-h-screen bg-background p-6">
        <div className="mx-auto max-w-[1800px] space-y-8">
          {/* Заголовок */}
          <h1 className="text-4xl font-bold text-center tracking-tight">Список профилей</h1>

          {/* Поисковая строка */}
          <div className="relative">
            <Search className="absolute left-6 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground z-10" />
            <Input
              placeholder="Поиск"
              value={searchQuery}
              onChange={handleSearchChange}
              className="pl-14 h-14 text-lg rounded-xl border-border/50 bg-card/50 backdrop-blur-sm w-full"
            />
          </div>

          {/* Фильтры */}
          <div className="flex flex-wrap items-center justify-center gap-8">
            {/* Выбор типа сортировки */}
            <div className="relative" ref={sortRef}>
              <button className={`text-filter ${showSortMenu ? "active" : ""}`} onClick={toggleSortMenu}>
                {sortBy === "rating" ? (
                  <Trophy className="h-4 w-4" />
                ) : sortBy === "alphabetical" ? (
                  <GitCompare className="h-4 w-4" />
                ) : (
                  <GitCompare className="h-4 w-4" />
                )}
                {getSortText()}
                <ChevronDown className={`h-4 w-4 chevron-icon ${showSortMenu ? "open" : ""}`} />
              </button>

              {showSortMenu && (
                <div className="dropdown-menu">
                  <button
                    className={`menu-item rounded flex items-center gap-2 ${sortBy === "rating" ? "active" : ""}`}
                    onClick={() => selectSortOption("rating")}
                  >
                    <Trophy className="h-4 w-4" />
                    По рейтингу
                  </button>
                  <button
                    className={`menu-item rounded flex items-center gap-2 ${sortBy === "alphabetical" ? "active" : ""}`}
                    onClick={() => selectSortOption("alphabetical")}
                  >
                    <GitCompare className="h-4 w-4" />
                    По алфавиту
                  </button>
                  <button
                    className={`menu-item rounded flex items-center gap-2 ${sortBy === "contribution" ? "active" : ""}`}
                    onClick={() => selectSortOption("contribution")}
                  >
                    <GitCompare className="h-4 w-4" />
                    По вкладу
                  </button>
                </div>
              )}
            </div>

            {/* Переключатель порядка сортировки */}
            <button
              className="text-filter"
              onClick={toggleSortOrder}
              title={sortOrder === "desc" ? "По убыванию" : "По возрастанию"}
            >
              <GitCompare className="h-4 w-4" />
              {sortOrder === "desc" ? "По убыванию" : "По возрастанию"}
              {sortOrder === "desc" ? (
                <ChevronDown className="h-4 w-4 text-red-500" />
              ) : (
                <ChevronUp className="h-4 w-4 text-green-500" />
              )}
            </button>

            {/* Фильтр по званию */}
            <div className="relative" ref={rankRef}>
              <div className="flex items-center gap-2">
                <button className={`text-filter ${showRankMenu ? "active" : ""}`} onClick={toggleRankMenu}>
                  {getRankText()}
                  <ChevronDown className={`h-4 w-4 chevron-icon ${showRankMenu ? "open" : ""}`} />
                </button>
                {rankFilter !== "all" && (
                  <button
                    onClick={clearRankFilter}
                    className="text-xs px-2 py-1 rounded bg-red-500/20 text-red-600 hover:bg-red-500/30 transition-colors"
                    title="Очистить фильтр"
                  >
                    ×
                  </button>
                )}
              </div>

              {showRankMenu && (
                <div className="dropdown-menu" style={{ maxHeight: "400px" }}>
                  <ScrollArea className="h-[300px]">
                    <div className="p-1">
                      <button
                        className={`menu-item rounded ${rankFilter === "all" ? "active" : ""}`}
                        onClick={() => selectRankOption("all")}
                      >
                        Все звания
                      </button>
                      {uniqueRanks.map((rank) => (
                        <button
                          key={rank}
                          className={`menu-item rounded flex items-center gap-2 ${rankFilter === rank ? "active" : ""}`}
                          onClick={() => selectRankOption(rank)}
                        >
                          <div className="h-3 w-3 rounded-full" style={{ backgroundColor: getRankColor(rank) }} />
                          {getRankLabel(rank)}
                        </button>
                      ))}
                    </div>
                    <ScrollBar orientation="vertical" />
                  </ScrollArea>
                </div>
              )}
            </div>
          </div>

          {/* Уведомление об ошибке */}
          {apiFailed && !loading && (
            <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-4">
              <p className="text-center text-yellow-600 dark:text-yellow-400">
                Не удалось загрузить данные с Codeforces API. Используются демо данные.
              </p>
            </div>
          )}

          {/* Список профилей */}
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardContent className="pt-6">
              {loading ? (
                <div className="flex h-[calc(100vh-450px)] flex-col items-center justify-center gap-4">
                  <Loader2 className="h-12 w-12 animate-spin text-primary" />
                  <div className="text-center">
                    <p className="text-xl font-semibold text-muted-foreground">Загрузка профилей...</p>
                    <p className="text-sm text-muted-foreground mt-2">Получаем данные пользователей с Codeforces</p>
                  </div>
                </div>
              ) : users.length === 0 ? (
                <div className="flex h-[calc(100vh-450px)] flex-col items-center justify-center gap-4">
                  <p className="text-muted-foreground">Нет данных для отображения</p>
                  {apiFailed && (
                    <button
                      onClick={() => window.location.reload()}
                      className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                    >
                      Обновить страницу
                    </button>
                  )}
                </div>
              ) : (
                <ScrollArea className="h-[calc(100vh-450px)] w-full">
                  <div className="flex flex-col gap-3 pr-6">
                    {filteredAndSortedUsers.map((user) => {
                      const currentRankColor = getRankColor(user.rank)
                      const maxRankColor = getRankColor(user.maxRank || user.rank)
                      const ratingDiff = user.maxRating && user.rating ? user.maxRating - user.rating : 0

                      return (
                        <Link key={user.handle} href={`/profile/${user.handle}`} prefetch={false}>
                          <div className="flex items-center justify-between rounded-lg border border-border/50 bg-secondary/30 p-4 transition-colors hover:bg-secondary/50">
                            {/* Левая часть: никнейм и звание */}
                            <div className="flex items-center gap-4 flex-1 min-w-0">
                              <span className="font-bold text-xl truncate" style={{ color: currentRankColor }}>
                                {user.handle}
                              </span>
                              <div className="h-8 w-px bg-border/70" />
                              <Badge
                                variant="outline"
                                className="truncate max-w-[200px] py-1 px-3"
                                style={{
                                  color: currentRankColor,
                                  borderColor: currentRankColor,
                                }}
                              >
                                {getRankLabel(user.rank)}
                              </Badge>

                              {/* Дополнительная информация: страна/организация */}
                              {(user.country || user.organization) && (
                                <>
                                  <div className="h-8 w-px bg-border/70" />
                                  <div className="flex flex-col text-xs text-muted-foreground truncate max-w-[200px]">
                                    {user.country && <span>{user.country}</span>}
                                    {user.organization && <span className="truncate">{user.organization}</span>}
                                  </div>
                                </>
                              )}
                            </div>

                            {/* Правая часть: рейтинг, вклад */}
                            <div className="flex items-center gap-4 shrink-0">
                              {/* Текущий рейтинг + макс рейтинг */}
                              <div className="flex flex-col items-center justify-center min-w-[10rem]">
                                <div className="flex items-baseline gap-1">
                                  <span className="font-bold text-2xl" style={{ color: currentRankColor }}>
                                    {user.rating || "—"}
                                  </span>
                                  {user.maxRating && user.maxRating > (user.rating || 0) && (
                                    <span className="flex items-baseline gap-1">
                                      <span className="text-gray-500">(</span>
                                      <span className="font-bold text-lg" style={{ color: maxRankColor }}>
                                        {user.maxRating}
                                      </span>
                                      {ratingDiff > 0 && (
                                        <span className="text-sm font-semibold ml-1" style={{ color: maxRankColor }}>
                                          +{ratingDiff}
                                        </span>
                                      )}
                                      <span className="text-gray-500">)</span>
                                    </span>
                                  )}
                                </div>
                              </div>

                              <div className="h-8 w-px bg-border/70" />

                              {/* Вклад */}
                              <div className="flex flex-col items-center justify-center min-w-[6rem]">
                                <span
                                  className="font-bold text-2xl"
                                  style={{ color: getContributionColor(user.contribution) }}
                                >
                                  {formatContribution(user.contribution)}
                                </span>
                              </div>
                            </div>
                          </div>
                        </Link>
                      )
                    })}
                  </div>
                  <ScrollBar orientation="vertical" />
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  )
}
