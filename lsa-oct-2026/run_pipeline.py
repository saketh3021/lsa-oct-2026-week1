"""Run the pipeline stages in order.

Week 1: extract + profile are ready. Transform, load and checks arrive in
weeks 2 and 3 and are skipped until then.

    python run_pipeline.py --source data/source
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import extract            # noqa: E402
import profile_data       # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=Path("data/source"))
    a = ap.parse_args()

    print("== 1/2 extract ==")
    extract.extract(a.source, Path("data/raw"))
    print("\n== 2/2 profile ==")
    profile_data.main()
    print("\n(transform, load and checks: not built yet)")


if __name__ == "__main__":
    main()
