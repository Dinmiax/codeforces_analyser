"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ExternalLink, Copy, Check } from "lucide-react"
import { useEffect, useState } from "react"
import { useParams, useRouter, useSearchParams } from "next/navigation"
import { Send, Bot, User } from "lucide-react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Input } from "@/components/ui/input"

interface CodeforcesProblem {
  contestId: number
  index: string
  name: string
  rating?: number
  tags: string[]
}

interface CodeforcesApiResponse {
  status: string
  result: {
    problems: CodeforcesProblem[]
  }
}

interface TestCase {
  input: string
  output: string
}

interface ParsedProblemData {
  metadata: {
    contest_id: string
    problem_id: string
    title: string
    time_limit: string
    memory_limit: string
    header: string
  }
  content: {
    task: string
    input: string
    output: string
    note?: string
  }
  tests: {
    [key: string]: TestCase
  }
  raw: {
    raw_text: string
    statement_paragraphs: string[]
    input_paragraphs: string[]
    output_paragraphs: string[]
    note_paragraphs: string[]
  }
}

// Пример данных парсера в новом формате
const EXAMPLE_PARSED_DATA: ParsedProblemData = {
  metadata: {
    contest_id: "1000",
    problem_id: "A",
    title: "A. Codehorses T-shirts",
    time_limit: "2 seconds",
    memory_limit: "256 MB",
    header: "A. Codehorses T-shirts<br>Ограничение по времени: 2 seconds | Ограничение по памяти: 256 MB",
  },
  content: {
    task: 'Codehorses has just hosted the second Codehorses Cup. This year, the same as the previous one, organizers are giving T-shirts for the winners.<br><br>The valid sizes of T-shirts are either "M" or from $$$0$$$ to $$$3$$$ "X" followed by "S" or "L" . For example, sizes "M" , "XXS" , "L" , "XXXL" are valid and "XM" , "Z" , "XXXXL" are not.<br><br>There are $$$n$$$ winners to the cup for both the previous year and the current year. Ksenia has a list with the T-shirt sizes printed for the last year cup and is yet to send the new list to the printing office.<br><br>Organizers want to distribute the prizes as soon as possible, so now Ksenia is required not to write the whole list from the scratch but just make some changes to the list of the previous year. In one second she can choose arbitrary position in any word and replace its character with some uppercase Latin letter. Ksenia can\'t remove or add letters in any of the words.<br><br>What is the minimal number of seconds Ksenia is required to spend to change the last year list to the current one?<br><br>The lists are unordered . That means, two lists are considered equal if and only if the number of occurrences of any string is the same in both lists.',
    input:
      "The first line contains one integer $$$n$$$ ($$$1 \\le n \\le 100$$$) — the number of T-shirts.<br><br>The $$$i$$$-th of the next $$$n$$$ lines contains $$$a_i$$$ — the size of the $$$i$$$-th T-shirt of the list for the previous year.<br><br>The $$$i$$$-th of the next $$$n$$$ lines contains $$$b_i$$$ — the size of the $$$i$$$-th T-shirt of the list for the current year.",
    output:
      "Print the minimal number of seconds Ksenia is required to spend to change the last year list to the current one. If the lists are already equal, print 0.",
    note: '"M" with "S" and "S" in one of the occurrences of "XS" with "L".<br><br>"L" in "XXXL" with "S".'
  },
  tests: {
    "test1": {
      "input": "3<br>XS<br>XS<br>M<br>XL<br>S<br>XS",
      "output": "2"
    },
    "test2": {
      "input": "2<br>XXXL<br>XXL<br>XXL<br>XXXS",
      "output": "1"
    },
    "test3": {
      "input": "2<br>M<br>XS<br>XS<br>M",
      "output": "0"
    }
  },
  raw: {
    raw_text: "The first line contains one integer $$$n$$$ ($$$1 \\le n \\le 100$$$) — the number of T-shirts. The $$$i$$$-th of the next $$$n$$$ lines contains $$$a_i$$$ — the size of the $$$i$$$-th T-shirt of the list for the previous year. The $$$i$$$-th of the next $$$n$$$ lines contains $$$b_i$$$ — the size of the $$$i$$$-th T-shirt of the list for the current year. Print the minimal number of seconds Ksenia is required to spend to change the last year list to the current one. If the lists are already equal, print 0. \"M\" with \"S\" and \"S\" in one of the occurrences of \"XS\" with \"L\". \"L\" in \"XXXL\" with \"S\"",
    statement_paragraphs: [
      "Codehorses has just hosted the second Codehorses Cup. This year, the same as the previous one, organizers are giving T-shirts for the winners.",
      "The valid sizes of T-shirts are either \"M\" or from $$$0$$$ to $$$3$$$ \"X\" followed by \"S\" or \"L\" . For example, sizes \"M\" , \"XXS\" , \"L\" , \"XXXL\" are valid and \"XM\" , \"Z\" , \"XXXXL\" are not.",
      "There are $$$n$$$ winners to the cup for both the previous year and the current year. Ksenia has a list with the T-shirt sizes printed for the last year cup and is yet to send the new list to the printing office.",
      "Organizers want to distribute the prizes as soon as possible, so now Ksenia is required not to write the whole list from the scratch but just make some changes to the list of the previous year. In one second she can choose arbitrary position in any word and replace its character with some uppercase Latin letter. Ksenia can't remove or add letters in any of the words.",
      "What is the minimal number of seconds Ksenia is required to spend to change the last year list to the current one?",
      "The lists are unordered . That means, two lists are considered equal if and only if the number of occurrences of any string is the same in both lists."
    ],
    input_paragraphs: [
      "The first line contains one integer $$$n$$$ ($$$1 \\le n \\le 100$$$) — the number of T-shirts.",
      "The $$$i$$$-th of the next $$$n$$$ lines contains $$$a_i$$$ — the size of the $$$i$$$-th T-shirt of the list for the previous year.",
      "The $$$i$$$-th of the next $$$n$$$ lines contains $$$b_i$$$ — the size of the $$$i$$$-th T-shirt of the list for the current year."
    ],
    output_paragraphs: [
      "Print the minimal number of seconds Ksenia is required to spend to change the last year list to the current one. If the lists are already equal, print 0."
    ],
    note_paragraphs: [
      "\"M\" with \"S\" and \"S\" in one of the occurrences of \"XS\" with \"L\".",
      "\"L\" in \"XXXL\" with \"S\"."
    ]
  }
}

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

type HintMode = "small" | "medium" | "full"

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

// Функция для обработки HTML с LaTeX формулами (из первой версии)
function parseHtmlWithLatex(html: string) {
  // Заменяем $$$...$$$ на MathJax теги для отображения формул
  let processedHtml = html
    .replace(/<br>/g, '<br/>') // Заменяем <br> на корректные теги
    .replace(/\$\$\$/g, '$$'); // Заменяем $$$ на $$ для MathJax
  
  // Для формул вида $...$ (inline)
  processedHtml = processedHtml.replace(
    /\$([^$]+?)\$/g,
    '<span class="math-inline">\\($1\\)</span>'
  );
  
  // Для формул вида $$...$$ (display)
  processedHtml = processedHtml.replace(
    /\$\$([^$]+?)\$\$/g,
    '<div class="math-display">\\[$1\\]</div>'
  );
  
  return processedHtml;
}

// Функция для очистки текста от HTML и LaTeX для отображения в pre
function cleanTextForPre(text: string) {
  return text
    .replace(/<br>/g, '\n')
    .replace(/\$\$\$/g, '')
    .replace(/\$([^$]+?)\$/g, '$1')
    .replace(/\$\$([^$]+?)\$\$/g, '$1');
}

function TestExampleCard({ testName, test }: { testName: string; test: TestCase }) {
  const [copiedInput, setCopiedInput] = useState(false)
  const [copiedOutput, setCopiedOutput] = useState(false)

  const handleCopyInput = () => {
    navigator.clipboard.writeText(cleanTextForPre(test.input))
    setCopiedInput(true)
    setTimeout(() => setCopiedInput(false), 2000)
  }

  const handleCopyOutput = () => {
    navigator.clipboard.writeText(cleanTextForPre(test.output))
    setCopiedOutput(true)
    setTimeout(() => setCopiedOutput(false), 2000)
  }

  return (
    <div className="rounded-lg border bg-card/50 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h4 className="font-semibold text-lg">{testName}</h4>
      </div>

      <div className="space-y-4">
        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium text-green-600">Ввод</span>
            <Button variant="ghost" size="sm" onClick={handleCopyInput} className="h-7 px-2 text-xs">
              {copiedInput ? <Check className="mr-1 h-3 w-3" /> : <Copy className="mr-1 h-3 w-3" />}
              {copiedInput ? "Скопировано" : "Копировать"}
            </Button>
          </div>
          <pre className="rounded bg-muted p-3 font-mono text-sm whitespace-pre-wrap">
            {cleanTextForPre(test.input)}
          </pre>
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium text-blue-600">Вывод</span>
            <Button variant="ghost" size="sm" onClick={handleCopyOutput} className="h-7 px-2 text-xs">
              {copiedOutput ? <Check className="mr-1 h-3 w-3" /> : <Copy className="mr-1 h-3 w-3" />}
              {copiedOutput ? "Скопировано" : "Копировать"}
            </Button>
          </div>
          <pre className="rounded bg-muted p-3 font-mono text-sm whitespace-pre-wrap">
            {cleanTextForPre(test.output)}
          </pre>
        </div>
      </div>
    </div>
  )
}

function ProblemSection({ title, content }: { title: string; content: string }) {
  const rerenderMathJax = () => {
    if (typeof window.MathJax !== "undefined" && window.MathJax.typesetPromise) {
      window.MathJax.typesetPromise();
    }
  };

  useEffect(() => {
    // Перерисовываем MathJax после рендеринга компонента
    const timer = setTimeout(() => {
      rerenderMathJax();
    }, 100);
    
    return () => clearTimeout(timer);
  }, [content]);

  const processedContent = parseHtmlWithLatex(content);

  return (
    <div className="space-y-3">
      <h3 className="text-xl font-semibold">{title}</h3>
      {content ? (
        <div
          className="prose prose-sm dark:prose-invert max-w-none prose-p:my-2"
          dangerouslySetInnerHTML={{ __html: processedContent }}
        />
      ) : (
        <p className="text-muted-foreground italic">Нет данных</p>
      )}
    </div>
  )
}

declare global {
  interface Window {
    MathJax: any
  }
}

export default function TaskDetailPage() {
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()
  const id = params.id as string
  const [contestId, index] = id.split("-")

  const [problem, setProblem] = useState<CodeforcesProblem | null>(null)
  const [parsedData, setParsedData] = useState<ParsedProblemData | null>(null)
  const [loading, setLoading] = useState(true)
  const [showRawData, setShowRawData] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Привет! Я помогу тебе с этой задачей. Выбери режим помощи или задай вопрос.",
      timestamp: new Date(),
    },
  ])
  const [inputMessage, setInputMessage] = useState("")
  const [hintMode, setHintMode] = useState<HintMode>("small")
  const [isGenerating, setIsGenerating] = useState(false)

  const rerenderMathJax = () => {
    if (typeof window.MathJax !== "undefined" && window.MathJax.typesetPromise) {
      window.MathJax.typesetPromise();
    }
  };

  useEffect(() => {
    const initMathJax = () => {
      if (typeof window.MathJax !== "undefined") {
        window.MathJax.typesetPromise?.()
          .then(() => {
            console.log("MathJax typesetting complete")
          })
          .catch((err: any) => {
            console.error("MathJax typesetting failed:", err)
          })
      }
    }

    if (typeof window.MathJax === "undefined") {
      const script = document.createElement("script")
      script.src = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"
      script.async = true
      script.id = "MathJax-script"

      const config = document.createElement("script")
      config.type = "text/x-mathjax-config"
      config.text = `
        MathJax = {
          tex: {
            inlineMath: [['\\\\(', '\\\\)']],
            displayMath: [['\\\\[', '\\\\]']],
            processEscapes: true,
          },
          options: {
            skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
            ignoreHtmlClass: 'tex2jax_ignore',
            processHtmlClass: 'tex2jax_process'
          },
          startup: {
            ready: () => {
              MathJax.startup.defaultReady()
              MathJax.typesetPromise()
            }
          }
        }
      `

      script.onload = () => {
        setTimeout(() => {
          const elements = document.querySelectorAll('.math-inline, .math-display')
          if (elements.length > 0) {
            initMathJax()
          }
        }, 500)
      }

      document.head.appendChild(config)
      document.head.appendChild(script)
    } else {
      setTimeout(initMathJax, 100)
    }

    if (parsedData) {
      setTimeout(rerenderMathJax, 300)
    }
  }, [parsedData])

  useEffect(() => {
    async function fetchProblem() {
      try {
        const response = await fetch("https://codeforces.com/api/problemset.problems")
        const data: CodeforcesApiResponse = await response.json()

        if (data.status === "OK") {
          const foundProblem = data.result.problems.find(
            (p) => p.contestId === Number.parseInt(contestId) && p.index === index,
          )
          setProblem(foundProblem || null)
        }
      } catch (error) {
        console.error("Error fetching problem:", error)
      } finally {
        setLoading(false)
      }
    }

    // Загружаем данные из API парсера
    async function fetchParsedData() {
      try {
        const response = await fetch(`http://localhost:8000/parse-problem/${contestId}/${index}`)
        if (response.ok) {
          const data = await response.json()
          setParsedData(data)
        } else {
          // Если API недоступно, используем пример данных
          console.log("Using example data, API returned:", response.status)
          setParsedData(EXAMPLE_PARSED_DATA)
        }
      } catch (error) {
        console.error("Error fetching parsed data:", error)
        // В случае ошибки используем пример данных
        setParsedData(EXAMPLE_PARSED_DATA)
      }
    }

    fetchProblem()
    fetchParsedData()
  }, [contestId, index])

  const handleBack = () => {
    const from = searchParams.get("from")
    if (from === "contest") {
      const contestIdParam = searchParams.get("contestId")
      if (contestIdParam) {
        router.push(`/contest/${contestIdParam}`)
      } else {
        router.push("/contests")
      }
    } else {
      router.push("/tasks")
    }
  }

  const handleToggleRawData = () => {
    setShowRawData(!showRawData)
  }

  const toggleHintMode = () => {
    setHintMode((prev) => {
      if (prev === "small") return "medium"
      if (prev === "medium") return "full"
      return "small"
    })
  }

  const getHintModeLabel = () => {
    if (hintMode === "small") return "Небольшая подсказка"
    if (hintMode === "medium") return "Помощь с решением"
    return "Полное объяснение с кодом"
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return

    const userMessage: Message = {
      role: "user",
      content: inputMessage,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputMessage("")
    setIsGenerating(true)

    try {
      const requestBody = {
        problem_id: id,
        mode: hintMode,
        question: inputMessage,
        problem_data: parsedData // Отправляем данные задачи для контекста
      }

      const response = await fetch("http://localhost:8000/get-hint", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        throw new Error("Failed to get hint")
      }

      const data = await response.json()

      const assistantMessage: Message = {
        role: "assistant",
        content: data.hint || "Извини, я не смог сгенерировать подсказку. Попробуй переформулировать вопрос.",
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error("Error getting hint:", error)

      const errorMessage: Message = {
        role: "assistant",
        content: "❌ Произошла ошибка при генерации подсказки. Попробуй еще раз.",
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsGenerating(false)
    }
  }

  const codeforcesUrl = `https://codeforces.com/problemset/problem/${contestId}/${index}`

  // Функция для форматирования названия теста
  const formatTestName = (testKey: string): string => {
    const match = testKey.match(/test(\d+)/)
    if (match) {
      return `Пример ${match[1]}`
    }
    return testKey
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="mx-auto max-w-5xl">
          <div className="flex h-[calc(100vh-200px)] items-center justify-center">
            <p className="text-muted-foreground">Загрузка задачи...</p>
          </div>
        </div>
      </div>
    )
  }

  if (!problem) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="mx-auto max-w-5xl">
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardContent className="p-6">
              <p className="text-center text-muted-foreground">Задача не найдена</p>
              <div className="mt-4 text-center">
                <Button variant="outline" onClick={handleBack}>
                  Назад
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <>
      <style jsx global>{`
        /* LaTeX формулы из первой версии */
        .math-inline {
          display: inline-block;
          font-family: "Latin Modern Math", "STIX Two Math", "Cambria Math", serif;
          font-style: italic;
          padding: 0 2px;
          vertical-align: middle;
          color: inherit;
        }
        
        .math-display {
          display: block;
          text-align: center;
          margin: 1em 0;
          padding: 10px;
          background: rgba(0, 0, 0, 0.02);
          border-radius: 6px;
          font-family: "Latin Modern Math", "STIX Two Math", "Cambria Math", serif;
          overflow-x: auto;
          overflow-y: hidden;
        }
        
        .dark .math-display {
          background: rgba(255, 255, 255, 0.05);
        }
        
        .prose .math-inline {
          margin: 0 1px;
        }
        
        .prose .math-display {
          margin: 1.5em 0;
          padding: 1em;
        }
        
        /* Улучшаем отображение формул в темной теме */
        .dark .math-inline {
          opacity: 0.95;
        }
        
        /* Стили для элементов с MathJax */
        .MJX-TEX {
          font-size: 1.1em !important;
        }
        
        /* Улучшаем читаемость формул */
        mjx-container[jax="CHTML"] {
          display: inline-block !important;
          margin: 0 !important;
          padding: 0 !important;
        }
        
        mjx-container[jax="CHTML"][display="true"] {
          display: block !important;
          margin: 1em 0 !important;
        }
      `}</style>

      <div className="min-h-screen bg-background p-4 md:p-6">
        <div className="mx-auto max-w-7xl space-y-6">
          <Button variant="outline" className="mb-4 bg-transparent" onClick={handleBack}>
            ← Назад
          </Button>

          <div className="flex gap-6">
            <div className="flex-1 space-y-6">
              <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
                <CardHeader>
                  <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                    <div className="flex-1 space-y-3">
                      <CardTitle className="text-2xl font-bold">
                        {parsedData?.metadata.title || problem.name}
                      </CardTitle>

                      <div className="flex flex-wrap items-center gap-3 text-sm">
                        <span className={`font-semibold ${getDifficultyColor(problem.rating)}`}>
                          {getDifficultyLabel(problem.rating)}
                        </span>
                        <div className="hidden h-4 w-px bg-border/70 md:block" />
                        <span className="font-semibold">Рейтинг: {problem.rating || "—"}</span>
                        <div className="hidden h-4 w-px bg-border/70 md:block" />
                        <span className="text-muted-foreground">
                          Задача {contestId}
                          {index}
                        </span>
                      </div>

                      {parsedData?.metadata && (
                        <div className="flex flex-wrap items-center gap-3 text-sm">
                          <span className="font-semibold text-primary">
                            Ограничение по времени: {parsedData.metadata.time_limit}
                          </span>
                          <div className="h-4 w-px bg-border/70" />
                          <span className="font-semibold text-primary">
                            Ограничение по памяти: {parsedData.metadata.memory_limit}
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col gap-2">
                      <a href={codeforcesUrl} target="_blank" rel="noopener noreferrer">
                        <Button variant="outline" size="sm" className="gap-2 bg-transparent">
                          <ExternalLink className="h-4 w-4" />
                          Открыть на Codeforces
                        </Button>
                      </a>

                      <Button variant="ghost" size="sm" onClick={handleToggleRawData} className="gap-2 text-xs">
                        {showRawData ? "Скрыть сырые данные" : "Показать сырые данные"}
                      </Button>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-8">
                  <div>
                    <h3 className="mb-3 text-lg font-semibold">Темы</h3>
                    <div className="flex flex-wrap gap-2">
                      {problem.tags.map((tag) => (
                        <Badge key={tag} variant="secondary">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {parsedData ? (
                    <div className="space-y-8">
                      <ProblemSection title="Условие" content={parsedData.content.task} />

                      <ProblemSection title="Входные данные" content={parsedData.content.input} />

                      <ProblemSection title="Выходные данные" content={parsedData.content.output} />

                      {parsedData.tests && Object.keys(parsedData.tests).length > 0 && (
                        <div>
                          <h3 className="mb-4 text-xl font-semibold">Примеры тестов</h3>
                          <div className="grid gap-4">
                            {Object.entries(parsedData.tests).map(([testKey, test]) => (
                              <TestExampleCard
                                key={testKey}
                                testName={formatTestName(testKey)}
                                test={test}
                              />
                            ))}
                          </div>
                        </div>
                      )}

                      {parsedData.content.note && parsedData.content.note.trim() !== "" && (
                        <ProblemSection title="Примечание" content={parsedData.content.note} />
                      )}

                      {showRawData && parsedData && (
                        <div className="rounded-lg border border-dashed border-muted-foreground/30 p-4">
                          <h3 className="mb-4 text-lg font-semibold text-muted-foreground">
                            Сырые данные (для нейросети)
                          </h3>
                          <div className="space-y-4">
                            <div>
                              <h4 className="mb-2 text-sm font-medium">Полный текст:</h4>
                              <div className="rounded bg-muted p-3 text-xs whitespace-pre-wrap break-words">
                                {parsedData.raw.raw_text}
                              </div>
                            </div>

                            <div className="grid gap-4 md:grid-cols-2">
                              <div>
                                <h4 className="mb-2 text-sm font-medium">Параграфы условия:</h4>
                                <ul className="space-y-2">
                                  {parsedData.raw.statement_paragraphs.map((para, idx) => (
                                    <li key={idx} className="text-xs text-muted-foreground">
                                      {para}
                                    </li>
                                  ))}
                                </ul>
                              </div>

                              <div>
                                <h4 className="mb-2 text-sm font-medium">Параграфы примечания:</h4>
                                <ul className="space-y-2">
                                  {parsedData.raw.note_paragraphs.map((para, idx) => (
                                    <li key={idx} className="text-xs text-muted-foreground">
                                      {para}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="rounded-lg bg-secondary/30 p-4">
                      <p className="text-muted-foreground">
                        Данные задачи загружаются. Полное условие будет доступно после загрузки.
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            <div className="w-96 shrink-0">
              <Card className="border-border/50 bg-card/50 backdrop-blur-sm sticky top-6 h-[calc(100vh-6rem)]">
                <CardContent className="p-0 h-full flex flex-col">
                  <div className="p-4 border-b border-border/50">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                          <Bot className="h-4 w-4 text-primary" />
                        </div>
                        <div>
                          <h3 className="font-bold text-sm">AI Помощник</h3>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={toggleHintMode}
                      className="w-full px-3 py-2 text-sm rounded-lg bg-primary/10 hover:bg-primary/20 transition-colors flex items-center justify-between"
                    >
                      <span className="font-medium">{getHintModeLabel()}</span>
                      <span className="text-xs text-muted-foreground">Переключить →</span>
                    </button>
                  </div>

                  <ScrollArea className="flex-1 p-4">
                    <div className="space-y-4">
                      {messages.map((message, index) => (
                        <div
                          key={index}
                          className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                          <div className="max-w-[85%]">
                            <div
                              className={`flex items-start gap-2 ${message.role === "user" ? "flex-row-reverse" : ""}`}
                            >
                              <div
                                className={`h-6 w-6 rounded-full flex items-center justify-center shrink-0 ${
                                  message.role === "user" ? "bg-primary/20" : "bg-secondary"
                                }`}
                              >
                                {message.role === "user" ? (
                                  <User className="h-3 w-3 text-primary" />
                                ) : (
                                  <Bot className="h-3 w-3" />
                                )}
                              </div>
                              <div
                                className={`rounded-xl px-3 py-2 text-sm ${
                                  message.role === "user" ? "bg-primary/10 text-primary-foreground" : "bg-secondary"
                                }`}
                              >
                                <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                      {isGenerating && (
                        <div className="flex justify-start">
                          <div className="flex items-start gap-2">
                            <div className="h-6 w-6 rounded-full flex items-center justify-center shrink-0 bg-secondary">
                              <Bot className="h-3 w-3 animate-pulse" />
                            </div>
                            <div className="rounded-xl px-3 py-2 bg-secondary">
                              <p className="text-sm text-muted-foreground">Генерирую ответ...</p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </ScrollArea>

                  <div className="p-4 border-t border-border/50">
                    <div className="flex gap-2">
                      <Input
                        placeholder="Задай вопрос по задаче..."
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault()
                            handleSendMessage()
                          }
                        }}
                        disabled={isGenerating}
                        className="flex-1 bg-background text-sm"
                      />
                      <Button
                        size="icon"
                        onClick={handleSendMessage}
                        disabled={isGenerating || !inputMessage.trim()}
                        className="shrink-0"
                      >
                        <Send className="h-4 w-4" />
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">Режим: {getHintModeLabel()}</p>
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
