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
import { UserPlus } from "lucide-react"

export function SignUpButton() {
  const [open, setOpen] = useState(false)
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Here you can add logic to handle the registration
    console.log("Registration:", { username, email })
    setOpen(false)
    setUsername("")
    setEmail("")
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {/* Purple colors already fixed, keeping them */}
        <Button
          size="lg"
          className="bg-[#a855f7]/20 hover:bg-[#a855f7]/30 text-[#c084fc] border border-[#a855f7]/50 backdrop-blur-sm"
        >
          <UserPlus className="mr-2 h-5 w-5" />
          Зарегистрироваться
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md bg-card/95 backdrop-blur-xl border-[#06b6d4]/20">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-foreground">Регистрация</DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Впервые здесь? Введите свои данные и придумайте пароль
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-6 pt-4">
          <div className="space-y-2">
            <Label htmlFor="username" className="text-foreground">
              !! Codeforces Хэндл !!
            </Label>
            <Input
              id="username"
              placeholder="Введите Хэндл на сайте"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="bg-background/50 border-[#06b6d4]/30 focus:border-[#06b6d4] text-foreground placeholder:text-muted-foreground"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email" className="text-foreground">
              Пароль
            </Label>
            <Input
              id="password"
              type="password"
              placeholder="Придумайте пароль"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="bg-background/50 border-[#06b6d4]/30 focus:border-[#06b6d4] text-foreground placeholder:text-muted-foreground"
            />
          </div>
          <Button
            type="submit"
            className="w-full bg-[#06b6d4]/20 hover:bg-[#06b6d4]/30 text-[#22d3ee] border border-[#06b6d4]/50"
          >
            Создать аккаунт!
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
