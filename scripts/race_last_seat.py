"""Live demo: many customers try to book the last seats of a trip at the same moment.

Usage: python scripts/race_last_seat.py [--api http://localhost:8000] [--clients 20] [--trip-id N]
Without --trip-id it picks the upcoming trip with the fewest seats left (but at least one).
Standard library only, so it runs with any Python 3.
"""

import argparse
import json
import threading
import urllib.error
import urllib.request
from collections import Counter


def call(method, url, body=None):
    request = urllib.request.Request(
        url, method=method, data=json.dumps(body).encode() if body else None,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--clients", type=int, default=20)
    parser.add_argument("--trip-id", type=int)
    args = parser.parse_args()
    api = args.api.rstrip("/") + "/api/v1"

    _, page = call("GET", f"{api}/admin/trips?status=scheduled&limit=100")
    trips = page["trips"]
    candidates = [t for t in trips if t["seats_available"] > 0]
    trip = next((t for t in trips if t["id"] == args.trip_id), None) if args.trip_id else \
        min(candidates, key=lambda t: t["seats_available"])
    print(f"Trip {trip['id']}: {trip['origin']['name']} to {trip['destination']['name']}, "
          f"{trip['seats_available']} seat(s) left. {args.clients} customers book 1 seat each, all at once.\n")

    start = threading.Barrier(args.clients)
    results = [None] * args.clients

    def customer(n):
        start.wait()
        status, body = call("POST", f"{api}/bookings",
                            {"trip_id": trip["id"], "passenger_name": f"Customer {n:02d}", "seats": 1})
        results[n] = (status, body.get("reference") or body["error"]["code"])

    threads = [threading.Thread(target=customer, args=(n,)) for n in range(args.clients)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for n, (status, outcome) in enumerate(results):
        print(f"  Customer {n:02d}: {status} {outcome}")
    summary = Counter(status for status, _ in results)
    _, after = call("GET", f"{api}/admin/trips?limit=100")
    final = next(t for t in after["trips"] if t["id"] == trip["id"])
    print(f"\nBooked: {summary.get(201, 0)}, refused: {summary.get(409, 0)}, other: "
          f"{sum(v for k, v in summary.items() if k not in (201, 409))}")
    print(f"Seats booked now: {final['seats_booked']} / {final['capacity']} (never more than capacity)")


if __name__ == "__main__":
    main()
