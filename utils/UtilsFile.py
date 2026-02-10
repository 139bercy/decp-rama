from pathlib import Path
from datetime import datetime, timezone
#import sys

class UtilsFile:
    @staticmethod
    def last_modification(path: str) -> datetime: #dict:
        """
        Return last modification info for `path`.

        Returns a dict with:
        - "timestamp": float unix timestamp (seconds since epoch)
        - "modified_local": local time ISO string
        - "modified_utc": UTC time ISO string
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        # Use stat().st_mtime (follows symlinks). Use lstat() if you want symlink metadata.
        ts = p.stat().st_mtime
        dt_local = datetime.fromtimestamp(ts)  # local time
        dt_utc = datetime.fromtimestamp(ts, timezone.utc)
        #return {
        #    "timestamp": ts,
        #    "modified_local": dt_local.isoformat(sep=' '),
        #    "modified_utc": dt_utc.isoformat()
        #}
        return dt_local.isoformat(sep=' ')
