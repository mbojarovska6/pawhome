"""
Shared helpers for Task 4 (Spark): the Spark session, and moving data between
Spark and the Iceberg tables of the pile.

  Spark      = does the PROCESSING (cleaning, joins, aggregations, machine learning)
  PyIceberg  = reads and writes the ICEBERG TABLES in the pile catalog (same catalog as Task 3)

Data travels between the two as Apache Arrow tables (fast, column-based, no copying row by row).
Notebooks 07, 08 and 09 import this file.
"""
import glob
import os

import pyarrow as pa
import pyspark
from pyspark.sql import SparkSession
from pyiceberg.expressions import AlwaysTrue

from lake import LAKES
from pile import get_catalog, snapshots, data_files  # noqa: F401  (re-exported for the notebooks)

# Where Part 1 writes its files: the Task 2 lake bucket in Silo, read through Hadoop's S3A connector.
LAKE_URI = os.getenv("LAKE_URI", f"s3a://{LAKES['silo']['bucket']}")


def _hadoop_version() -> str:
    """The Hadoop version bundled with PySpark (hadoop-aws must use exactly the same version)."""
    jars = glob.glob(os.path.join(os.path.dirname(pyspark.__file__), "jars", "hadoop-client-api-*.jar"))
    return os.path.basename(jars[0])[len("hadoop-client-api-"):-len(".jar")] if jars else "3.4.1"


def get_spark(app_name: str = "pawhome") -> SparkSession:
    """
    Start (or reuse) a Spark session in LOCAL MODE: driver and executors run inside this
    JupyterLab container and use all its CPU cores (local[*]).

    Extra packages (downloaded from Maven the first time, then cached):
      spark-avro  -> read/write Avro files
      hadoop-aws  -> the S3A connector, so Spark can read/write s3a://pawhome-lake/... in Silo
    """
    silo = LAKES["silo"]
    packages = [
        f"org.apache.spark:spark-avro_2.13:{pyspark.__version__}",
        f"org.apache.hadoop:hadoop-aws:{_hadoop_version()}",
    ]
    builder = (
        SparkSession.builder
        .master("local[*]")
        .appName(app_name)
        .config("spark.driver.memory", "2g")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.shuffle.partitions", "8")              # small data -> few partitions
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .config("spark.ui.showConsoleProgress", "false")              # no progress bars in the notebook
        # S3A = how Spark talks to Silo
        .config("spark.hadoop.fs.s3a.endpoint", silo["endpoint"])
        .config("spark.hadoop.fs.s3a.endpoint.region", "us-east-1")
        .config("spark.hadoop.fs.s3a.access.key", silo["access_key"])
        .config("spark.hadoop.fs.s3a.secret.key", silo["secret_key"])
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.aws.credentials.provider",
                "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
    )
    if os.getenv("SPARK_OFFLINE") != "1":       # only for testing without internet
        builder = builder.config("spark.jars.packages", ",".join(packages))
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark


# ---------------------------------------------------------------------------
# Files in the lake (Part 1)
# ---------------------------------------------------------------------------
def list_files(spark, path: str):
    """List the files under a path (s3a:// or file://) with Hadoop's FileSystem API -> [(relative name, bytes)]."""
    jvm = spark._jvm
    hpath = jvm.org.apache.hadoop.fs.Path(path)
    fs = hpath.getFileSystem(spark._jsc.hadoopConfiguration())
    if not fs.exists(hpath):
        return []
    out, it = [], fs.listFiles(hpath, True)
    base = fs.makeQualified(hpath).toString().rstrip("/") + "/"
    while it.hasNext():
        status = it.next()
        out.append((status.getPath().toString().replace(base, ""), status.getLen()))
    return sorted(out)


def copy_to_local(spark, path: str, local_dir: str) -> str:
    """Download one file from the lake to the container's disk (to inspect it with Python libraries)."""
    jvm = spark._jvm
    src = jvm.org.apache.hadoop.fs.Path(path)
    fs = src.getFileSystem(spark._jsc.hadoopConfiguration())
    os.makedirs(local_dir, exist_ok=True)
    target = os.path.join(local_dir, os.path.basename(path))
    fs.copyToLocalFile(False, src, jvm.org.apache.hadoop.fs.Path(f"file://{os.path.abspath(target)}"), True)
    return target


# ---------------------------------------------------------------------------
# Iceberg tables <-> Spark DataFrames (Part 2 and 3)
# ---------------------------------------------------------------------------
def read_iceberg(spark, identifier: str, row_filter=AlwaysTrue(), snapshot_id=None, pile: str = "silo"):
    """Read an Iceberg table of the pile (optionally filtered / at an old snapshot) into a Spark DataFrame."""
    table = get_catalog(pile).load_table(identifier)
    arrow = table.scan(row_filter=row_filter, snapshot_id=snapshot_id).to_arrow()
    return spark.createDataFrame(arrow)


def _all_optional(schema: pa.Schema) -> pa.Schema:
    """Make every column nullable, so later writes never clash with NOT NULL columns."""
    return pa.schema([f.with_nullable(True) for f in schema])


def write_iceberg(df, identifier: str, mode: str = "overwrite", join_cols=None,
                  partition_by=None, pile: str = "silo"):
    """
    Write a Spark DataFrame into an Iceberg table registered in the pile catalog.

      mode="overwrite" -> replace the table content (new snapshot)
      mode="append"    -> add rows (new snapshot)
      mode="upsert"    -> MERGE by join_cols: update rows that exist, insert new ones

    partition_by: list of (source_column, transform, partition_name) used when the table is CREATED,
                  e.g. [("month_start", MonthTransform(), "month")]
    Returns the table.
    """
    catalog = get_catalog(pile)
    arrow = df.toArrow()
    arrow = arrow.cast(_all_optional(arrow.schema))
    namespace = identifier.split(".")[0]
    catalog.create_namespace_if_not_exists(namespace)

    if not catalog.table_exists(identifier):
        table = catalog.create_table(identifier, schema=arrow.schema)
        if partition_by:
            with table.update_spec() as spec:
                for source, transform, name in partition_by:
                    spec.add_field(source, transform, name)
    table = catalog.load_table(identifier)

    # new columns in the data -> add them to the table (schema evolution, like in Task 3)
    with table.update_schema() as update:
        update.union_by_name(arrow.schema)
    table = catalog.load_table(identifier)

    if mode == "overwrite":
        table.overwrite(arrow)
    elif mode == "append":
        table.append(arrow)
    elif mode == "upsert":
        if arrow.num_rows:
            result = table.upsert(arrow, join_cols=join_cols)
            print(f"{identifier}: {result.rows_updated} rows updated, {result.rows_inserted} rows inserted")
        else:
            print(f"{identifier}: nothing new")
    else:
        raise ValueError(mode)
    return catalog.load_table(identifier)
