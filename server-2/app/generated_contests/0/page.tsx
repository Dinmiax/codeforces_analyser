import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { AlertCircle } from "lucide-react"
import Link from "next/link"

export default function GeneratedContestErrorPage() {
  return (
    <div className="min-h-screen bg-background p-6 flex items-center justify-center">
      <Card className="border-border/50 bg-card/50 backdrop-blur-sm max-w-md w-full">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <AlertCircle className="h-16 w-16 text-destructive" />
          </div>
          <CardTitle className="text-2xl font-bold">Ошибка генерации контеста</CardTitle>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          <p className="text-muted-foreground">
            К сожалению, не удалось сгенерировать контест. Пожалуйста, попробуйте еще раз с другими параметрами.
          </p>
          <div className="flex flex-col gap-2">
            <Button asChild>
              <Link href="/contests">Вернуться к контестам</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/">На главную</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
