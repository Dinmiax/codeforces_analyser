"use client"

import { usePathname } from "next/navigation"
import { SiteHeader } from "@/components/site-header"

export function ConditionalHeader() {
  const pathname = usePathname()
  const isHomePage = pathname === "/"

  if (isHomePage) return null

  return <SiteHeader />
}
