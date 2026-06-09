#!/usr/bin/env python3
"""
run_all.py - Script untuk menjalankan semua notebook LURGIP MVP secara berurutan

Cara pakai:
    python run_all.py

Script ini akan:
1. Jalankan 00_setup_config.ipynb (verifikasi koneksi & schema)
2. Jalankan 01_extract_data.ipynb (extract data dari 3 port)
3. Jalankan 02_analysis.ipynb (5 metrik analitik)
4. Jalankan 03_map_visualization.ipynb (peta interaktif)
5. Jalankan 04_export_report.ipynb (export laporan)

Output akan tersimpan di data/output/
"""

import papermill as pm
from pathlib import Path
import sys


def run_notebook(notebook_name: str, output_suffix: str = "_executed"):
    """
    Jalankan satu notebook dengan papermill.
    
    Input:
        notebook_name: Nama file notebook (tanpa path)
        output_suffix: Suffix untuk file output
    
    Output:
        None (notebook dijalankan dan disimpan dengan suffix)
    """
    notebooks_dir = Path("notebooks")
    input_path = notebooks_dir / notebook_name
    output_name = notebook_name.replace(".ipynb", f"{output_suffix}.ipynb")
    output_path = notebooks_dir / output_name
    
    print(f"🚀 Running: {notebook_name}")
    try:
        pm.execute_notebook(
            input_path,
            output_path,
            progress_bar=True,
            report_errors=True
        )
        print(f"✅ Completed: {notebook_name} → {output_name}")
    except Exception as e:
        print(f"❌ Error running {notebook_name}: {e}")
        raise


def main():
    """Jalankan semua notebook secara berurutan."""
    notebooks = [
        "00_setup_config.ipynb",
        "01_extract_data.ipynb",
        "02_analysis.ipynb",
        "03_map_visualization.ipynb",
        "04_export_report.ipynb",
    ]
    
    print("=" * 60)
    print("LURGIP MVP - Full Pipeline Execution")
    print("=" * 60)
    
    for i, nb in enumerate(notebooks, 1):
        print(f"\n[{i}/{len(notebooks)}] {nb}")
        print("-" * 40)
        try:
            run_notebook(nb)
        except Exception as e:
            print(f"\n⚠️  Pipeline stopped at {nb}")
            print(f"Error: {e}")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 All notebooks completed successfully!")
    print("=" * 60)
    print("\nCheck output files in: data/output/")


if __name__ == "__main__":
    main()
