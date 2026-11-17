# AI Use Disclosure

## Which parts did I write myself, and which were AI-assisted?

I owned the core engineering decisions and implementation, particularly the parts that define the system's behavior and correctness.

I designed and implemented the domain model, including fare rules, trip lifecycle, and booking constraints. I also implemented the core services, with particular attention to concurrency and the scenario where multiple customers attempt to book the last available seat simultaneously.

The API, application configuration, and frontend structure were also implemented by me, including the hooks, booking flow, and dashboard.

I used Claude (Anthropic) as an implementation assistant for the following:

- **Seed data:** I defined the fleet, trip scenarios, and initial data requirements, including realistic vehicle capacities, trips already in progress, and a vehicle with exactly one seat remaining for demonstration purposes. Claude implemented the seed command.
- **Unit tests:** I defined the test strategy, specifying the scenarios, edge cases, and expected behavior each test needed to validate. Claude assisted with implementation. I reviewed, adjusted, and verified the resulting tests.
- **Development environment:** Claude assisted with the Docker setup and Makefile to provide a consistent, one-command startup experience.
- **Frontend styling:** Claude assisted with selected visual details, particularly the remaining-seat indicators and progress bars on trip cards and the dashboard.
- **Documentation:** I maintained technical notes throughout development. Claude helped turn those notes into the README, design note, and handover documentation, which I subsequently reviewed and edited.

## Which tools did I use?

Claude (Anthropic).

## How did I validate AI-assisted contributions?

I treated AI-generated output like any other external contribution: it had to be reviewed, understood, and verified before being accepted.

My validation process included:

- Reviewing every change before integration. I retained no implementation that I could not explain or justify.
- Running the complete test suite against a real PostgreSQL database rather than relying on mocks for database behavior.
- Performing a deliberate concurrency regression experiment. I removed the row-level lock to verify that the concurrency tests would detect the resulting race condition. With twenty concurrent customers competing for five available seats, the unlocked implementation allowed all twenty bookings to succeed. Restoring the lock produced the expected behavior, and the tests passed.
- Checking the seed data and documentation against the original requirements to ensure consistency.

## Where did I deliberately avoid using AI, and why?

I deliberately kept the domain design, core business logic, service implementation, API contract, and application configuration under my direct ownership.

These areas define the system's behavior, enforce its business invariants, and establish the contracts other components depend on. They are also the areas I would be responsible for maintaining, debugging, and defending in a production environment.

I wanted to reason through these decisions myself and establish the implementation before using AI to accelerate supporting work.

My approach was to use AI to assist with execution, not to delegate engineering ownership.
