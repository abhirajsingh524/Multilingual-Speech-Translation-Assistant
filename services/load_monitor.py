"""
services/load_monitor.py
Lightweight server-side load monitor.

Tracks rolling average response time and request rate.
Used by the /processing route to decide whether to show
the hacker panel or the standard loader.

No external dependencies — pure Python stdlib.
"""
import time
import threading
from collections import deque

_lock         = threading.Lock()
_response_times: deque = deque(maxlen=20)   # last 20 request durations (seconds)
_request_times: deque  = deque(maxlen=60)   # timestamps of last 60 requests

# Thresholds
LATENCY_THRESHOLD_S  = 1.2   # avg response > 1.2 s  → high latency
TRAFFIC_THRESHOLD_RPM = 30   # > 30 req/min          → high traffic


def record_response(duration_s: float):
    """Call this after each request completes (e.g. via after_request hook)."""
    with _lock:
        _response_times.append(duration_s)
        _request_times.append(time.monotonic())


def avg_latency_s() -> float:
    with _lock:
        if not _response_times:
            return 0.0
        return sum(_response_times) / len(_response_times)


def requests_per_minute() -> float:
    now = time.monotonic()
    with _lock:
        recent = [t for t in _request_times if now - t <= 60]
    return float(len(recent))


def should_show_hacker_panel() -> bool:
    """
    Returns True when the server is under measurable load.
    Conditions (either):
      - Rolling average latency > LATENCY_THRESHOLD_S
      - Request rate > TRAFFIC_THRESHOLD_RPM
    """
    return (
        avg_latency_s()        > LATENCY_THRESHOLD_S or
        requests_per_minute()  > TRAFFIC_THRESHOLD_RPM
    )
