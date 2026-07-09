from pathlib import Path

_real_dashboard_sync = Path(__file__).resolve().parents[2] / "dashboard_sync"
if _real_dashboard_sync.is_dir():
    __path__.append(str(_real_dashboard_sync))
