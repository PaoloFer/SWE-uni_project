import logging
import threading
import time

from system.usecases import SystemUseCases

logger = logging.getLogger("system.background")


class SystemBackgroundWorker:
    def __init__(self, interval: int = 30, data_dir: str = "./data"):
        self.interval = interval
        self.usecases = SystemUseCases(data_dir)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="system-background-checks",
            daemon=True,
        )
        self._thread.start()
        logger.info("System background checks started (interval=%ss)", self.interval)

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.usecases.run_all_checks()
            except Exception:
                logger.exception("Error running system background checks")
            self._stop.wait(self.interval)