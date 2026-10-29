from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Flight:
    code: str
    origin: str
    destination: str
    depart: datetime
    arrive: datetime
    price_cents: int

    def __post_init__(self) -> None:
        if self.arrive <= self.depart:
            raise ValueError(f"{self.code}: arrives before it departs")
        if self.price_cents < 0:
            raise ValueError(f"{self.code}: negative price")
        if self.origin == self.destination:
            raise ValueError(f"{self.code}: origin equals destination")

    @property
    def duration_minutes(self) -> int:
        return int((self.arrive - self.depart).total_seconds() // 60)


@dataclass(frozen=True)
class Itinerary:
    legs: tuple[Flight, ...]

    @property
    def price_cents(self) -> int:
        return sum(f.price_cents for f in self.legs)

    @property
    def duration_minutes(self) -> int:
        return int((self.legs[-1].arrive - self.legs[0].depart).total_seconds() // 60)

    @property
    def stops(self) -> int:
        return len(self.legs) - 1

    def describe(self) -> str:
        route = " → ".join([self.legs[0].origin, *[f.destination for f in self.legs]])
        return (f"{route} | {len(self.legs)} leg(s) | "
                f"{self.price_cents / 100:.2f} EUR | {self.duration_minutes} min")
