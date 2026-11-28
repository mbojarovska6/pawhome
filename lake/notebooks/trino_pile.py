"""
Helpers for Task 5: send SQL to the Trino cluster from JupyterLab.

Trino is a distributed SQL engine: the COORDINATOR (trino-coordinator) plans each query,
the two WORKERS execute it. Notebooks 10 and 11 import this file.
"""
import os
import time

import pandas as pd
import trino

TRINO_HOST = os.getenv("TRINO_HOST", "trino-coordinator")
TRINO_UI = "http://localhost:8080/ui/"          # open this in your browser (any username)


def connect():
    """Connection to the coordinator (port 8080). No password: authentication is not enabled locally."""
    return trino.dbapi.connect(host=TRINO_HOST, port=8080, user="pawhome", http_scheme="http")


def run(query: str):
    """Run one SQL statement. Returns (DataFrame with the result, statistics of the query)."""
    cur = connect().cursor()
    cur.execute(query)
    rows = cur.fetchall()                       # waits until the query has finished
    columns = [c[0] for c in cur.description] if cur.description else []
    stats = dict(cur.stats or {})
    stats["query_id"] = cur.query_id
    return pd.DataFrame(rows, columns=columns), stats


def sql(query: str) -> pd.DataFrame:
    """Run one SQL statement and return only the result table."""
    return run(query)[0]


def query_stats(stats: dict) -> dict:
    """The numbers that show how much work a query did (used for partition pruning)."""
    return {
        "rows read": stats.get("processedRows"),
        "bytes read": stats.get("processedBytes"),
        "physical input bytes": stats.get("physicalInputBytes"),
        "splits (file pieces)": stats.get("totalSplits"),
        "elapsed ms": stats.get("elapsedTimeMillis"),
        "Trino UI": f"{TRINO_UI}query.html?{stats.get('query_id')}",
    }


def explain(query: str, keep=None) -> str:
    """Print Trino's query plan. keep = list of words: also print only the lines containing them."""
    plan = sql(f"EXPLAIN {query}").iloc[0, 0]
    if keep:
        print("\n".join(line for line in plan.splitlines() if any(k in line for k in keep)))
    return plan


def wait_for_cluster(expected_nodes: int = 3, timeout_s: int = 180) -> pd.DataFrame:
    """Wait until the coordinator and both workers are up and registered."""
    start = time.time()
    while True:
        try:
            nodes = sql("SELECT node_id, http_uri, node_version, coordinator, state FROM system.runtime.nodes")
            if len(nodes[nodes.state == "active"]) >= expected_nodes:
                return nodes.sort_values("coordinator", ascending=False).reset_index(drop=True)
        except Exception as error:                       # coordinator still starting
            last_error = error
        if time.time() - start > timeout_s:
            raise TimeoutError(f"Trino cluster not ready after {timeout_s}s: {locals().get('last_error', 'too few nodes')}")
        time.sleep(5)
