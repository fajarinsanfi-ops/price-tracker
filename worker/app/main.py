import json
import sys

from .config import Settings
from .price_checker import run_checks


def main() -> int:
    try:
        settings = Settings.from_env()
        result = run_checks(settings)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["errors"] == 0 else 1
    except Exception as exc:
        print(f"Price tracker worker failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
