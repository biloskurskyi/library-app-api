from typing import Protocol


class Notifier(Protocol):
    """Port through which the domain announces events; adapters decide how to deliver them."""

    def publish(self, event: object) -> None: ...
