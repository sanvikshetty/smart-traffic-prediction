# Local database setup

1. In the repository root, copy `.env.example` to `.env`.
2. Open `.env` in VS Code.
3. Replace `ENTER_YOUR_POSTGRES_PASSWORD_HERE` with the password you created for PostgreSQL user `postgres`.
4. Save the file.
5. Never commit `.env` to GitHub.

Expected PostgreSQL settings:
- host: localhost
- port: 5432
- database: smart_traffic_db
- user: postgres

If Neo4j is installed later, fill its local password in the same `.env` file.
