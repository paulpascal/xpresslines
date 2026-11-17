# Handover note

Welcome. The README gets you running in a few minutes. Before and after every change, run `make lint` and `make test`; CI runs the same. Three things matter most.

## 1. Seats change in one place only
**The rule:** only `BookingService.book` (`services/booking.py`) adds seats to a trip.

**Why:** each trip keeps a running count of its booked seats. It stays correct because one function updates it: it locks the trip, checks the seats left, then writes the booking and the count in the same transaction. So bookings can never go past the bus capacity.

**In practice:**
- Never add or remove bookings anywhere else: not in a new endpoint, a script, or a manual SQL fix. A future cancellation should be a new method on `BookingService` that locks the trip the same way and gives the seats back in the same transaction.
- Keep the lock short: no SMS or payment calls while a trip is locked. Send them after the booking is saved (see `domain/events.py`). These events run in the same process, so one can be lost if the server stops right after saving; before real SMS or payments, add an outbox table.
- `tests/test_concurrency.py` sends real parallel bookings. If it fails, don't merge.

## 2. Business rules live in `domain/` and `services/`, never in routes or the UI
**The rule:** `api/` only translates HTTP; the frontend only displays. Every rule lives in the backend, and every rule has a test.

**In practice:**
- A new booking rule (for example, sales close 30 minutes before departure) is one small function added to `domain/booking_rules.py`.
- A new trip status (for example, Cancelled) is one line in `domain/lifecycle.py`, plus a migration for the database status check.
- A new way of pricing is a new class in `domain/pricing.py`, chosen in `app/__init__.py`. Each booking keeps the price it was sold at.
- Refusals raise an error from `domain/errors.py`; the API turns them into a clear message automatically.

## 3. Time, money and database changes need care
- **Time:** the database stores UTC; people think in Lagos time (one setting, `OPERATOR_TZ` in `config.py`). Convert only when displaying or searching. A search date means a Lagos calendar day.
- **Money:** use exact decimals, never floats. Every amount carries its currency.
- **Database:** change `domain/models.py`, generate a migration with Alembic, **read it**, then apply it. Prefer adding over changing, so the version still running keeps working with the new schema and a deploy never needs downtime.
- **Retries:** apps may resend a booking with the same `Idempotency-Key`; the customer gets the same booking back, not a second one. Keep this working: mobile networks drop responses.

**Next, in order:** login for operators; online payment with seats held for a few minutes; cancellations and refunds; rate limiting; SMS with the booking reference.
