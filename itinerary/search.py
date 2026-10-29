"""Cheapest path through a time-dependent flight graph.

Naive Dijkstra fails here: the cost of a connection depends on *when* you
arrive, so the same airport at a different minute is a different state. Instead
we sweep flights in departure order and relax each one from the best itinerary
that can feed it - a shortest path over a DAG, which is O(E * legs).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from .models import Flight, Itinerary

DEFAULT_MIN_CONNECTION = timedelta(minutes=45)


class Best:
    """Best known itinerary ending with a given flight."""

    __slots__ = ("itinerary", "legs")

    def __init__(self, itinerary: Itinerary, legs: int):
        self.itinerary = itinerary
        self.legs = legs


def search(flights: list[Flight], origin: str, destination: str,
           depart_after: datetime, arrive_by: datetime,
           min_connection: timedelta = DEFAULT_MIN_CONNECTION,
           max_legs: int = 3) -> Itinerary | None:
    if origin.upper() == destination.upper():
        raise ValueError("origin and destination must differ")
    if arrive_by <= depart_after:
        raise ValueError("arrive_by must be after depart_after")
    if max_legs < 1:
        raise ValueError("max_legs must be >= 1")

    origin, destination = origin.upper(), destination.upper()
    ordered = sorted(flights, key=lambda f: (f.depart, f.price_cents))
    best: dict[str, Best] = {}   # flight code -> best itinerary ending with it
    answer: Itinerary | None = None

    def better(candidate: Itinerary, current: Itinerary | None) -> bool:
        if current is None:
            return True
        return (candidate.price_cents, candidate.duration_minutes) < (
            current.price_cents, current.duration_minutes)

    for flight in ordered:
        if flight.arrive > arrive_by or flight.destination.upper() == origin:
            continue
        if flight.origin.upper() == origin:
            if flight.depart < depart_after:
                continue
            candidate = Itinerary((flight,))
            current = best.get(flight.code)
            if current is None or better(candidate, current.itinerary):
                best[flight.code] = Best(candidate, 1)
                if flight.destination.upper() == destination:
                    answer = candidate if better(candidate, answer) else answer
            continue

        feeders = []
        for code, state in best.items():
            last = state.itinerary.legs[-1]
            if last.destination.upper() != flight.origin.upper():
                continue
            if flight.depart - last.arrive < min_connection:
                continue
            if state.legs + 1 > max_legs:
                continue
            feeders.append(state)
        if not feeders:
            continue
        # cheapest feeder wins; ties go to the shorter total journey
        feeders.sort(key=lambda s: (s.itinerary.price_cents, s.itinerary.duration_minutes))
        feeder = feeders[0]
        candidate = Itinerary(feeder.itinerary.legs + (flight,))
        current = best.get(flight.code)
        if current is None or better(candidate, current.itinerary):
            best[flight.code] = Best(candidate, feeder.legs + 1)
            if flight.destination.upper() == destination:
                answer = candidate if better(candidate, answer) else answer

    return answer
