from backend.common.bitget_client import BitgetClient

c = BitgetClient()
resp = c.get_usdt_perp_tickers()

with open("sample_output.json", "w", encoding="utf-8") as f:
    import json
    json.dump(resp, f, ensure_ascii=False, indent=2)

print("Wrote sample_output.json with", len(resp.get("data", [])), "tickers")
