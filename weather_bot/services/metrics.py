"""Compteurs de métriques en mémoire, thread-safe, pour l'observabilité basique.

Ne remplace pas un vrai système de métriques (Prometheus, etc.) mais permet
de savoir en un coup d'œil dans les logs combien de requêtes/erreurs/cache
hits ont eu lieu depuis le démarrage du bot.
"""

import threading

_lock = threading.Lock()
_counters: dict[str, int] = {
    "requests": 0,
    "cache_hits": 0,
    "errors": 0,
    "rate_limited": 0,
}


def increment(counter: str) -> None:
    with _lock:
        _counters[counter] = _counters.get(counter, 0) + 1


def snapshot() -> dict[str, int]:
    with _lock:
        return dict(_counters)
