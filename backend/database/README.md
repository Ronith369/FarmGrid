# FarmGrid Database

The demo uses SQLite by default because it is the easiest persistent database for a hackathon demo. The file `farmgrid.db` is created by the seed script and is **not deleted when the API restarts**.

## One-time setup
From the project root:
```bash
python database/seed/seed_demo.py
```

This creates demo users, farms, machinery, labour providers, buyer orders and sample requests/bookings. It is idempotent: running it again does not duplicate the demo records.

For a multi-user deployment, change `DATABASE_URL` to PostgreSQL. The SQLAlchemy models in the backend are already designed for that migration.
