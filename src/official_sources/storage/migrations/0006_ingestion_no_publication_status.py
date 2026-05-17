from __future__ import annotations

CHECKSUM_INPUT = """
Allow ingestion_runs.status='no_publication'.
"""

OLD_STATUS_CHECK = "CHECK(status IN ('pending', 'success', 'partial', 'failed'))"
NEW_STATUS_CHECK = "CHECK(status IN ('pending', 'success', 'partial', 'failed', 'no_publication'))"


def apply(connection) -> None:
    row = connection.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table' AND name = 'ingestion_runs'
        """
    ).fetchone()
    if row is None:
        return
    current_sql = row["sql"]
    if "no_publication" in current_sql:
        return
    if OLD_STATUS_CHECK not in current_sql:
        raise RuntimeError("Cannot update ingestion_runs status CHECK constraint")

    updated_sql = current_sql.replace(OLD_STATUS_CHECK, NEW_STATUS_CHECK)
    schema_version = connection.execute("PRAGMA schema_version").fetchone()[0]
    connection.execute("PRAGMA writable_schema=ON")
    connection.execute(
        """
        UPDATE sqlite_master
        SET sql = ?
        WHERE type = 'table' AND name = 'ingestion_runs'
        """,
        (updated_sql,),
    )
    connection.execute("PRAGMA writable_schema=OFF")
    connection.execute(f"PRAGMA schema_version = {schema_version + 1}")
