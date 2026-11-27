"""
Show the INTERNAL STRUCTURE of an Avro file and a Parquet file (Task 4, part 1).
Code generated with an AI assistant (Claude) and checked by running it on files written by Spark.

  Avro    = ROW-based   : header (magic, schema, codec, sync marker) + blocks of whole rows
  Parquet = COLUMN-based: magic + row groups -> column chunks -> pages ... + footer with all metadata
"""
import io
import json
import struct

import fastavro
import pandas as pd
import pyarrow.parquet as pq


# ============================================================================ helpers
def hexdump(data: bytes, start: int = 0, width: int = 16) -> str:
    """Classic hex view: offset | hex bytes | printable characters."""
    lines = []
    for i in range(0, len(data), width):
        chunk = data[i:i + width]
        hexes = " ".join(f"{b:02x}" for b in chunk)
        text = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{start + i:08x}  {hexes:<{width * 3}} |{text}|")
    return "\n".join(lines)


# ============================================================================ AVRO
def _read_long(f) -> int:
    """Avro 'long' = variable-length zig-zag integer."""
    shift, result = 0, 0
    while True:
        b = f.read(1)
        if not b:
            raise EOFError
        b = b[0]
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            break
        shift += 7
    return (result >> 1) ^ -(result & 1)


def _read_bytes(f) -> bytes:
    return f.read(_read_long(f))


def inspect_avro(path: str, show_records: int = 3) -> dict:
    """
    Walk through an Avro Object Container File byte by byte:
      [magic 'Obj\\x01'] [metadata map: avro.schema, avro.codec] [16-byte sync marker]
      then repeated blocks: [number of rows] [block size in bytes] [rows (maybe compressed)] [sync marker]
    """
    raw = open(path, "rb").read()
    f = io.BytesIO(raw)

    magic = f.read(4)
    metadata = {}
    while True:                                   # the metadata map is written in blocks
        count = _read_long(f)
        if count == 0:
            break
        if count < 0:
            _read_long(f)
            count = -count
        for _ in range(count):
            key = _read_bytes(f).decode()
            metadata[key] = _read_bytes(f)
    sync = f.read(16)
    header_size = f.tell()

    blocks = []
    while f.tell() < len(raw):
        start = f.tell()
        rows = _read_long(f)
        size = _read_long(f)
        f.seek(size, 1)
        marker_ok = f.read(16) == sync
        blocks.append({"block": len(blocks), "starts_at_byte": start, "rows": rows,
                       "data_bytes": size, "sync_marker_ok": marker_ok})

    schema = json.loads(metadata["avro.schema"])
    with open(path, "rb") as fh:
        records = [r for _, r in zip(range(show_records), fastavro.reader(fh))]

    print("=" * 78)
    print(f"AVRO FILE: {path.split('/')[-1]}  ({len(raw):,} bytes)")
    print("=" * 78)
    print(f"1) magic bytes        : {magic!r}   (every Avro file starts with 'Obj' + version 1)")
    print(f"2) codec (compression): {metadata.get('avro.codec', b'null').decode()}")
    print(f"3) sync marker        : {sync.hex()}   (16 random bytes, repeated after every block)")
    print(f"4) header size        : {header_size} bytes  (the WHOLE schema is stored inside the file)")
    print(f"5) data blocks        : {len(blocks)} block(s), {sum(b['rows'] for b in blocks)} rows in total")
    print("\nFirst 96 bytes of the file:")
    print(hexdump(raw[:96]))
    return {
        "schema_fields": pd.DataFrame([{"field": fld["name"], "avro type": json.dumps(fld["type"])}
                                       for fld in schema["fields"]]),
        "blocks": pd.DataFrame(blocks),
        "first_records": pd.DataFrame(records),
    }


# ============================================================================ PARQUET
def inspect_parquet(path: str) -> dict:
    """
    Parquet layout:
      [magic 'PAR1'] [row group 1: column chunk 1, column chunk 2, ...] [row group 2] ...
      [footer = FileMetaData (schema, row groups, column statistics)] [4-byte footer length] [magic 'PAR1']
    """
    raw = open(path, "rb").read()
    footer_len = struct.unpack("<I", raw[-8:-4])[0]
    pf = pq.ParquetFile(path)
    meta = pf.metadata

    print("=" * 78)
    print(f"PARQUET FILE: {path.split('/')[-1]}  ({len(raw):,} bytes)")
    print("=" * 78)
    print(f"1) magic at start / end : {raw[:4]!r} / {raw[-4:]!r}")
    print(f"2) footer (metadata)    : {footer_len:,} bytes, stored at the END of the file")
    print(f"3) written by           : {meta.created_by}")
    print(f"4) rows / columns       : {meta.num_rows} rows, {meta.num_columns} columns")
    print(f"5) row groups           : {meta.num_row_groups}  (each row group stores every column separately)")
    print("\nFirst 48 bytes:")
    print(hexdump(raw[:48]))
    print("\nLast 48 bytes (end of footer, footer length, 'PAR1'):")
    print(hexdump(raw[-48:], start=len(raw) - 48))

    schema_rows = []
    for i in range(meta.num_columns):
        col = pf.schema.column(i)
        schema_rows.append({"column": col.name, "physical type": col.physical_type,
                            "logical type": str(col.logical_type), "max definition level": col.max_definition_level})

    chunk_rows = []
    for rg in range(meta.num_row_groups):
        group = meta.row_group(rg)
        for c in range(group.num_columns):
            ch = group.column(c)
            st = ch.statistics
            chunk_rows.append({
                "row_group": rg,
                "column": ch.path_in_schema,
                "compression": ch.compression,
                "encodings": ", ".join(ch.encodings),
                "compressed_bytes": ch.total_compressed_size,
                "uncompressed_bytes": ch.total_uncompressed_size,
                "dictionary_page_at": ch.dictionary_page_offset,
                "data_page_at": ch.data_page_offset,
                "min": st.min if st is not None and st.has_min_max else None,
                "max": st.max if st is not None and st.has_min_max else None,
                "nulls": st.null_count if st is not None else None,
            })
    return {"schema": pd.DataFrame(schema_rows), "column_chunks": pd.DataFrame(chunk_rows)}
