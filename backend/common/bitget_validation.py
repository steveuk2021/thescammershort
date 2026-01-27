def ensure_required_env(settings) -> None:
    missing = []
    if not settings.bitget_api_key:
        missing.append("BITGET_API_KEY")
    if not settings.bitget_api_secret:
        missing.append("BITGET_API_SECRET")
    if not settings.bitget_api_passphrase:
        missing.append("BITGET_API_PASSPHRASE")
    if missing:
        raise RuntimeError(f"Missing required Bitget env vars: {', '.join(missing)}")
