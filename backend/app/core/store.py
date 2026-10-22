from dataclasses import dataclass, field
from threading import Lock

from app.core.models import Scan


@dataclass
class Store:
    scans: dict[str, Scan] = field(default_factory=dict)
    lock: Lock = field(default_factory=Lock)

    def save_scan(self, scan: Scan) -> None:
        with self.lock:
            self.scans[scan.id] = scan

    def get_scan(self, scan_id: str) -> Scan | None:
        with self.lock:
            return self.scans.get(scan_id)


store = Store()
