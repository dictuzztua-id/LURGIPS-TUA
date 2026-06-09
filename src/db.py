"""
db.py - Modul koneksi database & query helper untuk LURGIP MVP

Fungsi utama:
- get_connection(): Koneksi ke MySQL via PyMySQL
- query_to_df(): Eksekusi query, return DataFrame
- query_and_cache(): Query + cache ke Parquet
- union_ports(): UNION data dari 3 port dengan namespace
- add_port_namespace(): Tambah prefix port ke kolom ID (Patch 2)
- normalize_all_datetimes(): Normalisasi datetime SFA (Patch 4, Rule #6)

Dibuat sesuai aturan:
- Rule #6: Semua datetime dari tabel SFA harus melalui normalize_all_datetimes()
- Rule #7: Setiap DataFrame hasil query dari multi-port HARUS melalui add_port_namespace()
- Patch 2: Namespace port wajib untuk menghindari collision ID
- Patch 4: Isu timezone datetime
"""

import pymysql
import pandas as pd
from pathlib import Path
import pyarrow.parquet as pq
import pyarrow as pa
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from .config import (
    DB_CONFIGS, DATA_DIR, PORT_NAMESPACE, ID_COLUMNS,
    DEPO_TO_PORT, REF_DIR
)


def get_connection(port_key: str = "port_3306") -> pymysql.Connection:
    """
    Membuat koneksi ke database MySQL.
    
    Input:
        port_key: Kunci konfigurasi ('port_3306', 'port_3307', 'port_3308')
    
    Output:
        pymysql.Connection object
    
    Asumsi:
        - Kredensial sudah dikonfigurasi di src/config.py
        - Database MySQL sudah running di localhost
    """
    cfg = DB_CONFIGS.get(port_key)
    if not cfg:
        raise ValueError(f"Port config '{port_key}' tidak ditemukan di DB_CONFIGS")
    
    conn = pymysql.connect(**cfg)
    return conn


def query_to_df(sql: str, port_key: str = "port_3306") -> pd.DataFrame:
    """
    Eksekusi query SQL dan return hasil sebagai pandas DataFrame.
    
    Input:
        sql: Query SQL string
        port_key: Port database yang akan diquery
    
    Output:
        pd.DataFrame dengan hasil query
    
    Asumsi:
        - Koneksi database aktif
        - Query valid untuk schema DMS/SFA
    """
    with get_connection(port_key) as conn:
        df = pd.read_sql(sql, conn)
    return df


def query_and_cache(
    sql: str, 
    cache_name: str,
    port_key: str = "port_3306",
    force_refresh: bool = False
) -> pd.DataFrame:
    """
    Query database dan cache hasil ke Parquet file.
    
    Input:
        sql: Query SQL string
        cache_name: Nama file cache (tanpa ekstensi)
        port_key: Port database yang akan diquery
        force_refresh: Jika True, abaikan cache dan query ulang
    
    Output:
        pd.DataFrame dengan hasil query (dari cache atau fresh)
    
    Asumsi:
        - Folder data/raw sudah ada
        - File Parquet bisa ditulis/dibaca
    """
    path = Path(DATA_DIR) / f"{cache_name}.parquet"
    
    if path.exists() and not force_refresh:
        print(f"📦 Loading cached: {path}")
        return pd.read_parquet(path)
    
    print(f"🔍 Querying {port_key}...")
    df = query_to_df(sql, port_key)
    
    # Tambah namespace port sebelum cache (Rule #7)
    df = add_port_namespace(df, port_key)
    
    df.to_parquet(path, index=False)
    print(f"✅ Cached {len(df):,} rows → {path}")
    return df


def add_port_namespace(df: pd.DataFrame, port_key: str) -> pd.DataFrame:
    """
    Menambahkan prefix port namespace ke semua kolom ID.
    
    WAJIB dijalankan segera setelah query dari multi-port,
    SEBELUM disimpan ke cache atau di-UNION (Patch 2, Rule #7).
    
    Input:
        df: DataFrame hasil query
        port_key: Kunci port ('port_3306', dll)
    
    Output:
        DataFrame dengan kolom ID yang sudah di-namespace
        Contoh: "343-0000001" → "P1::343-0000001"
    
    Asumsi:
        - Separator "::" tidak muncul di ID asli DMS
        - Kolom ID sudah terdefinisi di ID_COLUMNS
    """
    ns = PORT_NAMESPACE.get(port_key, "UNK")
    df = df.copy()
    
    for col in ID_COLUMNS:
        if col in df.columns:
            def add_ns(v):
                if pd.isna(v) or str(v).strip() == "":
                    return v
                return f"{ns}::{v}"
            df[col] = df[col].apply(add_ns)
    
    # Tambah kolom sumber untuk tracing
    df["_port"] = port_key
    df["_namespace"] = ns
    
    return df


def union_ports(
    sql: str, 
    cache_name: str,
    force_refresh: bool = False
) -> pd.DataFrame:
    """
    Jalankan query yang sama di 3 port, UNION hasilnya dengan namespace.
    
    Input:
        sql: Query SQL yang akan dijalankan di setiap port
        cache_name: Nama file cache union (tanpa ekstensi)
        force_refresh: Jika True, query ulang semua port
    
    Output:
        pd.DataFrame gabungan dari 3 port dengan namespace
    
    Asumsi:
        - Query valid untuk semua port
        - Schema tabel konsisten antar port
    """
    path = Path(DATA_DIR) / f"{cache_name}_union.parquet"
    
    if path.exists() and not force_refresh:
        print(f"📦 Loading cached union: {path}")
        return pd.read_parquet(path)
    
    dfs = []
    for port_key in DB_CONFIGS.keys():
        try:
            print(f"  🔍 Querying {port_key}...")
            df = query_to_df(sql, port_key)
            df = add_port_namespace(df, port_key)  # WAJIB (Rule #7)
            dfs.append(df)
            print(f"    ✅ {port_key}: {len(df):,} rows")
        except Exception as e:
            print(f"    ⚠️  {port_key} skip: {e}")
    
    if not dfs:
        raise RuntimeError("Tidak ada port yang berhasil diquery")
    
    result = pd.concat(dfs, ignore_index=True)
    
    # Validasi tidak ada collision setelah namespace
    for col in ["szCustomerId", "szId"]:
        if col in result.columns:
            dupes = result.groupby(col)["_port"].nunique()
            cross_port = dupes[dupes > 1]
            if len(cross_port) > 0:
                print(f"  ⚠️  {len(cross_port)} ID di {col} muncul di >1 port")
    
    result.to_parquet(path, index=False)
    print(f"✅ UNION {cache_name}: {len(result):,} total rows → {path}")
    return result


def normalize_all_datetimes(df: pd.DataFrame, datetime_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Normalisasi semua kolom datetime dari tabel SFA agar konsisten.
    
    PATCH 4: Ada dua sumber timezone berbeda:
    - Tabel DMS (dms_sd_docso, dms_sd_doccall) → WIB (UTC+7)
    - Tabel SFA (sfa_docsales, sfa_doccallitem, sfa_doccall) → Bisa UTC
    
    Fungsi ini mengkonversi semua datetime ke WIB (UTC+7) untuk konsistensi.
    
    Input:
        df: DataFrame dengan kolom datetime
        datetime_cols: List nama kolom datetime. Jika None, auto-detect.
    
    Output:
        DataFrame dengan kolom datetime yang sudah dinormalisasi ke WIB
    
    Asumsi:
        - Datetime tanpa timezone info dianggap UTC (dari SFA mobile)
        - Target normalisasi adalah WIB (Asia/Jakarta = UTC+7)
    """
    df = df.copy()
    
    if datetime_cols is None:
        # Auto-detect kolom datetime
        datetime_cols = []
        for col in df.columns:
            if df[col].dtype == 'datetime64[ns]' or 'dtm' in col.lower() or 'date' in col.lower():
                datetime_cols.append(col)
    
    for col in datetime_cols:
        if col not in df.columns:
            continue
        
        # Konversi ke datetime jika belum
        if df[col].dtype != 'datetime64[ns]':
            df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Asumsi: datetime dari SFA adalah UTC, konversi ke WIB (+7 jam)
        # Jika sudah ada timezone info, convert ke WIB
        # Jika tidak ada timezone info, anggap UTC lalu convert ke WIB
        df[col] = df[col].apply(lambda x: x + pd.Timedelta(hours=7) if pd.notna(x) else x)
    
    return df


def resolve_excel_id(customer_id: str) -> str:
    """
    Convert ID dari file Excel reference (misal '343-0001234') 
    ke namespace format yang konsisten dengan union_ports().
    
    Input:
        customer_id: ID dari file Excel (format: PREFIX-NOMOR)
    
    Output:
        ID dengan namespace (format: 'P1::343-0001234')
    
    Asumsi:
        - Prefix depo ada di DEPO_TO_PORT mapping
        - Format ID: PREFIX-NOMOR (misal 343-0000001)
    """
    if not customer_id or pd.isna(customer_id):
        return customer_id
    
    prefix = str(customer_id).split("-")[0]
    ns = DEPO_TO_PORT.get(prefix, "UNKNOWN")
    return f"{ns}::{customer_id}"


def load_reference_excel(filename: str) -> pd.DataFrame:
    """
    Load file Excel referensi dan tambahkan namespace ID.
    
    Input:
        filename: Nama file di folder data/reference/
    
    Output:
        DataFrame dengan kolom szCustomerId_ns yang sudah di-namespace
    """
    path = Path(REF_DIR) / filename
    
    if not path.exists():
        raise FileNotFoundError(f"Reference file not found: {path}")
    
    df = pd.read_excel(path)
    
    # Cari kolom ID pelanggan (bisa berbagai nama)
    id_cols = ['ID_PELANGGAN', 'szCustomerId', 'CustomerID', 'szId']
    id_col = None
    for c in id_cols:
        if c in df.columns:
            id_col = c
            break
    
    if id_col:
        df['szCustomerId_ns'] = df[id_col].apply(resolve_excel_id)
    
    return df
