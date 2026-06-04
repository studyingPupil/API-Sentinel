"""Phase 2 — Database verification: init tables and print schema."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, engine
from sqlalchemy import inspect


def verify():
    print("Initializing database...")
    init_db()
    print("OK — tables created\n")

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print(f"Tables found: {len(tables)}\n")

    for table in sorted(tables):
        print(f"  [{table}]")
        cols = inspector.get_columns(table)
        for col in cols:
            pk = " (PK)" if col.get("primary_key") else ""
            nullable = "" if col["nullable"] else " NOT NULL"
            print(f"    {col['name']:<22} {str(col['type']):<18}{nullable}{pk}")
        fks = inspector.get_foreign_keys(table)
        for fk in fks:
            print(f"    FK: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
        print()

    # Verify seed data
    from app.database import SessionLocal
    from app.models import Setting
    db = SessionLocal()
    try:
        settings = db.query(Setting).all()
        print("Default settings seed:")
        for s in settings:
            print(f"  {s.key} = {s.value}")
    finally:
        db.close()


if __name__ == "__main__":
    verify()
