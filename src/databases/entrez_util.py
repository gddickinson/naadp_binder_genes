"""Entrez network hardening — the one place NCBI calls get a timeout.

**The bug this module exists to fix, measured in S0.** Biopython's
`Bio.Entrez` builds its requests on `urllib.request.urlopen` and passes no
timeout. `urlopen` with no timeout blocks in `SSLSocket.read()` forever, so
a stalled NCBI connection hangs the calling thread with no error, no output
and no CPU. In the headless pipeline the orchestrator waits on its worker
threads, so one hung Entrez read hangs the entire run silently — the S0
smoke test sat for fifteen minutes at 0 % CPU in `PySSL_select` before it
was sampled and killed.

`urlopen` falls back to the **module-level default socket timeout** when it
is handed none, so setting that default is what actually bounds an Entrez
call. Biopython exposes no per-call timeout parameter, which is why this is
done at the socket layer rather than at the call site.

Every `Bio.Entrez` call in this repo goes through `entrez_call()`.
"""

from __future__ import annotations

import socket
import time
from typing import Any, Callable

#: Default ceiling on any single Entrez request, in seconds. NCBI's own
#: guidance is that a well-formed esearch/esummary returns in a few seconds;
#: anything past a minute is a stall, not a slow query.
DEFAULT_TIMEOUT_S = 60

#: Set once, process-wide, by `ensure_socket_timeout()`. Recorded so a
#: caller can tell whether it is running hardened.
_configured_timeout: float | None = None


def ensure_socket_timeout(timeout_s: float = DEFAULT_TIMEOUT_S) -> float:
    """Bound every socket that is created without an explicit timeout.

    Deliberately process-wide and not restored afterwards. The alternative —
    setting and unsetting the default around each call — races with the
    other worker threads the orchestrator runs, and a socket that is created
    during the "unset" window inherits no timeout at all, which is the bug.

    Clients that pass their own timeout (every `requests` call in this repo
    does) are unaffected: an explicit timeout always wins over the default.
    """
    global _configured_timeout
    current = socket.getdefaulttimeout()
    if current is None or current > timeout_s:
        socket.setdefaulttimeout(timeout_s)
        _configured_timeout = timeout_s
    else:
        _configured_timeout = current
    return _configured_timeout


def configured_timeout() -> float | None:
    """The timeout `ensure_socket_timeout()` installed, or None if unset."""
    return _configured_timeout


def entrez_call(fn: Callable[..., Any], *args: Any,
                timeout_s: float = DEFAULT_TIMEOUT_S,
                retries: int = 3,
                backoff_s: float = 2.0,
                **kwargs: Any) -> Any:
    """Call an `Entrez.*` function with a bounded, retried network read.

    Returns the open handle exactly as the wrapped function does, so call
    sites keep using it as a context manager.

    A timeout is retried because NCBI stalls are usually transient; the
    final failure is raised rather than swallowed, so a genuinely
    unreachable NCBI surfaces as an error instead of an empty result set
    that would look like a real absence.
    """
    ensure_socket_timeout(timeout_s)
    last: Exception | None = None
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except (socket.timeout, TimeoutError, OSError) as exc:
            last = exc
            if attempt < retries - 1:
                time.sleep(backoff_s * (attempt + 1))
    raise RuntimeError(
        f"NCBI Entrez call {getattr(fn, '__name__', fn)} failed after "
        f"{retries} attempts (timeout {timeout_s}s): {last}"
    ) from last
