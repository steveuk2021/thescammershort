# Bitget Integration Notes (Phase 0)

- Base URL is `https://api.bitget.com` for prod and demo.
- This client uses Bitget REST signing (HMAC SHA256, base64).
- Only core endpoints are wired for Phase 0:
  - Market tickers (24h stats)
  - Contract specs
  - Account balances
  - Positions
  - Place order
- Demo trading uses `paptrading: 1` header when `USE_TESTNET=true`.
- v2 endpoints are used under `/api/v2/mix/...`.
