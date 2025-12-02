import datetime

class UtilsDate:
    @staticmethod
    def parseDt(s:str):
        """Parse une chaîne de date en datetime. Gestion de 'Z' et de quelques formats."""
        if s is None:
            raise ValueError("created_at contient None")
        s = s.strip()
        # remplacer Z par +00:00 pour fromisoformat
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(s)
        except Exception:
            # essayer quelques formats courants
            fmts = ("%Y-%m-%dT%H:%M:%S.%f%z",
                    "%Y-%m-%dT%H:%M:%S%z",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d")
            for fmt in fmts:
                try:
                    return datetime.strptime(s, fmt)
                except Exception:
                    pass
            raise ValueError(f"Format de date non reconnu : {s}")
