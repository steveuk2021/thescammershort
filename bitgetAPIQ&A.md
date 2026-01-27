Here’s a **live-verified, Bitget official documentation** summary answering each item in your Bitget API question list (focus on **USDT-M Perpetuals REST API – mix/contract**) based on the latest docs available online: ([Bitget][1])

---

## ✔️ 1) REST API Base URL (USDT-M Perps)

**Production:**

```
https://api.bitget.com
```

All documented futures endpoints (mix) use this domain (e.g., `/api/v2/mix/...`). ([bitgetlimited.github.io][2])

**Demo/Testnet:**
Bitget supports **demo trading via API**, but the **base domain remains the same**:

* You create a **Demo API Key** in Demo mode on the Bitget dashboard. ([Bitget][3])
* Then you call the same endpoints under `https://api.bitget.com`, with **demo API key** + specific header below.

**Demo-specific header:**

```
paptrading: 1
```

is **required in the request header** for demo trading. ([Bitget][3])

No other demo-specific headers are documented beyond that.

---

## ✔️ 2) API Passphrase

**Required?**
YES — for all **private REST requests** (trading/account). ([Bitget][4])

**Where it’s set:**
It is set **when creating the API key** in your Bitget user dashboard (API management). ([bitgetlimited.github.io][2])

Header name:

```
ACCESS-PASSPHRASE
```

Must be included in every authenticated REST request.

---

## ✔️ 3) Signature Algorithm & Signing String

**Algorithm:**
HMAC-SHA256 with **secretKey**, then **Base64 encode** the hash. ([Bitget][4])

**String to sign (exact):**

```
timestamp + method.toUpperCase() + requestPath + "?" + queryString + body
```

* If no queryString: omit `"?" + queryString`. ([Bitget][4])
* **timestamp** is the same value as `ACCESS-TIMESTAMP` header. ([Bitget][4])

**No canonical JSON sorting rule for body documented** — the body is used as a plain string (most examples show raw JSON without sorting). ([Bitget][4])

**Headers for auth:**

```
ACCESS-KEY
ACCESS-SIGN
ACCESS-PASSPHRASE
ACCESS-TIMESTAMP
Content-Type: application/json
locale: en-US (or zh-CN)
```

([Bitget][4])

---

## ✔️ 4) Timestamp Format & Time Drift

**Format:**
Milliseconds since Unix epoch (`System.currentTimeMillis()` style). ([Bitget][4])

**Time drift:**
Not explicitly documented in futures section, but common server validation applies — Bitget’s signature examples use ms. Typically ± a few seconds; if server time differs you may synchronize via server time endpoint (Websocket docs recommend syncing if drift too large). ([Bitget][5])

There is **no recvWindow parameter** documented for futures REST as part of signing rules (unlike some other exchanges). ([Bitget][4])

---

## ✔️ 5) Correct Endpoints (USDT-M Perpetuals)

| Function                        | Endpoint                                                        | Notes                                      |
| ------------------------------- | --------------------------------------------------------------- | ------------------------------------------ |
| **24h tickers (all)**           | GET `/api/v2/mix/market/tickers?productType=USDT-FUTURES`       | fetch 24h stats                            |
| **All positions (per account)** | GET `/api/v2/mix/position/allPosition?productType=USDT-FUTURES` | returns all futures positions              |
| **Place market order**          | POST `/api/v2/mix/order/place-order`                            | with `"orderType":"market"`                |
| **Close position (market)**     | Same place-order endpoint                                       | Use `side` + `tradeSide` depending on mode |
| ([Bitget][6])                   |                                                                 |                                            |

**Close position example logic (hedge mode):**

* Close long: `side=buy`, `tradeSide=close`
* Close short: `side=sell`, `tradeSide=close`
  (one-way mode: tradeSide is ignored) ([Bitget][6])

---

## ✔️ 6) Required Fields for `placeOrder` (USDT-M Perps)

| Field           | Value / Requirements                                                                                   |
| --------------- | ------------------------------------------------------------------------------------------------------ |
| **productType** | `"USDT-FUTURES"`                                                                                       |
| **marginCoin**  | `"USDT"`                                                                                               |
| **side**        | `"buy"` or `"sell"`                                                                                    |
| **tradeSide**   | *optional in one-way mode*; required in hedge mode (`"open"` / `"close"`)                              |
| **orderType**   | `"market"` or `"limit"`                                                                                |
| **size**        | contract quantity in base units — must respect `sizeMultiplier` and `minTradeNum` from contract config |
| **price**       | Not required for market orders                                                                         |
| **clientOid**   | Optional custom ID                                                                                     |
| **reduceOnly**  | Optional (YES/NO)                                                                                      |
| ([Bitget][6])   |                                                                                                        |

**Size units & rounding:**
Use **contract config** (`/api/v2/mix/market/contracts`) to get:

* `minTradeNum` – min size
* `sizeMultiplier` – step size
  (for USDT-M perps). ([Bitget][7])

---

## ✔️ 7) Symbol Format

**USDT-M perpetual contract symbol format:**

```
BTCUSDT
ETHUSDT
...
```

This is the symbol used in futures REST endpoints. ([Bitget][7])

**Note:** In some Bitget UI/Websocket contexts, *suffix formats* like `BTCUSDT_UMCBL` may appear in docs, but REST uses the simple base symbol for futures APIs. ([bitgetlimited.github.io][2])

---

## ✔️ 8) How to Query Contract Specs

**Endpoint:**

```
GET /api/v2/mix/market/contracts
```

Query with:

```
?productType=USDT-FUTURES&symbol=BTCUSDT
```

Returns:

* tick size (`pricePlace`)
* contract size (`sizeMultiplier`)
* min trade size (`minTradeNum`) and other params ([Bitget][7])

Use these to round order quantities properly.

---

## ✔️ 9) Subaccounts

**Subaccounts** are supported via broker API endpoints (for managing sub-account API keys), not direct futures trading param adjustments. ([bitgetlimited.github.io][8])

No separate futures REST parameter for subaccounts in standard endpoints — you use separate API keys per subaccount or broker API. ([bitgetlimited.github.io][8])

---

## ✔️ 10) Rate Limits & Tracking Headers

Rate limits are endpoint-specific. For example:

* **Place order:** 10 requests/second per UID
* **Get contract config:** 20 requests/second per IP ([Bitget][6])

Bitget does **not document a universal rate headers** like `x-rate-limit-remaining` for REST; you must handle **429 responses** if limits are hit. ([bitgetlimited.github.io][8])

---

## ✔️ 11) Standard Error Codes

Bitget uses structured error codes in JSON with fields like:

```
{ "code": "xxxx", "msg": "...", "requestTime": ..., "data": null }
```

* Authentication/signature errors typically return codes like `40001`/`40002` (invalid signature/key)
* Market/order errors have other specific codes (e.g., insufficient position, invalid parameters).

Specific error codes are documented on the API error section in the docs — refer to **Error Code** in futures API doc for the exact list. (Not fully exposed in the snippet search results available.) ([Bitget][1])

---

## Summary Table

| Item                | Verified Answer                                                           |
| ------------------- | ------------------------------------------------------------------------- |
| Base URL            | `https://api.bitget.com` (same prod & demo domain)                        |
| Demo trading header | `paptrading: 1`                                                           |
| Passphrase          | Required on all private REST                                              |
| Signature           | HMAC-SHA256 → Base64; string: `timestamp + method + path + ?query + body` |
| Timestamp           | ms since epoch                                                            |
| 24h Tickers         | `GET /api/v2/mix/market/tickers`                                          |
| Positions           | `GET /api/v2/mix/position/allPosition`                                    |
| Place market        | `POST /api/v2/mix/order/place-order`                                      |
| Close position      | Same endpoint w/ side+tradeSide                                           |
| Required fields     | productType, marginCoin, side, orderType, size                            |
| Symbol format       | `BTCUSDT` style                                                           |
| Contract specs      | `GET /api/v2/mix/market/contracts`                                        |
| Subaccounts         | via broker API                                                            |
| Rate limits         | Endpoint specific (e.g., 10–20/s)                                         |
| Error codes         | Standard structured error JSON                                            |

---

If you want **direct URLs + full parameter schemas** extracted into a ready-to-use specification (OpenAPI/JSON) from the official docs, specify that next and I’ll generate it.

