"use client"

import { useState } from "react"
import { Target, ShieldAlert } from "lucide-react"
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

interface LegTpSlDialogProps {
  positionId: string
  symbol: string
  type: "tp" | "sl"
  currentPrice: number | null
  formatPrice: (price: number) => string
}

export function LegTpSlDialog({ 
  positionId, 
  symbol, 
  type, 
  currentPrice,
  formatPrice 
}: LegTpSlDialogProps) {
  const [open, setOpen] = useState(false)
  const [price, setPrice] = useState(currentPrice?.toString() || "")

  const isTP = type === "tp"
  const title = isTP ? "Set Take Profit" : "Set Stop Loss"
  const description = isTP 
    ? `Set a take-profit price for ${symbol}. Position will close when price drops to this level.`
    : `Set a stop-loss price for ${symbol}. Position will close when price rises to this level.`

  const handleSubmit = () => {
    const num = Number(price)
    if (Number.isNaN(num)) return
    if (type === "tp") {
      api.commandLegTp(symbol, num).catch(console.error)
    } else {
      api.commandLegSl(symbol, num).catch(console.error)
    }
    setOpen(false)
  }

  const handleClear = () => {
    if (type === "tp") {
      api.commandLegTpClear(symbol).catch(console.error)
    } else {
      api.commandLegSlClear(symbol).catch(console.error)
    }
    setPrice("")
    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={`h-7 gap-1.5 text-xs ${
            isTP 
              ? "border-profit/50 text-profit hover:bg-profit/10 hover:text-profit bg-transparent" 
              : "border-loss/50 text-loss hover:bg-loss/10 hover:text-loss bg-transparent"
          }`}
        >
          {isTP ? <Target className="h-3 w-3" /> : <ShieldAlert className="h-3 w-3" />}
          {isTP ? "Set TP" : "Set SL"}
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-card border-border">
        <DialogHeader>
          <DialogTitle className="text-foreground">{title}</DialogTitle>
          <DialogDescription className="text-muted-foreground">
            {description}
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <Label htmlFor={`${positionId}-${type}-price`} className="text-foreground">
            {isTP ? "Take Profit Price" : "Stop Loss Price"}
          </Label>
          <div className="mt-2">
            <Input
              id={`${positionId}-${type}-price`}
              type="text"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder={currentPrice ? formatPrice(currentPrice) : "Enter price..."}
              className="bg-secondary border-border text-foreground font-mono"
            />
          </div>
          {currentPrice && (
            <p className="mt-2 text-xs text-muted-foreground">
              Current {isTP ? "TP" : "SL"}: {formatPrice(currentPrice)}
            </p>
          )}
          <p className="mt-2 text-xs text-muted-foreground">
            {isTP 
              ? "For SHORT positions, TP triggers when mark price drops below this level."
              : "For SHORT positions, SL triggers when mark price rises above this level."}
          </p>
        </div>
        <DialogFooter className="flex gap-2">
          {currentPrice && (
            <Button
              variant="outline"
              onClick={handleClear}
              className="border-border text-muted-foreground bg-transparent"
            >
              Clear {isTP ? "TP" : "SL"}
            </Button>
          )}
          <Button
            variant="outline"
            onClick={() => setOpen(false)}
            className="border-border"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!price}
            className={isTP 
              ? "bg-profit hover:bg-profit/90 text-primary-foreground" 
              : "bg-loss hover:bg-loss/90 text-destructive-foreground"
            }
          >
            Set {isTP ? "TP" : "SL"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
