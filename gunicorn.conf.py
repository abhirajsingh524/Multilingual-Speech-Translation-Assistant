"""
gunicorn.conf.py — Memory-optimised config for Render free tier (≤512 MB RAM).

Usage:
    gunicorn -c gunicorn.conf.py app:app

Key decisions:
  workers=1   — each worker is a full Python process; 2 workers = 2× RAM.
  threads=2   — handles concurrent requests within the single worker cheaply.
  timeout=120 — local model fallback can take 30-60 s; don't kill the request.
  max_requests — recycle the worker periodically to prevent memory creep.
"""
import multiprocessing

# ── Workers ───────────────────────────────────────────────────────────────────
# 1 worker = 1 Python process.  On 512 MB, this is the only safe value.
# The formula (2 × CPU + 1) gives 3 on a 1-vCPU Render instance — too much.
workers = 1
threads = 2                     # lightweight concurrency within the worker

# ── Timeouts ──────────────────────────────────────────────────────────────────
timeout         = 120           # local Whisper/NLLB can take up to 60 s
graceful_timeout = 30
keepalive       = 5

# ── Worker recycling — prevents slow memory creep ────────────────────────────
max_requests          = 100     # restart worker after 100 requests
max_requests_jitter   = 20      # randomise to avoid thundering herd

# ── Binding ───────────────────────────────────────────────────────────────────
bind = "0.0.0.0:10000"

# ── Logging ───────────────────────────────────────────────────────────────────
loglevel    = "info"
accesslog   = "-"               # stdout
errorlog    = "-"               # stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(D)sµs'

# ── Process name ──────────────────────────────────────────────────────────────
proc_name = "msta"
