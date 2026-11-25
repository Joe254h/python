"""Switch ICPAC Minutes to write reports with a model on this computer (Ollama).

Run it once from the meeting-recorder folder, next to local_writer.py:

    python enable_local_reports.py

It makes four small edits (services.py, app.py, static/js/app.js, .env), keeps a copy of
each file as <name>.before-local, and changes nothing if any file is not as expected.
Running it again is safe. To go back to OpenRouter, set REPORT_WRITER=openrouter in .env.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODEL = "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M"

MAKE_WRITER = '''def make_writer():
    """REPORT_WRITER=local writes reports with a model on this computer (Ollama): no key, no credit."""
    if os.environ.get("REPORT_WRITER", "").strip().lower() == "local":
        from local_writer import LocalWriter
        return LocalWriter()
    return OpenRouterWriter()


def _error_text(resp) -> str:'''

PROGRESS = '''        self.store.update(sid, status="writing", stage="Writing the report", progress=0.9)
        if hasattr(self.writer, "on_progress"):  # the local writer says which part it is reading
            self.writer.on_progress = lambda stage: self.store.update(sid, stage=stage)
'''

# (file, text that must be there, replacement, text that shows the edit is already done)
EDITS = [
    ("services.py", "        self.writer = writer or OpenRouterWriter()",
     "        self.writer = writer or make_writer()", "writer or make_writer()"),
    ("services.py", "def _error_text(resp) -> str:", MAKE_WRITER, "def make_writer():"),
    ("services.py",
     '        self.store.update(sid, status="writing", stage="Writing the report", progress=0.9)\n',
     PROGRESS, "self.writer.on_progress = lambda"),
    ("app.py", '"writer": {"ready": w.ready, "model": w.model},',
     '"writer": {"ready": w.ready, "model": w.model, "name": getattr(w, "name", "OpenRouter"),\n'
     '                       "hint": getattr(w, "setup_hint", "add OPENROUTER_API_KEY")},',
     '"hint": getattr(w, "setup_hint"'),
    ("static/js/app.js",
     '{ ok: c.writer.ready, on: "Reports · OpenRouter", off: "Reports: add OPENROUTER_API_KEY" },',
     '{ ok: c.writer.ready, on: `Reports · ${c.writer.name || "OpenRouter"}`,\n'
     '      off: `Reports: ${c.writer.hint || "add OPENROUTER_API_KEY"}` },',
     "c.writer.hint"),
]

ENV_LINES = ("\n# Reports with a model on this computer (Ollama): no key, no credit.\n"
             "# Set REPORT_WRITER=openrouter to go back to OpenRouter.\n"
             f"REPORT_WRITER=local\nLOCAL_REPORT_MODEL={MODEL}\n")


def read(path: Path) -> tuple[str, str]:
    raw = path.read_bytes().decode("utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    return raw.replace("\r\n", "\n"), newline


def main(root: Path = HERE) -> int:
    if not (root / "local_writer.py").is_file():
        print(f"local_writer.py is missing. Download it into {root} first.")
        return 1
    texts, newlines, problems = {}, {}, []
    for name, old, new, done in EDITS:
        path = root / name
        if name not in texts:
            if not path.is_file():
                problems.append(f"{name} is missing")
                continue
            texts[name], newlines[name] = read(path)
        text = texts[name]
        if done in text:
            continue
        if text.count(old) != 1:
            problems.append(f"{name}: could not find the line to change:\n    {old.strip()}")
            continue
        texts[name] = text.replace(old, new)
    if problems:
        print("Nothing was changed, because:\n- " + "\n- ".join(problems))
        print("Send this message to Claude.")
        return 1

    changed = []
    for name, text in texts.items():
        path = root / name
        original, _ = read(path)
        if text == original:
            continue
        backup = path.with_name(path.name + ".before-local")
        if not backup.exists():
            shutil.copy2(path, backup)
        path.write_bytes(text.replace("\n", newlines[name]).encode("utf-8"))
        changed.append(name)

    env = root / ".env"
    env_text, env_nl = read(env) if env.is_file() else ("", "\n")
    if re.search(r"(?m)^REPORT_WRITER=local\s*$", env_text):
        pass
    elif re.search(r"(?m)^REPORT_WRITER=.*$", env_text):
        env_text = re.sub(r"(?m)^REPORT_WRITER=.*$", "REPORT_WRITER=local", env_text)
        changed.append(".env")
    else:
        env_text = env_text.rstrip("\n") + "\n" + ENV_LINES
        changed.append(".env")
    if ".env" in changed:
        if env.is_file() and not env.with_name(".env.before-local").exists():
            shutil.copy2(env, env.with_name(".env.before-local"))
        env.write_bytes(env_text.replace("\n", env_nl).encode("utf-8"))

    if changed:
        print("Local reports switched on. Changed: " + ", ".join(changed))
    else:
        print("Local reports were already switched on. Nothing to change.")
    print("Now restart the app (Ctrl+C, then start it again) and press Ctrl+F5 in the browser.")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE))
