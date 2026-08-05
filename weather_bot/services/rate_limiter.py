"""Rate limiting simple par chat_id (fenêtre glissante en mémoire).

Empêche un utilisateur d'enchaîner un nombre excessif de requêtes météo
(donc d'appels à l'API payante WeatherAPI) sur une courte période.
"""

import time
from collections import defaultdict, deque

from weather_bot.config import RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS

# {chat_id: deque des timestamps des requêtes récentes}
_requests: dict[int, deque[float]] = defaultdict(deque)


def is_rate_limited(chat_id: int) -> bool:
    """
    Retourne True si le chat_id a dépassé le nombre de requêtes autorisées
    sur la fenêtre glissante configurée, sinon enregistre la requête et
    retourne False.
    """
    now = time.time()
    window = _requests[chat_id]

    while window and now - window[0] > RATE_LIMIT_WINDOW_SECONDS:
        window.popleft()

    if len(window) >= RATE_LIMIT_MAX_REQUESTS:
        return True

    window.append(now)
    return False
