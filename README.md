# itinerary-optimizer

Cheapest feasible multi-city itinerary: connections must respect a minimum
layover, the whole trip must land before a deadline, and legs are capped.

Zero dependencies (stdlib only), Python 3.9+.

## Why not Dijkstra

The cost of a connection depends on *when* you arrive, so "MAD" at 10:00 and
"MAD" at 18:00 are different states. A static graph gives wrong answers. The
search sweeps flights by departure time and relaxes each one from the best
itinerary that can feed it — a shortest path over a DAG, O(E × max_legs).

## Usage

```python
from itinerary import search
best = search(flights, "CDG", "LIS", depart_after=..., arrive_by=..., max_legs=3)
print(best.describe())   # CDG → MAD → LIS | 2 leg(s) | 130.00 EUR | 360 min
```

## Design notes

- **Tie-breaks are explicit:** cheapest wins, then shortest total duration.
- **Feasibility is checked, not hoped for:** `min_connection` (default 45 min),
  `arrive_by`, `depart_after` and `max_legs` are all enforced.
- `Flight` validates itself (arrive after depart, non-negative price, no
  self-loop), so a bad feed fails at the boundary.

## Tests

12 tests: cheaper-connection-beats-direct, tight layover rejected, deadline
deadline, leg cap, tie-breaking on duration, no-route.
