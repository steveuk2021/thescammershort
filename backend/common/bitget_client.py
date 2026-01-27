import base64
import hashlib
import hmac
import json
import time
from typing import Any, Optional, Dict
from urllib.parse import urlencode

import httpx

from .config import settings


class BitgetClient:
    def __init__(self) -> None:
        self.base_url = settings.bitget_base_url.rstrip("/")
        self.api_key = settings.bitget_api_key
        self.api_secret = settings.bitget_api_secret
        self.api_passphrase = settings.bitget_api_passphrase

    def _timestamp(self) -> str:
        # Bitget expects milliseconds as a string
        return str(int(time.time() * 1000))

    def _sign(self, ts: str, method: str, path: str, query: str, body: str) -> str:
        if query:
            path = f"{path}?{query}"
        message = f"{ts}{method.upper()}{path}{body}"
        mac = hmac.new(self.api_secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256)
        return base64.b64encode(mac.digest()).decode("utf-8")

    def _headers(self, ts: str, sign: str) -> dict[str, str]:
        headers = {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": sign,
            "ACCESS-TIMESTAMP": ts,
            "ACCESS-PASSPHRASE": self.api_passphrase,
            "Content-Type": "application/json",
        }
        if settings.use_testnet:
            # Bitget demo trading requires this header
            headers["paptrading"] = "1"
        return headers

    def _request(
        self, method: str, path: str, params: Optional[Dict[str, Any]] = None, body: Optional[Dict[str, Any]] = None
    ) -> Any:
        url = f"{self.base_url}{path}"
        params = params or {}
        body = body or {}
        body_str = json.dumps(body) if body else ""
        query_str = urlencode(params, doseq=True)
        ts = self._timestamp()
        sign = self._sign(ts, method, path, query_str, body_str)
        headers = self._headers(ts, sign)

        with httpx.Client(timeout=10.0) as client:
            response = client.request(method, url, params=params, content=body_str, headers=headers)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = response.text
                raise RuntimeError(f"Bitget API error {response.status_code} {path}: {detail}") from exc
            return response.json()

    # Market data
    def get_usdt_perp_tickers(self) -> Any:
        # All USDT-M perpetual tickers (24h stats)
        return self._request("GET", "/api/v2/mix/market/tickers", params={"productType": "USDT-FUTURES"})

    def get_contracts(self, symbol: Optional[str] = None) -> Any:
        params = {"productType": "USDT-FUTURES"}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/api/v2/mix/market/contracts", params=params)

    # Account/position data
    def get_positions(self, symbol: Optional[str] = None) -> Any:
        params = {"productType": "USDT-FUTURES"}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/api/v2/mix/position/all-position", params=params)

    def get_accounts(self, product_type: str = "USDT-FUTURES") -> Any:
        # Account balances for the given product type
        return self._request("GET", "/api/v2/mix/account/accounts", params={"productType": product_type})

    # Orders
    def place_order(
        self,
        symbol: str,
        side: str,
        size: str,
        margin_coin: str = "USDT",
        order_type: str = "market",
        trade_side: Optional[str] = None,
        reduce_only: Optional[str] = None,
    ) -> Any:
        # side: buy | sell
        # trade_side: open | close (required in hedge mode)
        body = {
            "symbol": symbol,
            "marginCoin": margin_coin,
            "size": size,
            "side": side,
            "orderType": order_type,
            "productType": "USDT-FUTURES",
            "marginMode": "crossed",
        }
        if trade_side:
            body["tradeSide"] = trade_side
        if reduce_only:
            body["reduceOnly"] = reduce_only
        return self._request("POST", "/api/v2/mix/order/place-order", body=body)

    def close_position_market(self, symbol: str, size: str, position_side: str, margin_coin: str = "USDT") -> Any:
        # position_side: long | short
        side = "sell" if position_side == "long" else "buy"
        return self.place_order(
            symbol=symbol,
            side=side,
            size=size,
            margin_coin=margin_coin,
            order_type="market",
            trade_side="close",
            reduce_only="YES",
        )

    def set_leverage(
        self,
        symbol: str,
        leverage: str,
        margin_coin: str = "USDT",
        margin_mode: Optional[str] = None,
        hold_side: Optional[str] = None,
    ) -> Any:
        body = {
            "symbol": symbol,
            "productType": "USDT-FUTURES",
            "marginCoin": margin_coin,
            "leverage": leverage,
        }
        if margin_mode:
            body["marginMode"] = margin_mode
        if hold_side:
            body["holdSide"] = hold_side
        print(f"[bitget] set-leverage request body={body}")
        return self._request("POST", "/api/v2/mix/account/set-leverage", body=body)
