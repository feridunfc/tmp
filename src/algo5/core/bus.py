from __future__ import annotations
from collections import defaultdict
from typing import Any, Callable, DefaultDict, List, Type
import logging

log = logging.getLogger(__name__)
Handler = Callable[[Any, "EventBus"], None]


class EventBus:
    """Basit in-memory publish/subscribe bus (handler imzası: fn(event, bus))."""

    def __init__(self) -> None:
        self._subs: DefaultDict[Type[Any], List[Handler]] = defaultdict(list)

    def subscribe(self, event_type: Type[Any], handler: Handler) -> None:
        self._subs[event_type].append(handler)
        log.debug("subscribed %s -> %s", handler.__name__, event_type.__name__)

    def publish(self, event: Any) -> None:
        for h in list(self._subs.get(type(event), [])):
            try:
                h(event, self)
            except Exception:
                log.exception("handler %s failed for %s", h.__name__, type(event).__name__)

    def publish_many(self, events: List[Any]) -> None:
        for e in events:
            self.publish(e)
