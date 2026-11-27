"""
Shared helpers for the PawHome "data pile" (Task 3): Iceberg tables + SQL catalog.

  data lake (Task 2)  = loose Parquet files in a bucket
  data pile (Task 3)  = Iceberg TABLES in a bucket + a CATALOG that knows them

The notebooks 04, 05 and 06 import this file, so the pile settings,
the catalog and the dlt destination are defined ONCE.
"""
import os
import sqlite3
import warnings

import dlt
import pandas as pd
from dlt.destinations import filesystem
from dlt.destinations.adapters import iceberg_adapter, iceberg_partition
from pyiceberg.catalog import load_catalog

# The first 'replace' into an empty table prints a harmless PyIceberg warning; hide it.
warnings.filterwarnings("ignore", message="Delete operation did not match any records")

from lake import LAKES, _fs

# ---------------------------------------------------------------------------
# 1. The piles: one bucket per object store, next to the Task 2 lake bucket.
#    Endpoint and passwords are the same as for the lakes (same Silo / RustFS).
# ---------------------------------------------------------------------------
PILES = {
    "silo": {**LAKES["silo"], "bucket": os.getenv("SILO_PILE_BUCKET", "pawhome-pile")},
    "rustfs": {**LAKES["rustfs"], "bucket": os.getenv("RUSTFS_PILE_BUCKET", "pawhome-pile")},
}

# Medallion architecture: bronze = raw copies of the sources (this task),
# silver = cleaned data, gold = data ready for reports (later tasks).
BRONZE = "bronze"

# The SQLite files of the catalogs live in the mounted work folder,
# so the catalog survives container restarts (like .dlt_pipelines).
CATALOG_DIR = os.getenv("PILE_CATALOG_DIR", "/home/jovyan/work/pile_catalog")


def catalog_name(pile: str = "silo") -> str:
    return f"pawhome_{pile}"


def catalog_properties(pile: str = "silo") -> dict:
    """
    Settings of the SQL catalog:
      uri        -> the SQLite database file that stores the table METADATA pointers
      warehouse  -> the bucket where Iceberg stores the table DATA and metadata files
      s3.*       -> how to reach the bucket (Silo or RustFS)
    """
    cfg = PILES[pile]
    os.makedirs(CATALOG_DIR, exist_ok=True)
    return {
        "type": "sql",
        "uri": f"sqlite:///{CATALOG_DIR}/{catalog_name(pile)}.db",
        "warehouse": f"s3://{cfg['bucket']}",
        "s3.endpoint": cfg["endpoint"],
        "s3.access-key-id": cfg["access_key"],
        "s3.secret-access-key": cfg["secret_key"],
        "s3.region": "us-east-1",
        "s3.path-style-access": "true",
    }


def get_catalog(pile: str = "silo"):
    """Open (or create on first use) the SQL catalog of a pile with PyIceberg."""
    return load_catalog(catalog_name(pile), **catalog_properties(pile))


def pile_destination(pile: str = "silo"):
    """dlt 'filesystem' destination that writes into the pile bucket."""
    cfg = PILES[pile]
    return filesystem(
        bucket_url=f"s3://{cfg['bucket']}",
        credentials={
            "aws_access_key_id": cfg["access_key"],
            "aws_secret_access_key": cfg["secret_key"],
            "endpoint_url": cfg["endpoint"],
            "region_name": "us-east-1",
        },
    )


def partition_by_ingestion_date(resource):
    """
    Iceberg partitioning: split the table's data files by the DAY of _ingested_at.
    The partition is called 'ingestion_date', so the data file keys look like
      bronze/<table>/data/ingestion_date=2026-11-06/<file>.parquet
    """
    return iceberg_adapter(resource, partition=iceberg_partition.day("_ingested_at", "ingestion_date"))


def run_to_pile(pipeline, data, write_disposition: str, pile: str = "silo") -> None:
    """
    Run a dlt pipeline into the pile as ICEBERG tables and print the new rows per table.

    Right before the run we tell dlt WHICH Iceberg catalog to register the tables in
    (without this, dlt would use a temporary in-memory catalog that is forgotten).
    """
    dlt.config["iceberg_catalog.iceberg_catalog_name"] = catalog_name(pile)
    dlt.config["iceberg_catalog.iceberg_catalog_type"] = "sql"
    dlt.config["iceberg_catalog.iceberg_catalog_config"] = catalog_properties(pile)

    pipeline.run(data, write_disposition=write_disposition,
                 table_format="iceberg", loader_file_format="parquet")
    counts = pipeline.last_trace.last_normalize_info.row_counts
    new_rows = {t: n for t, n in counts.items() if not t.startswith("_dlt")}
    print(f"[{pile}] new rows loaded:", new_rows or "none")


# ---------------------------------------------------------------------------
# 2. Helpers to LOOK at the pile from the notebooks
# ---------------------------------------------------------------------------
def ensure_pile_bucket(pile: str = "silo"):
    """Create the pile bucket if it doesn't exist yet (you can also create it in the console)."""
    fs = _fs(pile)
    bucket = PILES[pile]["bucket"]
    if not fs.exists(bucket):
        fs.mkdir(bucket)
        print(f"Created bucket {bucket} in {pile}")
    else:
        print(f"Bucket {bucket} already exists in {pile}")


def list_pile(prefix: str = "", pile: str = "silo") -> pd.DataFrame:
    """List the objects (data + metadata files) in the pile bucket under a prefix."""
    fs = _fs(pile)
    bucket = PILES[pile]["bucket"]
    fs.invalidate_cache()
    rows = []
    for path, info in fs.find(f"{bucket}/{prefix}", detail=True).items():
        rows.append({"key": path[len(bucket) + 1:], "size_kb": round(info["size"] / 1024, 1),
                     "last_modified": info.get("LastModified")})
    df = pd.DataFrame(rows, columns=["key", "size_kb", "last_modified"])
    return df.sort_values("key").reset_index(drop=True)


def show_catalog_db(pile: str = "silo") -> pd.DataFrame:
    """Show what the SQLite catalog database really contains: one row per Iceberg table."""
    path = catalog_properties(pile)["uri"].replace("sqlite:///", "")
    with sqlite3.connect(path) as con:
        return pd.read_sql(
            "SELECT table_namespace, table_name, metadata_location FROM iceberg_tables "
            "ORDER BY table_namespace, table_name", con)


def snapshots(table) -> pd.DataFrame:
    """One row per snapshot (= version) of an Iceberg table, oldest first."""
    rows = []
    for s in table.snapshots():
        summary = s.summary.additional_properties if s.summary else {}
        rows.append({
            "snapshot_id": s.snapshot_id,
            "committed_at": pd.to_datetime(s.timestamp_ms, unit="ms", utc=True),
            "operation": s.summary.operation.value if s.summary else None,
            "added_rows": int(summary.get("added-records", 0)),
            "deleted_rows": int(summary.get("deleted-records", 0)),
            "total_rows": int(summary.get("total-records", 0)),
            "schema_id": s.schema_id,
        })
    return pd.DataFrame(rows)


def data_files(table, snapshot_id=None) -> pd.DataFrame:
    """The Parquet data files that make up the table (at a snapshot, default = current)."""
    files = table.inspect.files() if snapshot_id is None else table.inspect.files(snapshot_id)
    df = files.select(["file_path", "record_count", "file_size_in_bytes"]).to_pandas()
    df["file_path"] = df["file_path"].str.replace(f"s3://{table.location().split('/')[2]}/", "", regex=False)
    return df


# ---------------------------------------------------------------------------
# 3. The bronze incremental load as one function (used again in Task 4, notebook 08)
#    = the same thing notebook 05 does step by step.
# ---------------------------------------------------------------------------
def run_bronze_incremental(pile: str = "silo") -> None:
    """Incremental dlt load PostgreSQL -> bronze.postgres_<table> (append on updated_at)."""
    from dlt.sources.sql_database import sql_table
    from lake import POSTGRES_URL, DB_TABLES, PIPELINES_DIR, add_metadata

    resources = []
    for name in DB_TABLES:
        r = sql_table(POSTGRES_URL, table=name, incremental=dlt.sources.incremental("updated_at"))
        r.apply_hints(table_name=f"postgres_{name}")
        add_metadata(r, source_system="postgres", source_resource=name, ingestion_type="incremental")
        partition_by_ingestion_date(r)
        resources.append(r)

    pipeline = dlt.pipeline(
        pipeline_name="pile_incremental" if pile == "silo" else f"pile_incremental_{pile}",
        destination=pile_destination(pile),
        dataset_name=BRONZE,
        pipelines_dir=PIPELINES_DIR,
    )
    run_to_pile(pipeline, resources, write_disposition="append", pile=pile)
