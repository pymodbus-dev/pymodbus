"""Simulator data model implementation."""
from __future__ import annotations

from .simdata import SimData
from .simdevice import SimDevice


class SimCore:  # pylint: disable=too-few-public-methods
    """Handler for the simulator/server."""

    def __init__(self) -> None:
        """Build datastore."""
        self.devices: dict[int, SimDevice] = {}

    @classmethod
    def build_block(cls, _block: list[SimData]) -> tuple[int, int, int] | None:
        """Build registers for device."""
        return None
