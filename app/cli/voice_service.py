from __future__ import annotations

import argparse
import time
from pathlib import Path

from app.config import Config
from app.core.supervisor import Supervisor


def main() -> int:
    parser = argparse.ArgumentParser(description="Run live voice service in terminal")
    parser.add_argument("--target-lang", default="vi")
    parser.add_argument("--source-id", default="")
    parser.add_argument(
        "--config",
        default=str(Path.home() / ".config" / "deep-caption" / "config.yaml"),
    )
    args = parser.parse_args()

    config = Config.load(Path(args.config))
    supervisor = Supervisor(config=config, source_id=args.source_id, target_lang=args.target_lang)
    supervisor.start()
    print("Voice service started. Press Ctrl+C to stop.")
    try:
        while True:
            for segment in supervisor.poll():
                print(f"{segment.source_lang}->{segment.target_lang} | {segment.source_text} => {segment.translated_text}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        supervisor.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
