"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ScrollBar } from "@/components/ui/scroll-area"
import { 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  ChevronDown, 
  ChevronUp, 
  Target, 
  BookOpen, 
  TrendingDown, 
  TrendingUp,
  BarChart3,
  Zap,
  Flame,
  Brain,
  Award,
  Crown
} from "lucide-react"
import { useState, useRef, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import { LoginButton } from "@/components/login-button"

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

export default function GenerateContestsPage() {
  const router = useRouter()
  const [isLoggedIn] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Привет! Я помогу сгенерировать для вас контест. Выберите режим генерации и сложность, или просто опишите что вам нужно.",
      timestamp: new Date(Date.now() - 3600000)
    }
  ])
  const [inputMessage, setInputMessage] = useState("")
  const [generateMode, setGenerateMode] = useState<"weak" | "topic">("weak")
  const [selectedTopic, setSelectedTopic] = useState("")
  const [difficulty, setDifficulty] = useState("medium")
  const [isGenerating, setIsGenerating] = useState(false)
  
  // Состояния для выпадающих меню
  const [showDifficultyMenu, setShowDifficultyMenu] = useState(false)
  
  // Рефы для отслеживания кликов вне меню
  const difficultyRef = useRef<HTMLDivElement>(null)

  // Функции для получения отображаемого текста
  const getDifficultyText = useCallback(() => {
    if (difficulty === "very-easy") return "Очень легкая"
    if (difficulty === "easy") return "Легкая"
    if (difficulty === "medium") return "Средняя"
    if (difficulty === "hard") return "Сложная"
    return "Очень сложная"
  }, [difficulty])

  // Функция для получения иконки сложности
  const getDifficultyIcon = useCallback((level: string) => {
    switch(level) {
      case "very-easy": return <Award className="h-4 w-4" />
      case "easy": return <BarChart3 className="h-4 w-4" />
      case "medium": return <Zap className="h-4 w-4" />
      case "hard": return <Flame className="h-4 w-4" />
      case "very-hard": return <Crown className="h-4 w-4" />
      default: return <BarChart3 className="h-4 w-4" />
    }
  }, [])

  // Функция для получения иконки режима
  const getModeIcon = useCallback((mode: "weak" | "topic") => {
    return mode === "weak" 
      ? <Target className="h-4 w-4" />
      : <BookOpen className="h-4 w-4" />
  }, [])

  // Закрываем выпадающее меню при клике вне его
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (difficultyRef.current && !difficultyRef.current.contains(event.target as Node)) {
        setShowDifficultyMenu(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Функции для переключения меню
  const toggleDifficultyMenu = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    setShowDifficultyMenu(prev => !prev)
  }, [])

  // Функция для выбора пункта меню сложности
  const selectDifficultyOption = useCallback((value: string) => {
    setDifficulty(value)
    setShowDifficultyMenu(false)
  }, [])

  // Функция для переключения режима генерации
  const toggleGenerateMode = useCallback(() => {
    setGenerateMode(prev => prev === "weak" ? "topic" : "weak")
    if (generateMode === "topic") {
      setSelectedTopic("")
    }
  }, [generateMode])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() && generateMode === "topic" && !selectedTopic.trim()) {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Пожалуйста, введите тему для генерации контеста или выберите режим 'Западающие темы'",
        timestamp: new Date()
      }])
      return
    }

    const userMessage: Message = {
      role: "user",
      content: inputMessage || 
        (generateMode === "weak" 
          ? `Хочу контест на западающие темы со сложностью ${difficulty}`
          : `Хочу контест на тему "${selectedTopic}" со сложностью ${difficulty}`),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputMessage("")
    setIsGenerating(true)

    try {
      const requestBody = {
        mode: generateMode,
        topic: generateMode === "topic" ? selectedTopic : undefined,
        difficulty,
        prompt: inputMessage,
      }

      const response = await fetch("http://localhost:8000/generate-contest", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        throw new Error("Failed to generate contest")
      }

      const data = await response.json()

      const assistantMessage: Message = {
        role: "assistant",
        content: `✅ Контест успешно сгенерирован!\n\nID контеста: ${data.contestId}\nСложность: ${difficulty}\nРежим: ${generateMode === "weak" ? "Западающие темы" : `Тема: ${selectedTopic}`}\n\nПеренаправляю на страницу контеста...`,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])

      const profileId = 1
      setTimeout(() => {
        router.push(`/generated_contests/${profileId}/${data.contestId}`)
      }, 2000)
    } catch (error) {
      console.error("Error generating contest:", error)

      const errorMessage: Message = {
        role: "assistant",
        content: "❌ Произошла ошибка при генерации контеста. Попробуйте еще раз или измените параметры запроса.",
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, errorMessage])

      setTimeout(() => {
        router.push("/generated_contests/0")
      }, 2000)
    } finally {
      setIsGenerating(false)
    }
  }

  if (isLoggedIn) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <Card className="max-w-md w-full border-0 bg-card/50 backdrop-blur-sm">
          <CardContent className="p-6 text-center space-y-4">
            <Sparkles className="h-12 w-12 mx-auto text-primary" />
            <h2 className="text-xl font-bold">Требуется авторизация</h2>
            <p className="text-muted-foreground">Для генерации контестов необходимо войти в аккаунт</p>
            <LoginButton />
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <>
      <style jsx global>{`
        /* Стили для текстовых фильтров */
        .text-filter {
          position: relative;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 12px 20px;
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
          background: rgba(var(--accent-rgb), 0.1);
        }
        
        /* Стиль для переключателя режимов */
        .mode-toggle {
          position: relative;
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 20px;
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
        
        .mode-toggle:hover {
          color: hsl(var(--primary));
          background: rgba(0, 0, 0, 0.05);
        }
        
        .dark .mode-toggle:hover {
          background: rgba(255, 255, 255, 0.05);
        }
        
        .mode-toggle.active {
          color: hsl(var(--primary));
          background: rgba(var(--accent-rgb), 0.1);
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

        .dark .dropdown-menu {
          background-color: rgba(var(--card-rgb), 0.95);
          border-color: rgba(var(--border-rgb), 0.3);
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
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
          background-color: hsl(var(--card));
          border-color: hsl(var(--border));
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
        }
        
        .menu-item {
          display: flex;
          align-items: center;
          gap: 8px;
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
          background-color: rgba(var(--accent-rgb), 0.15);
        }
        
        .menu-item.active {
          background-color: rgba(var(--accent-rgb), 0.2);
          color: hsl(var(--accent-foreground));
          font-weight: 500;
        }
        
        .menu-item .icon {
          flex-shrink: 0;
        }
        
        /* Иконка стрелки */
        .chevron-icon {
          transition: transform 0.15s ease;
        }
        
        .chevron-icon.open {
          transform: rotate(180deg);
        }
        
        /* Иконка для сложности в кнопке */
        .difficulty-icon {
          flex-shrink: 0;
        }
      `}</style>
      
      <div className="min-h-screen bg-background p-6">
        <div className="mx-auto max-w-[1600px] space-y-8">
          {/* Заголовок */}
          <h1 className="text-4xl font-bold text-center tracking-tight">Генерация контестов</h1>

          <div className="flex gap-8">
            {/* Левая колонка с настройками */}
            <div className="w-80 space-y-6">
              

              <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
                <CardContent className="p-6 space-y-4">
                  <h2 className="text-lg font-bold flex items-center gap-2">
                    <Brain className="h-5 w-5" />
                    Как это работает
                  </h2>
                  <ul className="space-y-2 text-sm text-muted-foreground">
                    <li className="flex items-start gap-2">
                      <div className="h-1.5 w-1.5 rounded-full bg-primary mt-1.5" />
                      <span>Выберите режим генерации</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <div className="h-1.5 w-1.5 rounded-full bg-primary mt-1.5" />
                      <span>Укажите сложность</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <div className="h-1.5 w-1.5 rounded-full bg-primary mt-1.5" />
                      <span>Опишите дополнительные требования</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <div className="h-1.5 w-1.5 rounded-full bg-primary mt-1.5" />
                      <span>AI сгенерирует персонализированный контест</span>
                    </li>
                  </ul>
                </CardContent>
              </Card>


              <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
                <CardContent className="p-6 space-y-6">
                  <h2 className="text-lg font-bold flex items-center gap-2">
                    <Sparkles className="h-5 w-5" />
                    Настройки генерации
                  </h2>
                  
                  {/* Фильтры */}
                  <div className="flex flex-col gap-6">
                    {/* Режим генерации - переключатель */}
                    <div className="space-y-3">
                      <label className="text-sm font-medium">Режим генерации</label>
                      <button 
                        className="mode-toggle w-full justify-between"
                        onClick={toggleGenerateMode}
                      >
                        <div className="flex items-center gap-3">
                          {getModeIcon(generateMode)}
                          <span>
                            {generateMode === "weak" ? "Западающие темы" : "Выбор темы"}
                          </span>
                        </div>
                        {generateMode === "weak" ? (
                          <TrendingDown className="h-4 w-4 text-blue-500" />
                        ) : (
                          <TrendingUp className="h-4 w-4 text-purple-500" />
                        )}
                      </button>
                    </div>

                    {/* Сложность - выпадающий список */}
                    <div className="relative" ref={difficultyRef}>
                      <label className="text-sm font-medium mb-2 block">Сложность</label>
                      <button 
                        className={`text-filter w-full justify-between ${showDifficultyMenu ? 'active' : ''}`}
                        onClick={toggleDifficultyMenu}
                      >
                        <div className="flex items-center gap-3">
                          {getDifficultyIcon(difficulty)}
                          <span>{getDifficultyText()}</span>
                        </div>
                        <ChevronDown className={`h-4 w-4 chevron-icon ${showDifficultyMenu ? 'open' : ''}`} />
                      </button>
                      
                      {showDifficultyMenu && (
                        <div className="dropdown-menu">
                          <button
                            className={`menu-item ${difficulty === 'very-easy' ? 'active' : ''}`}
                            onClick={() => selectDifficultyOption('very-easy')}
                          >
                            <Award className="h-4 w-4 icon" />
                            Очень легкая
                          </button>
                          <button
                            className={`menu-item ${difficulty === 'easy' ? 'active' : ''}`}
                            onClick={() => selectDifficultyOption('easy')}
                          >
                            <BarChart3 className="h-4 w-4 icon" />
                            Легкая
                          </button>
                          <button
                            className={`menu-item ${difficulty === 'medium' ? 'active' : ''}`}
                            onClick={() => selectDifficultyOption('medium')}
                          >
                            <Zap className="h-4 w-4 icon" />
                            Средняя
                          </button>
                          <button
                            className={`menu-item ${difficulty === 'hard' ? 'active' : ''}`}
                            onClick={() => selectDifficultyOption('hard')}
                          >
                            <Flame className="h-4 w-4 icon" />
                            Сложная
                          </button>
                          <button
                            className={`menu-item ${difficulty === 'very-hard' ? 'active' : ''}`}
                            onClick={() => selectDifficultyOption('very-hard')}
                          >
                            <Crown className="h-4 w-4 icon" />
                            Очень сложная
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Поле темы */}
                  {generateMode === "topic" && (
                    <div className="space-y-3">
                      <label className="text-sm font-medium flex items-center gap-2">
                        <BookOpen className="h-4 w-4" />
                        Тема
                      </label>
                      <Input
                        placeholder="Введите тему контеста..."
                        value={selectedTopic}
                        onChange={(e) => setSelectedTopic(e.target.value)}
                        className="bg-background"
                      />
                    </div>
                  )}
                </CardContent>
              </Card>

            </div>

            {/* Правая колонка с чатом */}
            <div className="flex-1">
              <Card className="border-border/50 bg-card/50 backdrop-blur-sm h-full">
                <CardContent className="p-0 h-full flex flex-col">
                  {/* Заголовок чата */}
                  <div className="p-6 border-b border-border/50">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                        <Bot className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-bold">AI Ассистент</h3>
                        <p className="text-sm text-muted-foreground">Поможет сгенерировать идеальный контест</p>
                      </div>
                    </div>
                  </div>

                  {/* Сообщения */}
                  <ScrollArea className="flex-1 p-6">
                    <div className="space-y-6">
                      {messages.map((message, index) => (
                        <div
                          key={index}
                          className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                          <div className="max-w-[80%]">
                            <div className={`flex items-start gap-3 ${message.role === "user" ? "flex-row-reverse" : ""}`}>
                              <div className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${
                                message.role === "user" 
                                  ? "bg-primary/20" 
                                  : "bg-secondary"
                              }`}>
                                {message.role === "user" ? (
                                  <User className="h-4 w-4 text-primary" />
                                ) : (
                                  <Bot className="h-4 w-4" />
                                )}
                              </div>
                              <div className={`rounded-2xl px-4 py-3 ${
                                message.role === "user"
                                  ? "bg-primary/10 text-primary-foreground ml-auto"
                                  : "bg-secondary/50"
                              }`}>
                                <p className="whitespace-pre-line">{message.content}</p>
                                <p className={`text-xs mt-2 ${
                                  message.role === "user" ? "text-primary/70 text-right" : "text-muted-foreground"
                                }`}>
                                  {message.timestamp.toLocaleTimeString("ru-RU", {
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })}
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                      {isGenerating && (
                        <div className="flex justify-start">
                          <div className="flex items-start gap-3">
                            <div className="h-8 w-8 rounded-full bg-secondary flex items-center justify-center">
                              <Bot className="h-4 w-4" />
                            </div>
                            <div className="rounded-2xl px-4 py-3 bg-secondary/50">
                              <div className="flex gap-1">
                                <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce" />
                                <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:0.2s]" />
                                <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:0.4s]" />
                              </div>
                              <p className="text-xs mt-2 text-muted-foreground">
                                Генерирую контест...
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                    <ScrollBar orientation="vertical" />
                  </ScrollArea>

                  {/* Поле ввода */}
                  <div className="p-6 border-t border-border/50">
                    <div className="flex gap-2">
                      <Input
                        placeholder="Опишите дополнительные требования к контесту..."
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault()
                            handleSendMessage()
                          }
                        }}
                        disabled={isGenerating}
                        className="flex-1 bg-background"
                      />
                      <Button 
                        onClick={handleSendMessage} 
                        disabled={isGenerating || (!inputMessage.trim() && generateMode === "topic" && !selectedTopic.trim())}
                        className="gap-2"
                      >
                        <Send className="h-4 w-4" />
                        {isGenerating ? "Генерация..." : "Отправить"}
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">
                      Нажмите Enter для отправки, Shift + Enter для новой строки
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
