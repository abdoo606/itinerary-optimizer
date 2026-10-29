import unittest
from datetime import datetime, timedelta

from itinerary.models import Flight, Itinerary
from itinerary.search import search

BASE = datetime(2026, 11, 10, 6, 0)


def at(hour, minute=0, day=0):
    return BASE + timedelta(days=day, hours=hour, minutes=minute)


def flight(code, origin, destination, dep_h, arr_h, price, dep_m=0, arr_m=0):
    return Flight(code, origin, destination, at(dep_h, dep_m), at(arr_h, arr_m), price)


class ModelTests(unittest.TestCase):
    def test_duration_and_price(self):
        f = flight("A1", "CDG", "MAD", 8, 10, 9000)
        self.assertEqual(f.duration_minutes, 120)

    def test_invalid_flight_rejected(self):
        with self.assertRaises(ValueError):
            Flight("BAD", "CDG", "MAD", at(10), at(9), 100)
        with self.assertRaises(ValueError):
            Flight("BAD", "CDG", "CDG", at(9), at(10), 100)

    def test_itinerary_aggregates(self):
        a = flight("A1", "CDG", "MAD", 8, 10, 5000)
        b = Flight("B1", "MAD", "LIS", at(12), at(14), 5000)
        it = Itinerary((a, b))
        self.assertEqual(it.price_cents, 10000)
        self.assertEqual(it.stops, 1)
        self.assertEqual(it.duration_minutes, 360)
        self.assertIn("CDG → MAD → LIS", it.describe())


class SearchTests(unittest.TestCase):
    def test_cheap_connection_beats_expensive_direct(self):
        flights = [
            flight("D1", "CDG", "LIS", 8, 11, 30000),
            flight("C1", "CDG", "MAD", 8, 10, 6000),
            flight("C2", "MAD", "LIS", 12, 14, 7000),
        ]
        best = search(flights, "CDG", "LIS", at(6), at(20))
        self.assertEqual(best.price_cents, 13000)
        self.assertEqual([f.code for f in best.legs], ["C1", "C2"])
        self.assertEqual(best.stops, 1)

    def test_direct_wins_when_cheaper(self):
        flights = [
            flight("D1", "CDG", "LIS", 8, 11, 12000),
            flight("C1", "CDG", "MAD", 8, 10, 6000),
            flight("C2", "MAD", "LIS", 12, 14, 7000),
        ]
        self.assertEqual(search(flights, "CDG", "LIS", at(6), at(20)).price_cents, 12000)

    def test_connection_too_tight_is_rejected(self):
        flights = [
            flight("C1", "CDG", "MAD", 8, 10, 6000),
            Flight("C2", "MAD", "LIS", at(10, 30), at(12), 5000),
        ]
        self.assertIsNone(search(flights, "CDG", "LIS", at(6), at(20)))

    def test_connection_with_enough_time_is_accepted(self):
        flights = [
            flight("C1", "CDG", "MAD", 8, 10, 6000),
            Flight("C2", "MAD", "LIS", at(10, 50), at(12), 5000),
        ]
        self.assertEqual(search(flights, "CDG", "LIS", at(6), at(20)).price_cents, 11000)

    def test_arrival_deadline_is_respected(self):
        flights = [flight("D1", "CDG", "LIS", 18, 21, 9000)]
        self.assertIsNone(search(flights, "CDG", "LIS", at(6), at(20)))
        self.assertIsNotNone(search(flights, "CDG", "LIS", at(6), at(22)))

    def test_departure_window_is_respected(self):
        flights = [flight("D1", "CDG", "LIS", 8, 11, 9000)]
        self.assertIsNone(search(flights, "CDG", "LIS", at(9), at(20)))

    def test_max_legs_limits_stops(self):
        flights = [
            flight("C1", "CDG", "MAD", 8, 10, 5000),
            flight("C2", "MAD", "BCN", 12, 14, 5000),
            flight("C3", "BCN", "LIS", 16, 18, 5000),
        ]
        self.assertIsNone(search(flights, "CDG", "LIS", at(6), at(23), max_legs=2))
        self.assertIsNotNone(search(flights, "CDG", "LIS", at(6), at(23), max_legs=3))

    def test_tie_on_price_breaks_on_duration(self):
        flights = [
            flight("FAST", "CDG", "LIS", 6, 8, 10000),
            flight("SLOW", "CDG", "LIS", 9, 15, 10000),
        ]
        self.assertEqual(search(flights, "CDG", "LIS", at(6), at(23)).legs[0].code, "FAST")

    def test_no_route(self):
        self.assertIsNone(search([], "CDG", "LIS", at(6), at(20)))

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            search([], "CDG", "CDG", at(6), at(20))
        with self.assertRaises(ValueError):
            search([], "CDG", "LIS", at(20), at(6))
        with self.assertRaises(ValueError):
            search([], "CDG", "LIS", at(6), at(20), max_legs=0)
