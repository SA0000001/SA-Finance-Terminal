from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def stale_after_for_source(source: str) -> int:
    source_lower = source.lower()
    if any(
        keyword in source_lower
        for keyword in ("order book", "funding", "open interest", "taker", "long/short", "usdt.d", "market cap")
    ):
        return 300
    if any(keyword in source_lower for keyword in ("etf flow", "farside")):
        return 43200
    if any(keyword in source_lower for keyword in ("news", "coindesk", "cryptocompare", "fng")):
        return 1800
    if any(keyword in source_lower for keyword in ("fred", "stablecoin")):
        return 21600
    if "blockchain" in source_lower:
        return 3600
    return 900


class HealthRecorder:
    def __init__(self):
        self._entries: dict[str, dict] = {}

    def success(self, source: str, latency_ms: float | None = None, stale_after_seconds: int | None = None):
        now = utc_now_iso()
        self._entries[source] = {
            "source": source,
            "ok": True,
            "latency_ms": round(latency_ms, 1) if latency_ms is not None else None,
            "fetched_at": now,
            "last_success_at": now,
            "error": "",
            "stale_after_seconds": stale_after_seconds or stale_after_for_source(source),
        }

    def failure(self, source: str, error: str, latency_ms: float | None = None, stale_after_seconds: int | None = None):
        self._entries[source] = {
            "source": source,
            "ok": False,
            "latency_ms": round(latency_ms, 1) if latency_ms is not None else None,
            "fetched_at": utc_now_iso(),
            "last_success_at": None,
            "error": error,
            "stale_after_seconds": stale_after_seconds or stale_after_for_source(source),
        }

    def export(self) -> dict[str, dict]:
        return dict(self._entries)


def is_stale(entry: dict, now: datetime | None = None) -> bool:
    if not entry.get("last_success_at"):
        return False
    now = now or datetime.now(timezone.utc)
    last_success = parse_iso_datetime(entry.get("last_success_at"))
    if last_success is None:
        return False
    threshold = entry.get("stale_after_seconds") or stale_after_for_source(entry.get("source", ""))
    return (now - last_success).total_seconds() > threshold


def merge_source_health(previous: dict[str, dict] | None, latest: dict[str, dict] | None) -> dict[str, dict]:
    previous = previous or {}
    latest = latest or {}
    merged = {key: dict(value) for key, value in previous.items()}
    now = datetime.now(timezone.utc)

    for source, entry in latest.items():
        merged_entry = dict(merged.get(source, {}))
        merged_entry.update(entry)
        merged_entry["source"] = source
        merged_entry["stale_after_seconds"] = (
            entry.get("stale_after_seconds")
            or merged_entry.get("stale_after_seconds")
            or stale_after_for_source(source)
        )

        if entry.get("ok"):
            merged_entry["last_success_at"] = entry.get("last_success_at") or entry.get("fetched_at")
        else:
            merged_entry["last_success_at"] = merged.get(source, {}).get("last_success_at")

        merged_entry["stale"] = is_stale(merged_entry, now)
        merged[source] = merged_entry

    for source, entry in merged.items():
        entry["stale"] = is_stale(entry, now)

    return merged


def _format_timestamp(value: str | None) -> str:
    parsed = parse_iso_datetime(value)
    if parsed is None:
        return "Never"
    return parsed.astimezone().strftime("%d.%m %H:%M:%S")


def build_health_summary(health_state: dict[str, dict]) -> dict:
    entries = []
    stale_sources = []
    failed_sources = []

    for source in sorted(health_state):
        entry = dict(health_state[source])
        status = "OK"
        if entry.get("stale"):
            status = "STALE"
            stale_sources.append(source)
        elif not entry.get("ok"):
            status = "FAIL"
            failed_sources.append(source)

        entries.append(
            {
                "Kaynak": source,
                "Durum": status,
                "Gecikme": f"{entry['latency_ms']:.0f} ms" if entry.get("latency_ms") is not None else "-",
                "Son basarili": _format_timestamp(entry.get("last_success_at")),
                "Hata": entry.get("error", "") or "-",
            }
        )

    return {
        "total_sources": len(entries),
        "healthy_sources": sum(1 for item in entries if item["Durum"] == "OK"),
        "failed_sources": failed_sources,
        "stale_sources": stale_sources,
        "rows": entries,
    }
