import type React from "react"
import type { Metadata } from "next"
import { Montserrat } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import "./globals.css"
import { ConditionalHeader } from "@/components/conditional-header"

const montserrat = Montserrat({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Codeforces Upgrade",
  description: "Advanced analytics dashboard for competitive programming",
  generator: "v0.app",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`font-sans antialiased ${montserrat.className}`}>
        <ConditionalHeader />
        {children}
        <Analytics />
      </body>
    </html>
  )
}
