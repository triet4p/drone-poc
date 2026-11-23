from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data"
UPLOADS = DATA / "uploads"       # normalized full JPEG (overlay coordinates)
PREVIEWS = DATA / "previews"     # max 2048 px for the browser
ORIGINALS = DATA / "originals"   # uploaded bytes, untouched
THUMBS = DATA / "thumbs"
DEMO = DATA / "demo"
DB = DATA / "demo.db"
DIST = BASE / "frontend" / "dist"

LABEL_JA = {"crack": "ひび割れ", "spalling": "うき・はく離", "rust": "腐食",
            "water leakage": "漏水", "exposed rebar": "鉄筋露出"}
CLASSES = list(LABEL_JA)
RANKS = ["AA", "A1", "A2", "B", "C", "S"]
MODEL_ID = "IDEA-Research/grounding-dino-tiny"
THRESHOLD = 0.18
MAX_BYTES = 40 * 1024 * 1024
LICENSES = {"client", "cc-by", "cc0", "pd", "demo", "unknown"}

STRUCTURES = [
    ("S1", "E1", "盛土", "earth", 12400, 13150),
    ("B14", "B-14", "B-14 橋梁", "bridge", 13150, 13520),
    ("S2", "E2", "切土", "earth", 13520, 14200),
    ("T07", "T-07", "T-07 トンネル", "tunnel", 14200, 14980),
    ("S3", "E3", "盛土", "earth", 14980, 15600),
]
MEMBERS = [
    ("B14-A1", "B14", "A1", "A1 橋台", 13168),
    ("B14-P1", "B14", "P1", "P1 橋脚", 13200),
    ("B14-P2", "B14", "P2", "P2 橋脚", 13230),
    ("B14-P3", "B14", "P3", "P3 橋脚", 13262),
    ("B14-P4", "B14", "P4", "P4 橋脚", 13330),
    ("B14-P5", "B14", "P5", "P5 橋脚", 13400),
    ("B14-P6", "B14", "P6", "P6 橋脚", 13460),
    ("B14-A2", "B14", "A2", "A2 橋台", 13505),
    ("B14-G1", "B14", "G1", "G1 主桁", 13190),
    ("B14-G2", "B14", "G2", "G2 主桁", 13260),
    ("B14-G3", "B14", "G3", "G3 主桁", 13330),
    ("B14-G4", "B14", "G4", "G4 主桁", 13410),
    ("B14-G5", "B14", "G5", "G5 主桁", 13480),
    ("T07-P1", "T07", "起点坑口", "起点方坑口 覆工", 14205),
    ("T07-P2", "T07", "終点坑口", "終点方坑口 覆工", 14975),
]
