"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { HelpCircle, MessageSquare, BookOpen, Send } from "lucide-react"

export function HelpButton() {
  const [mainOpen, setMainOpen] = useState(false)
  const [feedbackOpen, setFeedbackOpen] = useState(false)
  const [explanationOpen, setExplanationOpen] = useState(false)
  const [taskNumber, setTaskNumber] = useState("")
  const [explanation, setExplanation] = useState("")
  const [editingExplanation, setEditingExplanation] = useState(false)
  const [tempExplanation, setTempExplanation] = useState(explanation)

  const openFeedback = () => {
    setMainOpen(false)
    setFeedbackOpen(true)
  }

  const openExplanation = () => {
    setMainOpen(false)
    setExplanationOpen(true)
  }

  const saveExplanation = () => {
    setExplanation(tempExplanation)
    setEditingExplanation(false)
  }

  return (
    <>
      {/* Main Help Button */}
      <Button
        size="icon"
        className="fixed bottom-8 left-8 h-14 w-14 rounded-full bg-primary shadow-lg shadow-primary/50 transition-all hover:scale-110 hover:shadow-xl hover:shadow-primary/60"
        onClick={() => setMainOpen(true)}
      >
        <HelpCircle className="h-6 w-6" />
      </Button>

      {/* Main Menu Dialog */}
      <Dialog open={mainOpen} onOpenChange={setMainOpen}>
        <DialogContent className="bg-card sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-2xl">How can we help?</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <Button
              variant="outline"
              className="h-auto flex-col items-start gap-2 border-border/50 bg-secondary/30 p-4 hover:bg-secondary/50 hover:border-primary/50"
              onClick={openFeedback}
            >
              <div className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-primary" />
                <span className="text-lg font-semibold">Send Feedback</span>
              </div>
              <p className="text-left text-sm text-muted-foreground">Share your thoughts and suggestions with us</p>
            </Button>

            <Button
              variant="outline"
              className="h-auto flex-col items-start gap-2 border-border/50 bg-secondary/30 p-4 hover:bg-secondary/50 hover:border-primary/50"
              onClick={openExplanation}
            >
              <div className="flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-primary" />
                <span className="text-lg font-semibold">Task Explanation</span>
              </div>
              <p className="text-left text-sm text-muted-foreground">Learn more about how this dashboard works</p>
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Feedback Dialog */}
      <Dialog open={feedbackOpen} onOpenChange={setFeedbackOpen}>
        <DialogContent className="bg-card sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-2xl">Send Feedback</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" placeholder="your@email.com" className="bg-background" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="feedback">Your Feedback</Label>
              <Textarea id="feedback" placeholder="Tell us what you think..." className="min-h-32 bg-background" />
            </div>
            <Button className="w-full gap-2">
              <Send className="h-4 w-4" />
              Submit Feedback
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Explanation Dialog */}
      <Dialog open={explanationOpen} onOpenChange={setExplanationOpen}>
        <DialogContent className="bg-card sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-2xl">Task Explanation</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="taskNumber">Task Number</Label>
              <Input
                id="taskNumber"
                type="text"
                placeholder="Enter task number (e.g., 1234A)"
                value={taskNumber}
                onChange={(e) => setTaskNumber(e.target.value)}
                className="bg-background"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="explanation">Explanation</Label>
              {editingExplanation ? (
                <>
                  <Textarea
                    id="explanation"
                    value={tempExplanation}
                    onChange={(e) => setTempExplanation(e.target.value)}
                    placeholder="Enter task explanation here..."
                    className="min-h-40 bg-background"
                  />
                  <div className="flex gap-2">
                    <Button onClick={saveExplanation} className="flex-1">
                      Save
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setEditingExplanation(false)
                        setTempExplanation(explanation)
                      }}
                      className="flex-1"
                    >
                      Cancel
                    </Button>
                  </div>
                </>
              ) : (
                <>
                  <div className="rounded-lg border border-gray-700 bg-secondary/30 p-4 min-h-40">
                    {explanation ? (
                      <p className="text-sm leading-relaxed text-foreground">{explanation}</p>
                    ) : (
                      <p className="text-sm text-muted-foreground italic">No explanation yet. Click edit to add one.</p>
                    )}
                  </div>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setEditingExplanation(true)
                      setTempExplanation(explanation)
                    }}
                    className="w-full"
                  >
                    Edit Explanation
                  </Button>
                </>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
