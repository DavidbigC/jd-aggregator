import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("JOBRADAR_DATA", ROOT / "data"))
DB_PATH = DATA_DIR / "jobradar.db"
SEED_CSV = ROOT / "seeds" / "boards.csv"

STALE_DAYS = 10
MATCH_WINDOW_DAYS = 45
SIMILARITY_THRESHOLD = 0.85

INTERVALS = {
    "ats": 180,
    "jobstash": 360,
    "getro": 360,
    "consider": 360,
    "web3career": 60,
    "cryptojobslist": 60,
    "cryptocurrencyjobs": 60,
    "web3vacancy": 120,
    "cryptojobs": 180,
    "eleduck": 120,
    "rebase": 60,
    "telegram": 60,
    "mycareersfuture": 360,
}

COMPANY_ALIASES = {
    "payward": "kraken",
    "tools for humanity": "world",
    "worldcoin": "world",
    "foris dax": "crypto com",
    "foris dax mt": "crypto com",
    "binance com": "binance",
}
