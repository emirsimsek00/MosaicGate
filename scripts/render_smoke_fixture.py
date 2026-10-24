"""Regenerate the transport fixture; it is not an evaluation/holdout case."""

from pathlib import Path

from mosaicgate.smoke_fixtures import REPORT_TEXT, report_png


def main() -> None:
    output = Path(__file__).resolve().parents[1] / "fixtures" / "smoke"
    output.mkdir(parents=True, exist_ok=True)
    (output / "q3.txt").write_text(REPORT_TEXT, encoding="utf-8")
    (output / "q3.png").write_bytes(report_png())


if __name__ == "__main__":
    main()
