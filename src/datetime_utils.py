"""
datetime_utils.py - Utilitas normalisasi datetime untuk LURGIP MVP

PATCH 4: Normalisasi Timezone Database

Masalah:
- Tabel DMS (dms_sd_docso, dms_sd_doccall) → WIB (UTC+7)
- Tabel SFA (sfa_docsales, sfa_doccallitem, sfa_doccall) → Bisa UTC
- MySQL TIMESTAMP otomatis convert ke timezone session

Fungsi:
- normalize_to_wib(): Konversi datetime ke WIB
- detect_datetime_cols(): Auto-detect kolom datetime di DataFrame
- normalize_all_datetimes(): Wrapper lengkap untuk semua kolom datetime

Dibuat sesuai aturan:
- Rule #6: Semua datetime dari tabel SFA harus melalui normalize_all_datetimes()
- Patch 4: Isu timezone datetime
"""

import pandas as pd
from typing import List, Optional
from datetime import datetime, timezone, timedelta


def normalize_to_wib(
    dt: pd.Timestamp,
    assume_utc: bool = True
) -> pd.Timestamp:
    """
    Normalisasi satu timestamp ke WIB (UTC+7).
    
    Input:
        dt: pandas Timestamp atau datetime object
        assume_utc: Jika True dan dt tidak punya tz info, anggap UTC
    
    Output:
        pd.Timestamp dalam timezone WIB (Asia/Jakarta)
    
    Asumsi:
        - Input bisa naive (no tz) atau aware (with tz)
        - Naive datetime dari SFA dianggap UTC
    """
    if pd.isna(dt):
        return dt
    
    # Konversi ke pd.Timestamp jika belum
    if not isinstance(dt, pd.Timestamp):
        dt = pd.Timestamp(dt)
    
    # Jika tidak ada timezone info dan assume_utc=True, tambahkan UTC
    if dt.tz is None and assume_utc:
        dt = dt.tz_localize('UTC')
    
    # Convert ke WIB
    wib_tz = timezone(timedelta(hours=7))
    dt_wib = dt.astimezone(wib_tz)
    
    # Return tanpa timezone info (naive) tapi sudah dalam nilai WIB
    return dt_wib.replace(tzinfo=None)


def detect_datetime_cols(df: pd.DataFrame) -> List[str]:
    """
    Auto-detect kolom yang berisi datetime di DataFrame.
    
    Deteksi berdasarkan:
    1. dtype == 'datetime64[ns]'
    2. Nama kolom mengandung 'dtm', 'date', 'time' (case-insensitive)
    
    Input:
        df: DataFrame untuk di-scan
    
    Output:
        List nama kolom yang terdeteksi sebagai datetime
    
    Asumsi:
        - Konvensi penamaan kolom DMS/SFA menggunakan prefix 'dtm'
        - Kolom datetime sudah bertipe datetime64 atau bisa di-convert
    """
    datetime_cols = []
    
    for col in df.columns:
        # Cek dtype
        if df[col].dtype == 'datetime64[ns]':
            datetime_cols.append(col)
            continue
        
        # Cek nama kolom (konvensi DMS/SFA)
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['dtm', 'date', 'time']):
            # Coba convert untuk verifikasi
            try:
                pd.to_datetime(df[col].iloc[0])
                datetime_cols.append(col)
            except:
                pass
    
    return datetime_cols


def normalize_all_datetimes(
    df: pd.DataFrame,
    datetime_cols: Optional[List[str]] = None,
    assume_utc: bool = True
) -> pd.DataFrame:
    """
    Normalisasi semua kolom datetime dari tabel SFA agar konsisten ke WIB.
    
    PATCH 4: Ada dua sumber timezone berbeda:
    - Tabel DMS (dms_sd_docso, dms_sd_doccall) → WIB (UTC+7)
    - Tabel SFA (sfa_docsales, sfa_doccallitem, sfa_doccall) → Bisa UTC
    
    Fungsi ini mengkonversi semua datetime ke WIB (UTC+7) untuk konsistensi.
    
    Input:
        df: DataFrame dengan kolom datetime
        datetime_cols: List nama kolom datetime. Jika None, auto-detect.
        assume_utc: Jika True, datetime tanpa tz dianggap UTC (dari SFA mobile)
    
    Output:
        DataFrame dengan kolom datetime yang sudah dinormalisasi ke WIB
    
    Asumsi:
        - Datetime tanpa timezone info dianggap UTC (dari SFA mobile)
        - Target normalisasi adalah WIB (Asia/Jakarta = UTC+7)
        - Tidak menghapus timezone info, hanya convert nilai
    
    Contoh penggunaan:
        df = query_to_df("SELECT * FROM sfa_doccallitem", "port_3306")
        df = normalize_all_datetimes(df)
    """
    df = df.copy()
    
    if datetime_cols is None:
        datetime_cols = detect_datetime_cols(df)
    
    for col in datetime_cols:
        if col not in df.columns:
            continue
        
        # Konversi ke datetime jika belum
        if df[col].dtype != 'datetime64[ns]':
            df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Apply normalisasi per row
        df[col] = df[col].apply(lambda x: normalize_to_wib(x, assume_utc))
    
    return df


# ── Penggunaan di notebook ─────────────────────────────────────────────────
# from src.datetime_utils import normalize_all_datetimes
#
# df_visits = query_to_df("SELECT * FROM sfa_doccallitem", "port_3306")
# df_visits = normalize_all_datetimes(df_visits)
# # Sekarang semua datetime dalam WIB, siap untuk perbandingan
