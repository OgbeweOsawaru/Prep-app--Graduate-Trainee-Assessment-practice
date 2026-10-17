from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR/ "data"/"questions.csv"
BLUEPRINT={"numerical":25,"verbal":25,"critical":10}
TIME_LIMIT_SECONDS=60 * 60
MAX_FREE_TESTS = 4
SECTIONS=list(BLUEPRINT.keys())
GRACE_SECONDS=15