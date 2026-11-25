"""Switch ICPAC Minutes to write reports with a model on this computer (Ollama).

Run it once from the meeting-recorder folder, next to local_writer.py:

    python enable_local_reports.py

It adds a short block to the end of services.py and sets REPORT_WRITER=local in .env,
keeping a copy of each file as <name>.before-local. It does not depend on the rest of
services.py, so it works on versions of the app that have changed since. Running it again
is safe. To go back to OpenRouter, set REPORT_WRITER=openrouter in .env.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODEL = "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M"
MARK = "# --- Local reports"
BLOCK = f"""

{MARK} (added by enable_local_reports.py; delete these lines to undo) ---
import os as _os_for_local_reports
if _os_for_local_reports.environ.get("REPORT_WRITER", "").strip().lower() == "local":
    import local_writer as _local_writer
    _local_writer.install(globals())
"""
ENV_LINES = ("\n# Reports with a model on this computer (Ollama): no key, no credit.\n"
             "# Set REPORT_WRITER=openrouter to go back to OpenRouter.\n"
             f"REPORT_WRITER=local\nLOCAL_REPORT_MODEL={MODEL}\n")


def read(path: Path) -> tuple[str, str]:
    raw = path.read_bytes().decode("utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    return raw.replace("\r\n", "\n"), newline


def save(path: Path, text: str, newline: str) -> None:
    backup = path.with_name(path.name + ".before-local")
    if path.is_file() and not backup.exists():
        shutil.copy2(path, backup)
    path.write_bytes(text.replace("\n", newline).encode("utf-8"))


def main(root: Path = HERE) -> int:
    services = root / "services.py"
    if not (root / "local_writer.py").is_file():
        print(f"local_writer.py is missing. Download it into {root} first.")
        return 1
    if not services.is_file():
        print(f"services.py is not in {root}. Run this from the meeting-recorder folder.")
        return 1
    text, newline = read(services)
    if MARK not in text and "OpenRouterWriter" not in text:
        writers = [ln.strip() for ln in text.splitlines() if re.search(r"Writer|writer\s*=", ln)]
        print("Nothing was changed: services.py has no OpenRouterWriter. Send Claude these lines:\n  "
              + "\n  ".join(writers[:15] or ["(no lines mention a writer)"]))
        return 1

    changed = []
    if MARK not in text:
        save(services, text.rstrip("\n") + BLOCK, newline)
        changed.append("services.py")

    env = root / ".env"
    env_text, env_nl = read(env) if env.is_file() else ("", "\n")
    if not re.search(r"(?m)^REPORT_WRITER=local\s*$", env_text):
        if re.search(r"(?m)^REPORT_WRITER=.*$", env_text):
            env_text = re.sub(r"(?m)^REPORT_WRITER=.*$", "REPORT_WRITER=local", env_text)
        else:
            env_text = env_text.rstrip("\n") + "\n" + ENV_LINES
        save(env, env_text, env_nl)
        changed.append(".env")

    if changed:
        print("Local reports switched on. Changed: " + ", ".join(changed))
    else:
        print("Local reports were already switched on. Nothing to change.")
    print("Now restart the app (Ctrl+C, then start it again) and press Ctrl+F5 in the browser.")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE))
