import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("JOBRADAR_DATA", ROOT / "data"))
DB_PATH = DATA_DIR / "jobradar.db"
SEED_CSV = ROOT / "seeds" / "boards.csv"
SECTORS_CSV = ROOT / "seeds" / "company_sectors.csv"
PREFS_PROMPT = ROOT / "seeds" / "prefs_assistant_prompt.md"

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
    "seek": 180,
    "linkedin": 360,
    "remoteok": 120,
    "remotive": 180,
    "himalayas": 180,
    "wanted": 360,
    "104": 360,
    "arbeitnow": 360,
    "berlinstartupjobs": 360,
    "habr": 360,
    "hh": 360,
    "dou": 360,
    "djinni": 180,
    "justjoin": 360,
    "nofluff": 360,
    "green": 720,
    "rocketpunch": 720,
    "cutshort": 360,
    "itviec": 720,
    "remote3": 180,
    "foresight": 180,
    "learnblockchain": 360,
    "bitflyer": 720,
    "enrich": 30,
}
HOST_INTERVALS = {"www.linkedin.com": 6.0}
ENRICH_BATCH = 400
ENRICH_RETRY_DAYS = 7

SUPPORTED_ATS = {"greenhouse", "lever", "lever-eu", "ashby", "workable", "recruitee", "smartrecruiters", "bamboohr",
                 "breezy", "teamtailor", "personio", "rippling", "gem", "workday"}

COMPANY_ALIASES = {
    "payward": "kraken",
    "tools for humanity": "world",
    "worldcoin": "world",
    "foris dax": "crypto com",
    "foris dax mt": "crypto com",
    "binance com": "binance",
}
