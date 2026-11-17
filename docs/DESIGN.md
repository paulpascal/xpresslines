# Design

## Architecture
The customer and the operator use a React web app. It talks to a Flask API over JSON (`/api/v1`); nginx serves the app and forwards API calls, so the browser sees a single address. The API stores everything in PostgreSQL. See the [overview](diagrams/overview.png).

Inside the API, each layer has one job ([zoom](diagrams/zoom.png)): **`api/`** speaks HTTP, **`services/`** run the use cases (book, search, change a status), **`domain/`** holds the business rules (fares, booking rules, trip lifecycle), **`infra/`** talks to the database. The rules never depend on HTTP, so another channel (mobile, USSD) could reuse them.

## Data model
| Table | Holds | Rules the database enforces |
|---|---|---|
| `towns` | code, name, zone | zone from 1 to 4 |
| `trips` | origin, destination, departure time, capacity, seats booked, status | seats booked between 0 and capacity; origin differs from destination; status is one of the 6 stages |
| `bookings` | reference, trip, passenger, seats, fare paid, retry key | at least 1 seat; unique reference |

## Choices
**Flask:** the work is short database transactions, and the hard part is two people booking the last seat. Each request opens one transaction, and SQLAlchemy gives direct control of the locking. **React with Mantine:** ready-made components, so the two views are quick to build and consistent.

## Three trade-offs
| I chose | I gave up | Because |
|---|---|---|
| **Lock the trip row** while booking | bookings on the same bus wait their turn | the wait is milliseconds, other buses are unaffected, and seats left are checked again under the lock, so two people can never get the last seat |
| **A seat counter on each trip** | a single source of truth: the counter could disagree with the bookings | seats left is instant to read; counter and booking are written in one transaction, the database refuses more than capacity, and a check command catches drift |
| **Fares in code** | operators can't change prices without a release | 10 fixed fares, all tested; each booking keeps its price, so moving fares to the database later changes no history |

## Scaling to 50 routes and 10,000 bookings a day
10,000 a day is about one booking every 9 seconds; even an assumed 20x festive peak is 2 to 3 a second. A short load test on one laptop did 227 bookings a second, all on one bus (32 clients), so the next steps are about safety, not speed:
1. Managed database with backups, and error tracking.
2. Two or more API servers behind a load balancer (the API keeps no state, so no code change).
3. A read-only copy of the database for search and the dashboard; booking still checks the main database.
4. A queue for slow work (SMS, payment callbacks), so it never delays a booking.

## Monitoring
- **Log** each request, booking and refusal (with its reason) as one JSON line with a request id.
- **Watch** bookings per minute, refusals by reason, p95 booking time, errors, lock waits, pool use.
- **Alert** when errors pass 1% for 5 minutes, bookings stop in selling hours, the seat check finds drift, or health checks fail.
