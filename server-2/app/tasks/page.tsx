"use client"

import { Card, CardContent } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ScrollBar } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ExternalLink, Search, ChevronDown, ChevronUp, ArrowUpDown } from "lucide-react"
import Link from "next/link"
import { useEffect, useState, useMemo, useRef, useCallback } from "react"

interface CodeforcesTask {
  contestId: number
  index: string
  name: string
  rating?: number
  tags: string[]
}

function getDifficultyColor(rating?: number) {
  if (!rating) return "text-muted-foreground"
  if (rating <= 1000) return "text-[#00DD00]"
  if (rating <= 1400) return "text-[#a3e635]"
  if (rating <= 1900) return "text-[#eab308]"
  if (rating <= 2800) return "text-[#ef4444]"
  return "text-[#7f1d1d]"
}

function getDifficultyLabel(rating?: number) {
  if (!rating) return "Не указана"
  if (rating <= 1000) return "Очень легкая"
  if (rating <= 1400) return "Легкая"
  if (rating <= 1900) return "Средняя"
  if (rating <= 2800) return "Сложная"
  return "Очень сложная"
}

function getDifficultyCategory(rating?: number): string {
  if (!rating) return "none"
  if (rating <= 1000) return "very-easy"
  if (rating <= 1400) return "easy"
  if (rating <= 1900) return "medium"
  if (rating <= 2800) return "hard"
  return "very-hard"
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<CodeforcesTask[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc")
  const [difficultyFilter, setDifficultyFilter] = useState<string>("all")
  const [tagFilter, setTagFilter] = useState<string>("all")

  // Состояния для выпадающих меню
  const [showDifficultyMenu, setShowDifficultyMenu] = useState(false)
  const [showTagMenu, setShowTagMenu] = useState(false)

  // Рефы для отслеживания кликов вне меню
  const difficultyRef = useRef<HTMLDivElement>(null)
  const tagRef = useRef<HTMLDivElement>(null)

  // Debounce для поиска
  const [debouncedSearch, setDebouncedSearch] = useState("")
  
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchQuery)
    }, 150) // 150ms debounce

    return () => {
      clearTimeout(handler)
    }
  }, [searchQuery])

  // Загрузка задач
  useEffect(() => {
    async function fetchTasks() {
      try {
        const response = await fetch("https://codeforces.com/api/problemset.problems")
        const data = await response.json()
        if (data.status === "OK") {
          // Берем только задачи с рейтингом и ограничиваем количество для производительности
          const filteredTasks = data.result.problems
            .filter((p: CodeforcesTask) => p.rating)
            .slice(0, 150) // Уменьшил количество для производительности
          setTasks(filteredTasks)
        }
      } catch (error) {
        console.error("Error fetching tasks:", error)
      } finally {
        setLoading(false)
      }
    }
    fetchTasks()
  }, [])

  // Мемоизированные уникальные теги
  const uniqueTags = useMemo(() => {
    const tags = new Set<string>()
    tasks.forEach((task) => {
      task.tags.forEach((tag) => tags.add(tag))
    })
    return Array.from(tags).sort()
  }, [tasks])

  // Оптимизированная фильтрация и сортировка
  const filteredAndSortedTasks = useMemo(() => {
    let result = [...tasks]

    // Search filter
    if (debouncedSearch) {
      const query = debouncedSearch.toLowerCase()
      result = result.filter((task) => {
        const taskNumber = `${task.contestId}-${task.index}`.toLowerCase()
        const taskName = task.name.toLowerCase()
        const taskRating = task.rating?.toString() || ""
        return taskNumber.includes(query) || taskName.includes(query) || taskRating.includes(query)
      })
    }

    // Difficulty filter
    if (difficultyFilter !== "all") {
      result = result.filter((task) => getDifficultyCategory(task.rating) === difficultyFilter)
    }

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
  }, [tasks, debouncedSearch, sortOrder, difficultyFilter, tagFilter])

  // Получаем отображаемый текст для фильтров
  const getDifficultyText = useCallback(() => {
    if (difficultyFilter === "all") return "Сложность"
    if (difficultyFilter === "very-easy") return "Очень легкая"
    if (difficultyFilter === "easy") return "Легкая"
    if (difficultyFilter === "medium") return "Средняя"
    if (difficultyFilter === "hard") return "Сложная"
    return "Очень сложная"
  }, [difficultyFilter])

  const getTagText = useCallback(() => {
    if (tagFilter === "all") return "Тег"
    return tagFilter.length > 15 ? tagFilter.substring(0, 15) + "..." : tagFilter
  }, [tagFilter])

  // Закрываем все выпадающие меню при клике вне их
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (difficultyRef.current && !difficultyRef.current.contains(event.target as Node)) {
        setShowDifficultyMenu(false)
      }
      if (tagRef.current && !tagRef.current.contains(event.target as Node)) {
        setShowTagMenu(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Функции для переключения меню
  const toggleSort = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    setSortOrder(prev => prev === "asc" ? "desc" : "asc")
  }, [])

  const toggleDifficultyMenu = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    setShowDifficultyMenu(prev => !prev)
    setShowTagMenu(false)
  }, [])

  const toggleTagMenu = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    setShowTagMenu(prev => !prev)
    setShowDifficultyMenu(false)
  }, [])

  // Функции для выбора пунктов меню
  const selectDifficultyOption = useCallback((value: string) => {
    setDifficultyFilter(value)
    setShowDifficultyMenu(false)
  }, [])

  const selectTagOption = useCallback((value: string) => {
    setTagFilter(value)
    setShowTagMenu(false)
  }, [])

  // Функция для очистки фильтра тегов
  const clearTagFilter = useCallback(() => {
    setTagFilter("all")
  }, [])

  // Функция для обработки поиска
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value)
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
          right: 0;
          z-index: 50;
          margin-top: 4px;
          border-radius: 8px;
          background-color: rgba(var(--card-rgb), 0.95);
          backdrop-filter: blur(12px);
          border: 1px solid rgba(var(--border-rgb), 0.3);
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
          animation: fadeIn 0.15s ease-out;
          transform-origin: top center;
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
          <h1 className="text-4xl font-bold text-center tracking-tight">Список задач</h1>

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
            {/* Сортировка - теперь просто переключатель */}
            <button 
              className="text-filter"
              onClick={toggleSort}
              title={sortOrder === "asc" ? "Сортировка по возрастанию" : "Сортировка по убыванию"}
            >
              <ArrowUpDown className="h-4 w-4" />
              {sortOrder === "asc" ? "По возрастанию" : "По убыванию"}
              {sortOrder === "asc" ? (
                <ChevronUp className="h-4 w-4 text-green-500" />
              ) : (
                <ChevronDown className="h-4 w-4 text-red-500" />
              )}
            </button>

            {/* Фильтр по сложности */}
            <div className="relative" ref={difficultyRef}>
              <button 
                className={`text-filter ${showDifficultyMenu ? 'active' : ''}`}
                onClick={toggleDifficultyMenu}
              >
                {getDifficultyText()}
                <ChevronDown className={`h-4 w-4 chevron-icon ${showDifficultyMenu ? 'open' : ''}`} />
              </button>
              
              {showDifficultyMenu && (
                <div className="dropdown-menu min-w-[180px]">
                  <button
                    className={`menu-item ${difficultyFilter === 'all' ? 'active' : ''}`}
                    onClick={() => selectDifficultyOption('all')}
                  >
                    Все сложности
                  </button>
                  <button
                    className={`menu-item ${difficultyFilter === 'very-easy' ? 'active' : ''}`}
                    onClick={() => selectDifficultyOption('very-easy')}
                  >
                    Очень легкая
                  </button>
                  <button
                    className={`menu-item ${difficultyFilter === 'easy' ? 'active' : ''}`}
                    onClick={() => selectDifficultyOption('easy')}
                  >
                    Легкая
                  </button>
                  <button
                    className={`menu-item ${difficultyFilter === 'medium' ? 'active' : ''}`}
                    onClick={() => selectDifficultyOption('medium')}
                  >
                    Средняя
                  </button>
                  <button
                    className={`menu-item ${difficultyFilter === 'hard' ? 'active' : ''}`}
                    onClick={() => selectDifficultyOption('hard')}
                  >
                    Сложная
                  </button>
                  <button
                    className={`menu-item ${difficultyFilter === 'very-hard' ? 'active' : ''}`}
                    onClick={() => selectDifficultyOption('very-hard')}
                  >
                    Очень сложная
                  </button>
                </div>
              )}
            </div>

            {/* Фильтр по тегам */}
            <div className="relative" ref={tagRef}>
              <div className="flex items-center gap-2">
                <button 
                  className={`text-filter ${showTagMenu ? 'active' : ''}`}
                  onClick={toggleTagMenu}
                >
                  {getTagText()}
                  <ChevronDown className={`h-4 w-4 chevron-icon ${showTagMenu ? 'open' : ''}`} />
                </button>
                {tagFilter !== "all" && (
                  <button
                    onClick={clearTagFilter}
                    className="text-xs px-2 py-1 rounded bg-red-500/20 text-red-600 hover:bg-red-500/30 transition-colors"
                    title="Очистить фильтр"
                  >
                    ×
                  </button>
                )}
              </div>
              
              {showTagMenu && (
                <div className="dropdown-menu min-w-[250px]">
                  <ScrollArea className="h-[300px]">
                    <div className="p-1">
                      <button
                        className={`menu-item rounded ${tagFilter === 'all' ? 'active' : ''}`}
                        onClick={() => selectTagOption('all')}
                      >
                        Все теги
                      </button>
                      {uniqueTags.map((tag) => (
                        <button
                          key={tag}
                          className={`menu-item rounded ${tagFilter === tag ? 'active' : ''}`}
                          onClick={() => selectTagOption(tag)}
                        >
                          {tag}
                        </button>
                      ))}
                    </div>
                    <ScrollBar orientation="vertical" />
                  </ScrollArea>
                </div>
              )}
            </div>
          </div>

          {/* Список задач */}
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardContent className="pt-6">
              {loading ? (
                <div className="flex h-[calc(100vh-450px)] items-center justify-center">
                  <p className="text-muted-foreground">Загрузка задач...</p>
                </div>
              ) : (
                <ScrollArea className="h-[calc(100vh-450px)] w-full">
                  <div className="flex flex-col gap-3 pr-6">
                    {filteredAndSortedTasks.map((task) => (
                      <div key={`${task.contestId}-${task.index}`} className="flex items-center gap-3">
                        {/* Карточка задачи */}
                        <Link 
                          href={`/task/${task.contestId}-${task.index}`} 
                          className="flex-1"
                          prefetch={false}
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

                        {/* Отдельная кнопка для ссылки на Codeforces */}
                        <div className="flex items-center justify-between rounded-lg border border-border/50 p-2 bg-secondary/30 transition-colors hover:bg-secondary/50">
                          <Button 
                            size="icon" 
                            variant="outline" 
                            className="h-10 w-10 shrink-0 bg-transparent" 
                            asChild
                          >
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
