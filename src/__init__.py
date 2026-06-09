"""
__init__.py - Package initializer untuk src/

Import semua modul agar mudah diakses dari notebook.
"""

from .config import (
    DB_CONFIGS, DATA_DIR, REF_DIR, OUT_DIR,
    GHOST_DAYS, CHURN_THRESHOLD, VISIT_DURATION_MAX,
    PORT_NAMESPACE, ID_COLUMNS, DEPO_TO_PORT
)

from .db import (
    get_connection, query_to_df, query_and_cache,
    union_ports, add_port_namespace, normalize_all_datetimes,
    resolve_excel_id, load_reference_excel
)

from .geo_validator import (
    parse_coords, flag_ghost_coords, clean_coords,
    LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, DEPO_COORDS
)

from .analysis import (
    detect_ghost_outlets, calc_route_compliance, visit_duration_summary,
    sales_performance, calc_prospect_potential, WEIGHT_TABLE
)

__all__ = [
    # Config
    'DB_CONFIGS', 'DATA_DIR', 'REF_DIR', 'OUT_DIR',
    'GHOST_DAYS', 'CHURN_THRESHOLD', 'VISIT_DURATION_MAX',
    'PORT_NAMESPACE', 'ID_COLUMNS', 'DEPO_TO_PORT',
    
    # Database
    'get_connection', 'query_to_df', 'query_and_cache',
    'union_ports', 'add_port_namespace', 'normalize_all_datetimes',
    'resolve_excel_id', 'load_reference_excel',
    
    # Geo Validator
    'parse_coords', 'flag_ghost_coords', 'clean_coords',
    'LAT_MIN', 'LAT_MAX', 'LON_MIN', 'LON_MAX', 'DEPO_COORDS',
    
    # Analysis
    'detect_ghost_outlets', 'calc_route_compliance', 'visit_duration_summary',
    'sales_performance', 'calc_prospect_potential', 'WEIGHT_TABLE',
]
