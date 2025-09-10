from __future__ import annotations
from typing import Callable, DefaultDict, Dict, List, Type, Any
from collections import defaultdict
from datetime import datetime
from .domain import BaseEvent

class EventBus:
    """Basit senkron event bus. subscribe(EventClass, callback)"""
    def __init__(self):
        self._subs: DefaultDict[Type[BaseEvent], List[Callable[[BaseEvent], None]]] = defaultdict(list)

    def subscribe(self, event_cls: Type[BaseEvent], callback: Callable[[BaseEvent], None]) -> None:
        self._subs[event_cls].append(callback)

    def publish(self, event: BaseEvent) -> None:
        # sınıf bazlı dispatch; BaseEvent subscriber'larına da düşmesin diye tam sınıf eşleşmesi yapıyoruz
        for cls, cbs in list(self._subs.items()):
            if isinstance(event, cls):
                for cb in cbs:
                    cb(event)

# Mini HTTP metrics endpoint draft (Prometheus pull model ile uyumlu olacak servis tarafı için placeholder)
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
        else:
            self.send_response(404); self.end_headers()

def start_health_server(port: int = 8000):
    def _run():
        HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t
