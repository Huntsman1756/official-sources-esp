from __future__ import annotations

import argparse

from official_sources.sources.boe.ingestion import ingest_boe_summary
from official_sources.storage.database import connect, initialize_database
from official_sources.storage.repository import OfficialSourcesRepository


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest one BOE daily summary into SQLite.")
    parser.add_argument("target_date", help="Publication date in YYYY-MM-DD format.")
    parser.add_argument("--database", default="official-sources.sqlite")
    args = parser.parse_args()

    connection = connect(args.database)
    initialize_database(connection)
    repository = OfficialSourcesRepository(connection)
    repository.ensure_official_source_boe()
    run = ingest_boe_summary(repository, target_date=args.target_date)
    print(run)


if __name__ == "__main__":
    main()
