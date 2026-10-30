"""
Shared helpers for the PawHome data lake notebooks (Task 2).

All three notebooks import this file, so the lake settings, the object key
layout and the metadata columns are defined ONCE (same idea as crud.js in Task 1).
"""
import os
from datetime import datetime, timezone

import dlt
import pandas as pd
import pyarrow.dataset as ds
import s3fs
from dlt.destinations import filesystem

# ---------------------------------------------------------------------------
# 1. Object key layout required by the task:
#    <source_system>/<resource>/ingestion_date=<YYYY-MM-DD>/<load_id>.<file_id>.parquet
#
#    dlt puts every file under   <bucket>/<dataset_name>/<layout>
#    so we use dataset_name = source system ("postgres", "dogceo") and this layout:
# ---------------------------------------------------------------------------
LAYOUT = "{table_name}/ingestion_date={YYYY}-{MM}-{DD}/{load_id}.{file_id}.{ext}"

# Where dlt keeps its local state (last loaded values for incremental loads).
# It lives in the mounted work folder, so it survives container restarts.
PIPELINES_DIR = os.getenv("DLT_PIPELINES_DIR", "/home/jovyan/work/.dlt_pipelines")

# ---------------------------------------------------------------------------
# 2. The two lakes. Values come from environment variables set in
#    docker-compose.yml; the defaults are for running inside Docker.
# ---------------------------------------------------------------------------
LAKES = {
    # Main lake: Silo (S3-compatible, MinIO fork)
    "silo": {
        "endpoint": os.getenv("SILO_ENDPOINT", "http://silo:9000"),
        "access_key": os.getenv("SILO_ACCESS_KEY", "silo-admin"),
        "secret_key": os.getenv("SILO_SECRET_KEY", "silo-password-123"),
        "bucket": os.getenv("SILO_BUCKET", "pawhome-lake"),
    },
    # Additional lake (bonus): RustFS, another S3-compatible store
    "rustfs": {
        "endpoint": os.getenv("RUSTFS_ENDPOINT", "http://rustfs:9000"),
        "access_key": os.getenv("RUSTFS_ACCESS_KEY", "rustfs-admin"),
        "secret_key": os.getenv("RUSTFS_SECRET_KEY", "rustfs-password-123"),
        "bucket": os.getenv("RUSTFS_BUCKET", "pawhome-lake"),
    },
}

# "postgresql+psycopg2" = PostgreSQL, using the psycopg2 driver (installed from requirements.txt).
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql+psycopg2://pawhome:pawhome@db:5432/pawhome")

# The four tables of the operational database.
DB_TABLES = ["shelters", "adopters", "animals", "applications"]
def lake_destination(lake: str = "silo"):
    """Return a dlt 'filesystem' destination that writes into the chosen lake's bucket."""
    cfg = LAKES[lake]
    return filesystem(
        bucket_url=f"s3://{cfg['bucket']}",
        credentials={
            "aws_access_key_id": cfg["access_key"],
            "aws_secret_access_key": cfg["secret_key"],
            "endpoint_url": cfg["endpoint"],
            "region_name": "us-east-1",
        },
        layout=LAYOUT,
    )

def add_metadata(resource, source_system: str, source_resource: str, ingestion_type: str):
    """
    Add the technical metadata columns to every row of a dlt resource:
      _source_system   where the data comes from     (e.g. "postgres")
      _source_resource which table / endpoint         (e.g. "animals")
      _ingestion_type  "full" or "incremental"
      _ingested_at     when this run happened (UTC), same value for all rows of one run
      _load_id         the dlt load id of this run (also used in the file name)
    """
    ingested_at = datetime.now(timezone.utc)

    def _add(row):
        row["_source_system"] = source_system
        row["_source_resource"] = source_resource
        row["_ingestion_type"] = ingestion_type
        row["_ingested_at"] = ingested_at
        row["_load_id"] = dlt.current.load_package_state()["load_id"]
        return row

    resource.add_map(_add)
    return resource

# ---------------------------------------------------------------------------
# 3. Helpers to LOOK at the lake from the notebook
# ---------------------------------------------------------------------------
def _fs(lake: str = "silo") -> s3fs.S3FileSystem:
    cfg = LAKES[lake]
    return s3fs.S3FileSystem(
        key=cfg["access_key"],
        secret=cfg["secret_key"],
        client_kwargs={"endpoint_url": cfg["endpoint"]},
    )

def ensure_bucket(lake: str):
    """Create the lake's bucket if it doesn't exist yet (used for the RustFS lake)."""
    fs = _fs(lake)
    bucket = LAKES[lake]["bucket"]
    if not fs.exists(bucket):
        fs.mkdir(bucket)
        print(f"Created bucket {bucket} in {lake}")
    else:
        print(f"Bucket {bucket} already exists in {lake}")

def list_lake(prefix: str = "", lake: str = "silo", only_parquet: bool = True) -> pd.DataFrame:
    """List the objects in the lake under a prefix, e.g. list_lake('postgres/animals')."""
    fs = _fs(lake)
    bucket = LAKES[lake]["bucket"]
    fs.invalidate_cache()
    rows = []
    for path, info in fs.find(f"{bucket}/{prefix}", detail=True).items():
        key = path[len(bucket) + 1:]
        if only_parquet and not key.endswith(".parquet"):
            continue
        rows.append({"key": key, "size_kb": round(info["size"] / 1024, 1),
                     "last_modified": info.get("LastModified")})
    df = pd.DataFrame(rows, columns=["key", "size_kb", "last_modified"])
    return df.sort_values("key").reset_index(drop=True)

def read_lake(prefix: str, lake: str = "silo") -> pd.DataFrame:
    """Read ALL parquet files under a prefix into one pandas DataFrame."""
    fs = _fs(lake)
    bucket = LAKES[lake]["bucket"]
    fs.invalidate_cache()
    files = [p for p in fs.find(f"{bucket}/{prefix}") if p.endswith(".parquet")]
    if not files:
        return pd.DataFrame()
    return ds.dataset(files, filesystem=fs, format="parquet").to_table().to_pandas()