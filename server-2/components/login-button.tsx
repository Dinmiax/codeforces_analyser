"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LogIn } from "lucide-react"

export function LoginButton() {
  const [open, setOpen] = useState(false)
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Here you can add logic to handle the login
    console.log("Login:", { username, password })
    setOpen(false)
    setUsername("")
    setPassword("")
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          size="lg"
          className="bg-[#06b6d4]/20 hover:bg-[#06b6d4]/30 text-[#22d3ee] border border-[#06b6d4]/50 backdrop-blur-sm"
        >
          <LogIn className="mr-2 h-5 w-5" />
          Войти
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md bg-card/95 backdrop-blur-xl border-[#06b6d4]/20">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-foreground">Вход</DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Введите свои данные для полного доступа к функционалу
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-6 pt-4">
          <div className="space-y-2">
            <Label htmlFor="login-username" className="text-foreground">
              Логин
            </Label>
            <Input
              id="login-username"
              placeholder="Введите логин"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="bg-background/50 border-[#06b6d4]/30 focus:border-[#06b6d4] text-foreground placeholder:text-muted-foreground"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="login-password" className="text-foreground">
              Пароль
            </Label>
            <Input
              id="login-password"
              type="password"
              placeholder="Введите пароль"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="bg-background/50 border-[#06b6d4]/30 focus:border-[#06b6d4] text-foreground placeholder:text-muted-foreground"
            />
          </div>
          <Button
            type="submit"
            className="w-full bg-[#06b6d4]/20 hover:bg-[#06b6d4]/30 text-[#22d3ee] border border-[#06b6d4]/50"
          >
            Войти
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
