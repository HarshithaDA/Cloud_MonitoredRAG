"""Launch the local Arize Phoenix dashboard on http://localhost:6006."""

from __future__ import annotations

import os
import subprocess
import sys


def main() -> None:
    if not os.getenv("PHOENIX_HOST"):
        os.environ["PHOENIX_HOST"] = "127.0.0.1"
    if not os.getenv("PHOENIX_PORT"):
        os.environ["PHOENIX_PORT"] = "6006"
    print(
        f"Starting Phoenix at http://{os.environ['PHOENIX_HOST']}:"
        f"{os.environ['PHOENIX_PORT']}"
    )
    try:
        subprocess.run(
            [sys.executable, "-m", "phoenix.server.main", "serve"],
            check=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Phoenix is not installed. Run `python -m pip install arize-phoenix`."
        ) from exc
    except KeyboardInterrupt:
        print("Phoenix server stopped.")


if __name__ == "__main__":
    main()