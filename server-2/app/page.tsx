"use client"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Code2, TrendingUp, Users, Award } from "lucide-react"
import Link from "next/link"
import { SignUpButton } from "@/components/sign-up-button"
import { LoginButton } from "@/components/login-button"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-[#06b6d4]/10 via-background to-[#a855f7]/10" />
        <div className="relative mx-auto max-w-7xl px-6 py-24 lg:px-12 lg:py-32">
          <div className="text-center space-y-8">
            <h1 className="text-5xl lg:text-7xl font-bold tracking-tight text-foreground">Codeforces Upgrade</h1>
            <p className="text-xl lg:text-2xl text-muted-foreground max-w-3xl mx-auto">
              Продвинутая аналитическая панель для спортивного программирования
            </p>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Отслеживайте свой прогресс, анализируйте свои результаты и освойте спортивное программирование с помощью
              комплексной аналитики и инсайтов.
            </p>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
              <LoginButton />
              <SignUpButton />
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="mx-auto max-w-7xl px-6 py-16 lg:px-12 lg:py-24">
        <h2 className="text-3xl lg:text-4xl font-bold text-center mb-12 text-foreground">
          Почему стоит выбрать Codeforces Upgrade?
        </h2>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <Card className="p-6 bg-card/50 backdrop-blur-sm border-[#06b6d4]/20 hover:border-[#06b6d4]/40 transition-colors">
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-lg bg-[#06b6d4]/20 flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-[#22d3ee]" />
              </div>
              <h3 className="text-lg font-semibold text-foreground">Аналитика производительности</h3>
              <p className="text-muted-foreground">
                Отслеживайте прогресс рейтинга, статистику решений и тенденции производительности over time.
              </p>
            </div>
          </Card>

          <Card className="p-6 bg-card/50 backdrop-blur-sm border-[#06b6d4]/20 hover:border-[#06b6d4]/40 transition-colors">
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-lg bg-[#a855f7]/20 flex items-center justify-center">
                <Code2 className="w-6 h-6 text-[#c084fc]" />
              </div>
              <h3 className="text-lg font-semibold text-foreground">Отслеживание задач</h3>
              <p className="text-muted-foreground">
                Мониторьте решенные задачи, определяйте слабые места и планируйте тренировки.
              </p>
            </div>
          </Card>

          <Card className="p-6 bg-card/50 backdrop-blur-sm border-[#06b6d4]/20 hover:border-[#06b6d4]/40 transition-colors">
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-lg bg-[#06b6d4]/20 flex items-center justify-center">
                <Users className="w-6 h-6 text-[#22d3ee]" />
              </div>
              <h3 className="text-lg font-semibold text-foreground">Персонализированные контесты</h3>
              <p className="text-muted-foreground">
                Создавайте индивидуальные контесты на основе ваших слабых мест и целей для эффективной подготовки.
              </p>
            </div>
          </Card>

          <Card className="p-6 bg-card/50 backdrop-blur-sm border-[#06b6d4]/20 hover:border-[#06b6d4]/40 transition-colors">
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-lg bg-[#a855f7]/20 flex items-center justify-center">
                <Award className="w-6 h-6 text-[#c084fc]" />
              </div>
              <h3 className="text-lg font-semibold text-foreground">Совершенствуй навыки</h3>
              <p className="text-muted-foreground">
                Интеллектуальные рекомендации и целевые тренировки для прокачки конкретных алгоритмов и структур данных.
              </p>
            </div>
          </Card>
        </div>
      </div>

      {/* CTA Section */}
      <div className="mx-auto max-w-7xl px-6 py-16 lg:px-12">
        <Card className="p-12 bg-gradient-to-br from-[#06b6d4]/10 to-[#a855f7]/10 border-[#06b6d4]/20 text-center">
          <h2 className="text-3xl lg:text-4xl font-bold mb-4 text-foreground">
            Готовы освоить спортивное программирование?
          </h2>
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            Присоединяйтесь к тысячам спортивных программистов, которые улучшают свои навыки с Codeforces Upgrade.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <SignUpButton />
            <Button
              asChild
              variant="outline"
              size="lg"
              className="border-[#06b6d4]/50 hover:bg-[#06b6d4]/10 text-foreground bg-transparent"
            >
              <Link href="/profile/0">Посмотреть демо-панель</Link>
            </Button>
          </div>
        </Card>
      </div>
    </div>
  )
}
