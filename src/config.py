"""
config.py - Konfigurasi koneksi database & konstanta LURGIP MVP

Semua kredensial database disimpan di sini (tidak di-commit ke Git).
File ini masuk .gitignore.

Dibuat sesuai aturan:
- Rule #8: Jangan pernah commit atau hardcode kredensial database
- Blueprint Section 4: Struktur DB_CONFIGS
"""

# ── KONFIGURASI DATABASE (EDIT SESUAI ENVIRONMENT KAMU) ─────────────────────
# Port 3306, 3307, 3308 sesuai arsitektur multi-depo
DB_CONFIGS = {
    "port_3306": {
        "host": "103.85.65.185",
        "port": 3306,
        "user": "reporting",
        "password": "reporting@2025!!",
        "database": "dms",
        "charset": "utf8mb4"
    },
    "port_3307": {
        "host": "103.85.65.185",
        "port": 3307,
        "user": "reporting",
        "password": "reporting@2025!!",
        "database": "dms",
        "charset": "utf8mb4"
    },
    "port_3308": {
        "host": "103.85.65.185",
        "port": 3308,
        "user": "reporting",
        "password": "reporting@2025!!",
        "database": "dms",
        "charset": "utf8mb4"
    },
}

# ── PARAMETER ANALITIK ───────────────────────────────────────────────────────
GHOST_DAYS = 90              # hari tanpa transaksi = ghost outlet
CHURN_THRESHOLD = 0.70       # < 70% bulan lalu = churn risk
VISIT_DURATION_MAX = 300     # detik; lebih dari 5 menit = anomali GPS (Patch 1)
ANALYSIS_MONTHS = 2          # window analisis sales

# ── PATHS ────────────────────────────────────────────────────────────────────
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"
REF_DIR = BASE_DIR / "data" / "reference"
OUT_DIR = BASE_DIR / "data" / "output"

# Pastikan folder ada
for d in [DATA_DIR, REF_DIR, OUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── NAMESPACE MULTI-PORT (Patch 2) ──────────────────────────────────────────
# Mapping port → prefix namespace untuk menghindari collision ID
PORT_NAMESPACE = {
    "port_3306": "P1",   # depo Padalarang, Metro, Katapang, dll
    "port_3307": "P2",   # depo Bogor, Sukabumi, Cianjur, dll
    "port_3308": "P3",   # depo Cirebon, Purwakarta, Tasik, dll
}

# Kolom-kolom yang berisi ID antar-entitas (semua harus di-namespace)
ID_COLUMNS = [
    "szCustomerId", "szId", "szEmployeeId", "szRouteId",
    "szDocId", "szBranchId", "szDocCallId", "szRefDocId",
]

# ── MAPPING DEPO KE PORT (untuk resolve Excel reference data) ───────────────
DEPO_TO_PORT = {
    # P1 (3306)
    "343": "P1", "904": "P1", "902": "P1", "912": "P1",
    "900": "P1", "344": "P1", "914": "P1", "029": "P1",
    "030": "P1", "930": "P1",
    # P2 (3307)
    "337": "P2", "906": "P2", "901": "P2", "342": "P2",
    "911": "P2", "915": "P2", "918": "P2", "020": "P2",
    "021": "P2", "925": "P2", "926": "P2",
    # P3 (3308)
    "033": "P3", "032": "P3", "335": "P3", "908": "P3",
    "341": "P3", "910": "P3", "917": "P3", "916": "P3",
    "031": "P3", "919": "P3", "036": "P3",
}
