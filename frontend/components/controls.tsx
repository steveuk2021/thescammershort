"use client"

import { useState } from "react"
import { Pause, Play, XCircle, Target, ShieldAlert } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api } from "@/lib/api"

interface ControlsProps {
  isPaused: boolean
}

export function Controls({ isPaused }: ControlsProps) {
  const [flattenDialogOpen, setFlattenDialogOpen] = useState(false)
  const [tpDialogOpen, setTpDialogOpen] = useState(false)
  const [slDialogOpen, setSlDialogOpen] = useState(false)
  const [tpPercent, setTpPercent] = useState("10")
  const [slPercent, setSlPercent] = useState("25")

  const handlePauseResume = () => {
    if (isPaused) {
      api.commandResume().catch(console.error)
    } else {
      api.commandPause().catch(console.error)
    }
  }

  const handleFlattenAll = () => {
    api.commandCloseAll().catch(console.error)
    setFlattenDialogOpen(false)
  }

  const handleSetGlobalTp = () => {
    api.commandSetGlobalTp(Number(tpPercent)).catch(console.error)
    setTpDialogOpen(false)
  }

  const handleSetGlobalSl = () => {
    api.commandSetGlobalSl(Number(slPercent)).catch(console.error)
    setSlDialogOpen(false)
  }

  return (
    <div className="rounded border border-border bg-card p-4">
      <h2 className="mb-4 text-sm font-medium text-muted-foreground">Controls</h2>

      <div className="space-y-3">
        {/* Pause/Resume */}
        <Button
          onClick={handlePauseResume}
          variant={isPaused ? "default" : "secondary"}
          className={`w-full justify-start gap-2 ${
            isPaused
              ? "bg-profit hover:bg-profit/90 text-primary-foreground"
              : "bg-warning/20 hover:bg-warning/30 text-warning border-warning/50"
          }`}
        >
          {isPaused ? (
            <>
              <Play className="h-4 w-4" />
              Resume Trading
            </>
          ) : (
            <>
              <Pause className="h-4 w-4" />
              Pause Trading
            </>
          )}
        </Button>

        {/* Flatten All */}
        <Dialog open={flattenDialogOpen} onOpenChange={setFlattenDialogOpen}>
          <DialogTrigger asChild>
            <Button
              variant="outline"
              className="w-full justify-start gap-2 border-loss/50 text-loss hover:bg-loss/10 hover:text-loss bg-transparent"
            >
              <XCircle className="h-4 w-4" />
              Flatten All Positions
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-card border-border">
            <DialogHeader>
              <DialogTitle className="text-foreground">Flatten All Positions</DialogTitle>
              <DialogDescription className="text-muted-foreground">
                This will close all 8 open positions at market price. This action
                cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setFlattenDialogOpen(false)}
                className="border-border"
              >
                Cancel
              </Button>
              <Button
                onClick={handleFlattenAll}
                className="bg-loss hover:bg-loss/90 text-destructive-foreground"
              >
                Confirm Flatten
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Set Global TP */}
        <Dialog open={tpDialogOpen} onOpenChange={setTpDialogOpen}>
          <DialogTrigger asChild>
            <Button
              variant="outline"
              className="w-full justify-start gap-2 border-profit/50 text-profit hover:bg-profit/10 hover:text-profit bg-transparent"
            >
              <Target className="h-4 w-4" />
              Set Global Take Profit
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-card border-border">
            <DialogHeader>
              <DialogTitle className="text-foreground">Set Global Take Profit</DialogTitle>
              <DialogDescription className="text-muted-foreground">
                Set a take-profit percentage for all open positions without TP.
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <Label htmlFor="tp-percent" className="text-foreground">
                Take Profit %
              </Label>
              <div className="mt-2 flex items-center gap-2">
                <Input
                  id="tp-percent"
                  type="number"
                  value={tpPercent}
                  onChange={(e) => setTpPercent(e.target.value)}
                  className="bg-secondary border-border text-foreground"
                />
                <span className="text-muted-foreground">%</span>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                Positions will close when profit reaches this percentage.
              </p>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setTpDialogOpen(false)}
                className="border-border"
              >
                Cancel
              </Button>
              <Button
                onClick={handleSetGlobalTp}
                className="bg-profit hover:bg-profit/90 text-primary-foreground"
              >
                Set TP
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Set Global SL */}
        <Dialog open={slDialogOpen} onOpenChange={setSlDialogOpen}>
          <DialogTrigger asChild>
            <Button
              variant="outline"
              className="w-full justify-start gap-2 border-loss/50 text-loss hover:bg-loss/10 hover:text-loss bg-transparent"
            >
              <ShieldAlert className="h-4 w-4" />
              Set Global Stop Loss
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-card border-border">
            <DialogHeader>
              <DialogTitle className="text-foreground">Set Global Stop Loss</DialogTitle>
              <DialogDescription className="text-muted-foreground">
                Set a stop-loss percentage for all open positions without SL.
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <Label htmlFor="sl-percent" className="text-foreground">
                Stop Loss %
              </Label>
              <div className="mt-2 flex items-center gap-2">
                <Input
                  id="sl-percent"
                  type="number"
                  value={slPercent}
                  onChange={(e) => setSlPercent(e.target.value)}
                  className="bg-secondary border-border text-foreground"
                />
                <span className="text-muted-foreground">%</span>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                Positions will close when loss reaches this percentage.
              </p>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setSlDialogOpen(false)}
                className="border-border"
              >
                Cancel
              </Button>
              <Button
                onClick={handleSetGlobalSl}
                className="bg-loss hover:bg-loss/90 text-destructive-foreground"
              >
                Set SL
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}
