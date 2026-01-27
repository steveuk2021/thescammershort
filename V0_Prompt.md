# V0 UI Prompt — THE SCAMMER SHORT (Phase 0)

## Goal
Design a Phase 0 trading dashboard UI for **THE SCAMMER SHORT**. This is an internal tool that mirrors Bitget’s layout and feel, focused on real-time monitoring and manual controls.

## Style Direction
- **Mimic Bitget UI**: dense, professional trading interface.
- Dark theme, high-contrast data tables, minimal whitespace.
- Emphasis on clarity and speed: PnL, positions, margin, DD are always visible.

## Must-Have Panels (Phase 0)
1. **Run Status Panel**
   - Status: RUN / PAUSE / STOP
   - Current run ID
   - Entry time (UTC)
   - Mode: Paper / Live
   - Exchange: Bitget

2. **Portfolio Overview**
   - Total margin in use
   - Overall PnL (USDT + %)
   - Overall DD (USDT + %)
   - Leverage
   - Global kill switch threshold

3. **Positions Table (Per Leg)**
   - Symbol
   - Side (always short)
   - Entry price
   - Current price
   - Quantity
   - Per-leg PnL (USDT + %)
   - Max favorable PnL / Max adverse PnL
   - Exit status / reason

4. **Controls**
   - Pause / Resume bot
   - Flatten all (reduce-only)
   - Manual TP/SL per leg

## Secondary (nice-to-have if space allows)
- Event log stream (errors, alerts, order rejects)
- Heartbeat / service status

## Data Behavior
- Real-time updates (polling or WS)
- Changes should visually highlight (blink/flash) on updates

## Output
- Provide a single dashboard page layout.
- Use a Bitget-like aesthetic.
- Keep it compact and functional.
