"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { LoginButton } from "@/components/login-button"

const navItems = [
  { name: "Задания", href: "/tasks" },
  { name: "Контесты", href: "/contests" },
  { name: "Профиль", href: "/profiles" },
  { name: "Генерация контестов", href: "/generate-contests" },
]

function getRankColor(rank: string): string {
  const rankLower = rank.toLowerCase()
  if (rankLower.includes("legendary grandmaster")) return "#aa0000" // Dark red/burgundy
  if (rankLower.includes("international grandmaster")) return "#ff0000" // Red
  if (rankLower.includes("grandmaster")) return "#ff8c00" // Orange
  if (rankLower.includes("international master")) return "#ff8c00" // Orange
  if (rankLower.includes("master")) return "#aa00aa" // Purple
  if (rankLower.includes("candidate master")) return "#aa00aa" // Purple
  if (rankLower.includes("expert")) return "#0000ff" // Blue
  if (rankLower.includes("specialist")) return "#03a89e" // Cyan
  if (rankLower.includes("pupil")) return "#008000" // Green
  return "#808080" // Gray for newbie
}

export function SiteHeader() {
  const pathname = usePathname()
  const [activeIndex, setActiveIndex] = useState(0)
  const [hoverIndex, setHoverIndex] = useState<number | null>(null)

  const [isLoggedIn] = useState(false)
  const user = isLoggedIn
    ? {
        handle: "tourist",
        rank: "Legendary Grandmaster",
      }
    : null

  useEffect(() => {
    const index = navItems.findIndex((item) => pathname.startsWith(item.href))
    if (index !== -1) setActiveIndex(index)
  }, [pathname])

  const displayIndex = hoverIndex !== null ? hoverIndex : activeIndex

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="w-full mx-auto flex h-16 items-center px-6">
        {/* Левый блок: Логотип и навигация */}
        <div className="flex items-center gap-8 flex-1">
          <Link href="/" className="flex items-center space-x-2">
            <span className="text-xl font-bold text-foreground">CF Upgrade</span>
          </Link>

          {/* Navigation with animated underline */}
          <nav className="flex items-center gap-1 relative">
            {navItems.map((item, index) => {
              const isActive = displayIndex === index
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="relative px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                  onMouseEnter={() => setHoverIndex(index)}
                  onMouseLeave={() => setHoverIndex(null)}
                >
                  {item.name}
                  {isActive && (
                    <div
                      className="absolute left-1/2 -translate-x-1/2 bottom-0 h-0.5 bg-[#06b6d4] transition-all duration-300 ease-out"
                      style={{ width: "calc(100% - 2rem)" }}
                    />
                  )}
                </Link>
              )
            })}
          </nav>
        </div>

        <div className="flex items-center gap-4 flex-shrink-0 ml-auto">
          {isLoggedIn && user ? (
            <>
              <Link
                href={`/profile/${user.handle}`}
                className="hover:opacity-80 transition-opacity"
                style={{ color: getRankColor(user.rank) }}
              >
                <span className="text-sm font-medium">{user.handle}</span>
              </Link>
              <Button variant="outline" size="sm" onClick={() => console.log("Logout")}>
                Выйти
              </Button>
            </>
          ) : (
            <LoginButton />
          )}
        </div>
      </div>
    </header>
  )
}
