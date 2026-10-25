import time


class SimClock:
    def __init__(self, compression: float = 60.0):
        self.compression = compression
        self.start = time.monotonic()

    def now(self) -> float:
        return (time.monotonic() - self.start) * self.compression

    def restart(self, compression: float | None = None) -> None:
        if compression is not None:
            self.compression = compression
        self.start = time.monotonic()
