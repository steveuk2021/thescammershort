# Bitget USDT-M Perpetuals REST API (v2) — Parameter Schemas

---

## GET /api/v2/mix/market/tickers

**Description:** Get 24h ticker data for all contracts under a product type.

### Request
- **Method:** GET  
- **Path:** `/api/v2/mix/market/tickers`

### Query Parameters
| Name | Type | Required | Description |
|-----|------|----------|-------------|
| productType | string | YES | `USDT-FUTURES` \| `COIN-FUTURES` \| `USDC-FUTURES` |

### Response (data[])
| Field | Type | Description |
|------|------|-------------|
| symbol | string | Contract symbol (e.g. BTCUSDT) |
| lastPr | string | Last traded price |
| askPr | string | Best ask price |
| bidPr | string | Best bid price |
| askSz | string | Ask size |
| bidSz | string | Bid size |
| high24h | string | 24h high |
| low24h | string | 24h low |
| change24h | string | 24h price change |
| baseVolume | string | Base volume |
| quoteVolume | string | Quote volume |
| usdtVolume | string | USDT volume |
| indexPrice | string | Index price |
| markPrice | string | Mark price |
| fundingRate | string | Current funding rate |
| ts | string | Timestamp (ms) |

---

## GET /api/v2/mix/market/contracts

**Description:** Get contract specifications (tick size, lot size, limits).

### Request
- **Method:** GET  
- **Path:** `/api/v2/mix/market/contracts`

### Query Parameters
| Name | Type | Required | Description |
|-----|------|----------|-------------|
| productType | string | YES | `USDT-FUTURES` |
| symbol | string | NO | Contract symbol (e.g. BTCUSDT) |

### Response (data[])
| Field | Type | Description |
|------|------|-------------|
| symbol | string | Contract symbol |
| baseCoin | string | Base asset |
| quoteCoin | string | Quote asset |
| pricePlace | string | Price precision (tick size) |
| sizeMultiplier | string | Contract size step |
| minTradeNum | string | Minimum order size |
| maxOrderQty | string | Max limit order size |
| maxMarketOrderQty | string | Max market order size |
| makerFeeRate | string | Maker fee |
| takerFeeRate | string | Taker fee |
| minLever | string | Minimum leverage |
| maxLever | string | Maximum leverage |

---

## GET /api/v2/mix/position/all-position

**Description:** Get all open positions for the account.

### Request
- **Method:** GET  
- **Path:** `/api/v2/mix/position/all-position`
- **Auth:** Required

### Query Parameters
| Name | Type | Required | Description |
|-----|------|----------|-------------|
| productType | string | YES | `USDT-FUTURES` |
| marginCoin | string | NO | `USDT` |

### Response (data[])
| Field | Type | Description |
|------|------|-------------|
| symbol | string | Contract symbol |
| marginCoin | string | Margin currency |
| holdSide | string | `long` \| `short` |
| posMode | string | `one_way_mode` \| `hedge_mode` |
| leverage | string | Leverage |
| openPriceAvg | string | Average entry price |
| marginSize | string | Margin used |
| available | string | Available position |
| locked | string | Locked amount |
| total | string | Total position size |
| unrealizedPL | string | Unrealized PnL |
| liquidationPrice | string | Liquidation price |
| breakEvenPrice | string | Break-even price |
| markPrice | string | Mark price |
| keepMarginRate | string | Maintenance margin rate |
| totalFee | string | Total fees |
| deductedFee | string | Deducted fees |

---

## POST /api/v2/mix/order/place-order

**Description:** Place a futures order (market/limit, open/close).

### Request
- **Method:** POST  
- **Path:** `/api/v2/mix/order/place-order`
- **Auth:** Required  
- **Content-Type:** `application/json`

### Body Parameters
| Name | Type | Required | Description |
|-----|------|----------|-------------|
| symbol | string | YES | Contract symbol (e.g. ETHUSDT) |
| productType | string | YES | `USDT-FUTURES` |
| marginMode | string | YES | `isolated` \| `crossed` |
| marginCoin | string | YES | `USDT` |
| size | string | YES | Order size (contracts) |
| price | string | NO | Required for limit orders |
| side | string | YES | `buy` \| `sell` |
| tradeSide | string | CONDITIONAL | `open` \| `close` (hedge mode) |
| orderType | string | YES | `market` \| `limit` |
| force | string | NO | `gtc` \| `ioc` \| `fok` \| `post_only` |
| reduceOnly | string | NO | `YES` \| `NO` |
| clientOid | string | NO | Client order ID |

### Notes
- Market orders **must not** include `price`
- One-way mode: `tradeSide` optional
- Hedge mode: `tradeSide` required

