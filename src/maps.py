"""
maps.py - Builder peta interaktif untuk LURGIP MVP menggunakan Folium

Fungsi:
- create_outlet_map(): Peta sebaran outlet dengan warna status
- create_heatmap(): Heatmap densitas kunjungan salesman
- create_territory_map(): Peta batas wilayah (kecamatan/kabupaten)
- create_prospect_map(): Peta prospek dengan ukuran bubble = potensi

Dibuat sesuai aturan:
- Rule #3, #4: Koordinat szLangitude (TYPO) dan szLatitude
- Blueprint Section 7: Visualisasi peta
"""

import folium
from typing import Optional, List, Dict, Any
import pandas as pd


def create_outlet_map(
    df_outlets: pd.DataFrame,
    lat_col: str = "szLatitude",
    lon_col: str = "szLongitude",
    color_by: Optional[str] = None,
    popup_cols: Optional[List[str]] = None,
    zoom_start: int = 10,
    center: Optional[tuple] = None
) -> folium.Map:
    """
    Buat peta sebaran outlet dengan marker berwarna.
    
    Input:
        df_outlets: DataFrame dengan data outlet
        lat_col: Nama kolom latitude
        lon_col: Nama kolom longitude
        color_by: Kolom untuk menentukan warna marker (opsional)
        popup_cols: Kolom-kolom untuk ditampilkan di popup
        zoom_start: Level zoom awal peta
        center: Koordinat pusat peta (lat, lon). Jika None, auto-center.
    
    Output:
        folium.Map object dengan marker outlet
    
    Asumsi:
        - Koordinat sudah valid (tidak null, dalam bounding box)
        - color_by jika ada berisi nilai kategorikal atau numerik
    """
    pass


def create_heatmap(
    df_visits: pd.DataFrame,
    lat_col: str = "szLangitude",
    lon_col: str = "szLongitude",
    weight_col: Optional[str] = None,
    radius: int = 15,
    blur: int = 10,
    zoom_start: int = 10
) -> folium.Map:
    """
    Buat heatmap densitas kunjungan salesman.
    
    Input:
        df_visits: DataFrame dengan data kunjungan (sfa_doccallitem)
        lat_col: Nama kolom latitude (dengan TYPO szLangitude)
        lon_col: Nama kolom longitude
        weight_col: Kolom untuk bobot heatmap (misal decDuration, decAmount)
        radius: Radius heatmap dalam pixel
        blur: Blur effect untuk smoothing
        zoom_start: Level zoom awal peta
    
    Output:
        folium.Map object dengan heatmap layer
    
    Asumsi:
        - Koordinat sudah di-parse dan difilter (gunakan clean_coords())
        - weight_col jika ada berisi nilai numerik positif
    """
    pass


def create_territory_map(
    geojson_path: str,
    df_data: pd.DataFrame,
    key_on: str,
    value_col: str,
    zoom_start: int = 10
) -> folium.Map:
    """
    Buat peta choropleth dengan batas wilayah (kecamatan/kabupaten).
    
    Input:
        geojson_path: Path ke file GeoJSON batas wilayah
        df_data: DataFrame dengan data per wilayah
        key_on: Field di GeoJSON untuk join (misal 'properties.name')
        value_col: Kolom di df_data untuk warna choropleth
        zoom_start: Level zoom awal peta
    
    Output:
        folium.Map object dengan choropleth layer
    
    Asumsi:
        - File GeoJSON ada dan valid
        - Key di GeoJSON match dengan index df_data
    """
    pass


def create_prospect_map(
    df_prospects: pd.DataFrame,
    lat_col: str = "szLangitude",
    lon_col: str = "szLongitude",
    size_col: str = "potential_score",
    popup_cols: Optional[List[str]] = None,
    zoom_start: int = 10
) -> folium.Map:
    """
    Buat peta prospek dengan bubble size = potensi penjualan.
    
    Input:
        df_prospects: DataFrame dengan data prospek (sfa_prospect)
        lat_col: Nama kolom latitude (dengan TYPO szLangitude)
        lon_col: Nama kolom longitude
        size_col: Kolom untuk ukuran bubble (biasanya potential_score)
        popup_cols: Kolom-kolom untuk ditampilkan di popup
        zoom_start: Level zoom awal peta
    
    Output:
        folium.Map object dengan circle marker prospek
    
    Asumsi:
        - df_prospects sudah memiliki kolom potential_score dari calc_prospect_potential()
        - Koordinat sudah valid
    """
    pass


# ── Penggunaan di notebook ─────────────────────────────────────────────────
# from src.maps import create_outlet_map, create_heatmap, create_prospect_map
#
# # Peta outlet aktif
# m = create_outlet_map(df_outlets, color_by='szStatus', popup_cols=['szName', 'szHierarchyFull'])
# m.save('output/outlet_map.html')
#
# # Heatmap kunjungan
# m = create_heatmap(df_visits_clean, weight_col='decDuration')
# m.save('output/visit_heatmap.html')
#
# # Peta prospek
# m = create_prospect_map(df_prospects, size_col='potential_score')
# m.save('output/prospect_map.html')
