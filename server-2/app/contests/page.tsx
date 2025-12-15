"use client"

import { Card, CardContent } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ScrollBar } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Search, ChevronDown, ChevronUp, Calendar, Users, ArrowUpDown } from "lucide-react"
import Link from "next/link"
import { useEffect, useState, useMemo, useRef, useCallback } from "react"

interface CodeforcesContest {
  id: number
  name: string
  type: string
  phase: string
  durationSeconds: number
  startTimeSeconds: number
}

function getDivision(name: string): string {
  if (name.includes("Div. 1")) return "Div. 1"
  if (name.includes("Div. 2")) return "Div. 2"
  if (name.includes("Div. 3")) return "Div. 3"
  if (name.includes("Div. 4")) return "Div. 4"
  return "Other"
}

function formatDate(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric"
  })
}

export default function ContestsPage() {
  const [contests, setContests] = useState<CodeforcesContest[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [sortBy, setSortBy] = useState<"date" | "division">("date")
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc")
  const [divisionFilter, setDivisionFilter] = useState<string>("all")
  
  // Состояния для выпадающих меню
  const [showSortMenu, setShowSortMenu] = useState(false)
  const [showDivisionMenu, setShowDivisionMenu] = useState(false)
  
  // Рефы для отслеживания кликов вне меню
  const sortRef = useRef<HTMLDivElement>(null)
  const divisionRef = useRef<HTMLDivElement>(null)

  // Debounce для поиска
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchQuery)
    }, 150)

    return () => {
      clearTimeout(handler)
    }
  }, [searchQuery])

  // Загрузка контестов
  useEffect(() => {
    async function fetchContests() {
      try {
        const response = await fetch("https://codeforces.com/api/contest.list")
        const data = await response.json()
        if (data.status === "OK") {
          const finishedContests = data.result
            .filter((c: CodeforcesContest) => c.phase === "FINISHED")
            .slice(0, 100)
          setContests(finishedContests)
        }
      } catch (error) {
        console.error("Error fetching contests:", error)
      } finally {
        setLoading(false)
      }
    }
    fetchContests()
  }, [])

  // Оптимизированная фильтрация и сортировка
  const filteredAndSortedContests = useMemo(() => {
    let result = [...contests]

    // Search filter
    if (debouncedSearch) {
      const query = debouncedSearch.toLowerCase()
      result = result.filter((contest) => {
        const contestName = contest.name.toLowerCase()
        const contestId = contest.id.toString()
        return contestName.includes(query) || contestId.includes(query)
      })
    }

    // Division filter
    if (divisionFilter !== "all") {
      result = result.filter((contest) => getDivision(contest.name) === divisionFilter)
    }

    // Sorting
    if (sortBy === "date") {
      result.sort((a, b) => {
        return sortOrder === "desc" 
          ? b.startTimeSeconds - a.startTimeSeconds
          : a.startTimeSeconds - b.startTimeSeconds
      })
    } else {
      result.sort((a, b) => {
        const divA = getDivision(a.name)
        const divB = getDivision(b.name)
        const comparison = divA.localeCompare(divB)
        // ИСПРАВЛЕНО: ТОЛЬКО для дивизионов инвертируем логику
        return sortOrder === "desc" ? comparison : -comparison
      })
    }

    return result
  }, [contests, debouncedSearch, sortBy, sortOrder, divisionFilter])

  // Получаем отображаемый текст для фильтров
  const getSortText = useCallback(() => {
    return sortBy === "date" ? "По дате" : "По дивизиону"
  }, [sortBy])

  const getDivisionText = useCallback(() => {
    if (divisionFilter === "all") return "Дивизион"
    return divisionFilter
  }, [divisionFilter])

  // Закрываем все выпадающие меню при клике вне их
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (sortRef.current && !sortRef.current.contains(event.target as Node)) {
        setShowSortMenu(false)
      }
      if (divisionRef.current && !divisionRef.current.contains(event.target as Node)) {
        setShowDivisionMenu(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Функции для переключения меню
  const toggleSortMenu = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    setShowSortMenu(prev => !prev)
    setShowDivisionMenu(false)
  }, [])

  const toggleDivisionMenu = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    setShowDivisionMenu(prev => !prev)
    setShowSortMenu(false)
  }, [])

  // Функции для выбора пунктов меню
  const selectSortOption = useCallback((value: "date" | "division") => {
    setSortBy(value)
    setShowSortMenu(false)
  }, [])

  const selectDivisionOption = useCallback((value: string) => {
    setDivisionFilter(value)
    setShowDivisionMenu(false)
  }, [])

  // Функция для очистки фильтра дивизиона
  const clearDivisionFilter = useCallback(() => {
    setDivisionFilter("all")
  }, [])

  // Функция для обработки поиска
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value)
  }, [])

  // Функция для переключения порядка сортировки
  const toggleSortOrder = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    setSortOrder(prev => prev === "desc" ? "asc" : "desc")
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
          <h1 className="text-4xl font-bold text-center tracking-tight">Контесты</h1>

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
            {/* Выбор типа сортировки (дата/дивизион) */}
            <div className="relative" ref={sortRef}>
              <button 
                className={`text-filter ${showSortMenu ? 'active' : ''}`}
                onClick={toggleSortMenu}
              >
                {sortBy === "date" ? (
                  <Calendar className="h-4 w-4" />
                ) : (
                  <Users className="h-4 w-4" />
                )}
                {getSortText()}
                <ChevronDown className={`h-4 w-4 chevron-icon ${showSortMenu ? 'open' : ''}`} />
              </button>
              
              {showSortMenu && (
                <div className="dropdown-menu">
                  <button
                    className={`menu-item rounded flex items-center gap-2 ${sortBy === 'date' ? 'active' : ''}`}
                    onClick={() => selectSortOption('date')}
                  >
                    <Calendar className="h-4 w-4" />
                    По дате
                  </button>
                  <button
                    className={`menu-item rounded flex items-center gap-2 ${sortBy === 'division' ? 'active' : ''}`}
                    onClick={() => selectSortOption('division')}
                  >
                    <Users className="h-4 w-4" />
                    По дивизиону
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
              <ArrowUpDown className="h-4 w-4" />
              {sortOrder === "desc" ? "По убыванию" : "По возрастанию"}
              {sortOrder === "desc" ? (
                <ChevronDown className="h-4 w-4 text-red-500" />
              ) : (
                <ChevronUp className="h-4 w-4 text-green-500" />
              )}
            </button>

            {/* Фильтр по дивизиону */}
            <div className="relative" ref={divisionRef}>
              <div className="flex items-center gap-2">
                <button 
                  className={`text-filter ${showDivisionMenu ? 'active' : ''}`}
                  onClick={toggleDivisionMenu}
                >
                  {getDivisionText()}
                  <ChevronDown className={`h-4 w-4 chevron-icon ${showDivisionMenu ? 'open' : ''}`} />
                </button>
                {divisionFilter !== "all" && (
                  <button
                    onClick={clearDivisionFilter}
                    className="text-xs px-2 py-1 rounded bg-red-500/20 text-red-600 hover:bg-red-500/30 transition-colors"
                    title="Очистить фильтр"
                  >
                    ×
                  </button>
                )}
              </div>
              
              {showDivisionMenu && (
                <div className="dropdown-menu" style={{ maxHeight: '300px' }}>
                  <div className="p-1">
                    <button
                      className={`menu-item rounded ${divisionFilter === 'all' ? 'active' : ''}`}
                      onClick={() => selectDivisionOption('all')}
                    >
                      Все дивизионы
                    </button>
                    <button
                      className={`menu-item rounded ${divisionFilter === 'Div. 1' ? 'active' : ''}`}
                      onClick={() => selectDivisionOption('Div. 1')}
                    >
                      Div. 1
                    </button>
                    <button
                      className={`menu-item rounded ${divisionFilter === 'Div. 2' ? 'active' : ''}`}
                      onClick={() => selectDivisionOption('Div. 2')}
                    >
                      Div. 2
                    </button>
                    <button
                      className={`menu-item rounded ${divisionFilter === 'Div. 3' ? 'active' : ''}`}
                      onClick={() => selectDivisionOption('Div. 3')}
                    >
                      Div. 3
                    </button>
                    <button
                      className={`menu-item rounded ${divisionFilter === 'Div. 4' ? 'active' : ''}`}
                      onClick={() => selectDivisionOption('Div. 4')}
                    >
                      Div. 4
                    </button>
                    <button
                      className={`menu-item rounded ${divisionFilter === 'Other' ? 'active' : ''}`}
                      onClick={() => selectDivisionOption('Other')}
                    >
                      Другое
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Список контестов */}
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardContent className="pt-6">
              {loading ? (
                <div className="flex h-[calc(100vh-450px)] items-center justify-center">
                  <p className="text-muted-foreground">Загрузка контестов...</p>
                </div>
              ) : (
                <ScrollArea className="h-[calc(100vh-450px)] w-full">
                  <div className="flex flex-col gap-3 pr-6">
                    {filteredAndSortedContests.map((contest) => (
                      <Link 
                        key={contest.id} 
                        href={`/contest/${contest.id}`}
                        prefetch={false}
                      >
                        <div className="flex items-center justify-between rounded-lg border border-border/50 bg-secondary/30 p-4 transition-colors hover:bg-secondary/50">
                          <div className="flex items-center gap-4 flex-1 min-w-0">
                            <h3 className="font-medium truncate">{contest.name}</h3>
                          </div>

                          <div className="flex items-center gap-4 shrink-0">
                            <Badge variant="outline" className="min-w-[5rem] justify-center">
                              {getDivision(contest.name)}
                            </Badge>
                            <div className="h-6 w-px bg-border/70" />
                            <span className="text-sm text-muted-foreground min-w-[10rem] text-center">
                              {formatDate(contest.startTimeSeconds)}
                            </span>
                          </div>
                        </div>
                      </Link>
                    ))}
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
