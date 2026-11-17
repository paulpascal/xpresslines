# Local development without Docker for the API and UI (Postgres still runs in Docker).
.PHONY: db setup migrate seed reseed api web test lint race check

db:        ## start PostgreSQL only
	docker compose up -d db
setup:     ## install backend and frontend dependencies
	cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
	cd frontend && npm install
migrate:
	cd backend && .venv/bin/alembic upgrade head
seed:      ## load demo data if the database is empty
	cd backend && .venv/bin/flask --app app seed
reseed:    ## wipe everything and load fresh demo data
	cd backend && .venv/bin/flask --app app seed --reset
api:       ## Flask API on :8000
	cd backend && .venv/bin/flask --app app run --port 8000 --debug
web:       ## Vite dev server on :5173 (proxies /api to :8000)
	cd frontend && npm run dev
test:      ## backend tests (real PostgreSQL) and frontend unit tests
	cd backend && .venv/bin/pytest
	cd frontend && npm test
lint:      ## what CI checks: style, types, migrations in sync with models
	cd backend && .venv/bin/ruff check . && .venv/bin/mypy && .venv/bin/alembic check
race:      ## 20 customers race for the last seats of a trip
	python3 scripts/race_last_seat.py --clients 20
check:     ## verify every seat counter matches its bookings
	cd backend && .venv/bin/flask --app app check-seats
