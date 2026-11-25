"""The local (Ollama) report writer and the script that switches it on."""

import time
from pathlib import Path

import pytest
import requests

import enable_local_reports
import local_writer
import services
from app import create_app
from local_writer import LocalWriter, split_parts

from test_app import FakeTranscriber, make_audio, wait_done


class FakeOllama:
    """Stands in for requests.post/get against Ollama and records every chat."""

    def __init__(self, note_words=60, status=200, body=""):
        self.chats = []
        self.note_words = note_words
        self.status = status
        self.body = body

    def post(self, url, json=None, timeout=None):
        assert url.endswith("/api/chat")
        self.chats.append(json)
        system = json["messages"][0]["content"]
        if system.startswith("You take notes"):
            text = "DECIDED:\n- " + " ".join(["budget"] * self.note_words) + " [12:30]"
        elif system.startswith("You merge"):
            text = "DECIDED:\n- merged [12:30]"
        elif "slide deck" in system:
            text = '```json\n{"title": "T", "slides": []}\n```'
        else:
            text = "<think>plan</think>\n```markdown\n# Report\n\n## Decisions\n- Budget agreed [12:30]\n```"
        return Resp(self.status, {"message": {"content": text}, "done_reason": "stop"}, self.body)

    def get(self, url, timeout=None):
        return Resp(200, {"version": "0.40.16"})

    def kinds(self):
        out = []
        for c in self.chats:
            s = c["messages"][0]["content"]
            out.append("part" if s.startswith("You take notes") else "merge" if s.startswith("You merge")
                       else "report")
        return out


class Resp:
    def __init__(self, status, data, text=""):
        self.status_code, self._data, self.text = status, data, text
        self.ok = status < 400

    def json(self):
        return self._data


@pytest.fixture()
def ollama(monkeypatch):
    fake = FakeOllama()
    monkeypatch.setattr(local_writer.requests, "post", fake.post)
    monkeypatch.setattr(local_writer.requests, "get", fake.get)
    return fake


def meeting(words):
    lines = [f"[{i // 4:02d}:{i % 4 * 15:02d}] Speaker agrees the budget for item {i} should go ahead now please"
             for i in range(words // 14)]
    return "\n".join(lines)


def messages(transcript, language="English", vocab=""):
    meta = {"title": "Day 5 RCC", "created_at": time.time(), "language": "en",
            "report_language": "sw" if language == "Kiswahili" else "same"}
    return services.build_messages(meta, services.DEFAULT_TEMPLATE, transcript, {"vocabulary": vocab})


def test_short_meeting_is_written_in_one_request(ollama):
    w = LocalWriter()
    text, used = w.write(messages(meeting(600)))
    assert ollama.kinds() == ["report"]
    chat = ollama.chats[0]
    assert chat["options"]["num_ctx"] == w.num_ctx and chat["stream"] is False
    assert "Speaker agrees the budget for item 3" in chat["messages"][1]["content"]
    assert used == local_writer.DEFAULT_LOCAL_MODEL
    assert text == "# Report\n\n## Decisions\n- Budget agreed [12:30]"


def test_long_meeting_is_read_in_parts_then_written_from_notes(ollama):
    w, stages = LocalWriter(), []
    w.on_progress = stages.append
    transcript = meeting(10000)  # about an 87-minute meeting
    w.write(messages(transcript))
    parts = split_parts(transcript, w.part_words)
    assert len(parts) >= 5
    assert ollama.kinds() == ["part"] * len(parts) + ["report"]
    final = ollama.chats[-1]["messages"][1]["content"]
    assert "TRANSCRIPT NOTES" in final and "Part 1 of" in final
    assert "Speaker agrees" not in final
    assert "REPORT TEMPLATE" in final  # the user's template still reaches the model
    assert local_writer._tokens(ollama.chats[-1]["messages"][0]["content"] + final) + w.max_tokens <= w.num_ctx
    assert stages[0] == f"Writing the report: reading part 1 of {len(parts)}"
    assert stages[-1] == "Writing the report from the notes"
    for chat in ollama.chats:  # one window size, so Ollama never reloads the model
        assert chat["options"]["num_ctx"] == w.num_ctx


def test_parts_keep_whole_lines_and_every_word():
    transcript = meeting(10000)
    parts = split_parts(transcript, 1800)
    assert all(len(p.split()) <= 1800 for p in parts)
    assert "\n".join(parts).split() == transcript.split()
    assert all(line.startswith("[") for p in parts for line in p.splitlines())


def test_notes_are_in_the_report_language_with_vocabulary(ollama):
    LocalWriter().write(messages(meeting(10000), language="Kiswahili", vocab="ICPAC, IGAD"))
    part = ollama.chats[0]["messages"]
    assert part[0]["content"].endswith("Write in Kiswahili.")
    assert "Correct spellings of names and terms: ICPAC, IGAD" in part[1]["content"]


def test_retry_reuses_parts_already_read(ollama):
    w = LocalWriter()
    w.write(messages(meeting(10000)))
    ollama.chats.clear()
    w.write(messages(meeting(10000)))
    assert ollama.kinds() == ["report"]


def test_long_notes_are_merged_until_they_fit(ollama):
    ollama.note_words = 700
    w = LocalWriter()
    w.write(messages(meeting(10000)))
    assert "merge" in ollama.kinds() and ollama.kinds()[-1] == "report"
    final = ollama.chats[-1]["messages"]
    assert local_writer._tokens(final[0]["content"] + final[1]["content"]) + w.max_tokens <= w.num_ctx


@pytest.mark.parametrize("chosen,used", [
    (None, local_writer.DEFAULT_LOCAL_MODEL),
    ("google/gemini-2.5-pro", local_writer.DEFAULT_LOCAL_MODEL),  # an OpenRouter name left in settings
    ("qwen3:4b", "qwen3:4b"),
    ("hf.co/google/gemma-4-E4B-it-qat-q4_0-gguf", "hf.co/google/gemma-4-E4B-it-qat-q4_0-gguf"),
])
def test_model_choice(ollama, chosen, used):
    assert LocalWriter().write(messages(meeting(300)), chosen)[1] == used
    assert ollama.chats[0]["model"] == used


def test_clear_errors(monkeypatch):
    def refuse(*a, **k):
        raise requests.ConnectionError("refused")
    monkeypatch.setattr(local_writer.requests, "post", refuse)
    monkeypatch.setattr(local_writer.requests, "get", refuse)
    w = LocalWriter()
    assert w.ready is False
    with pytest.raises(RuntimeError, match="Open the Ollama app"):
        w.write(messages(meeting(300)))

    missing = FakeOllama(status=404, body='{"error":"model \\"x\\" not found, try pulling it first"}')
    monkeypatch.setattr(local_writer.requests, "post", missing.post)
    with pytest.raises(RuntimeError, match="ollama pull hf.co/unsloth/Qwen3-4B"):
        w.write(messages(meeting(300)))


def test_report_writer_setting(monkeypatch):
    monkeypatch.setenv("REPORT_WRITER", "local")
    assert isinstance(services.make_writer(), LocalWriter)
    monkeypatch.setenv("REPORT_WRITER", "")
    assert isinstance(services.make_writer(), services.OpenRouterWriter)


def test_app_end_to_end_with_local_reports(tmp_path, ollama):
    app = create_app(tmp_path / "data", transcriber=FakeTranscriber(), writer=LocalWriter())
    client = app.test_client()
    config = client.get("/api/config").get_json()["writer"]
    assert config == {"ready": True, "model": local_writer.DEFAULT_LOCAL_MODEL,
                      "name": "on this computer", "hint": "open the Ollama app"}
    mp3 = tmp_path / "weekly.mp3"
    make_audio(mp3, 10, ("-c:a", "libmp3lame", "-b:a", "64k"))
    with mp3.open("rb") as fh:
        r = client.post("/api/sessions/upload", data={"audio": (fh, "weekly.mp3"), "language": "en",
                                                       "report_language": "same",
                                                       "model": "google/gemini-2.5-pro"},
                        content_type="multipart/form-data")
    assert r.status_code == 201, r.get_json()
    sid = r.get_json()["id"]
    s = wait_done(client, sid)
    assert s["status"] == "done", s["error"]
    assert s["model"] == local_writer.DEFAULT_LOCAL_MODEL
    assert "Budget agreed" in client.get(f"/api/sessions/{sid}/report.md").get_data(as_text=True)


# ------------------------------------------------------------- enable_local_reports.py

ORIGINAL = {
    "services.py": ("class Processor:\n    def __init__(self):\n"
                    "        self.writer = writer or OpenRouterWriter()\n\n"
                    "def _error_text(resp) -> str:\n    pass\n\n"
                    "    def _report(self, sid):\n"
                    '        self.store.update(sid, status="writing", stage="Writing the report", progress=0.9)\n'
                    "        settings = 1\n"),
    "app.py": '            "writer": {"ready": w.ready, "model": w.model},\n',
    "static/js/app.js": ('    { ok: c.writer.ready, on: "Reports · OpenRouter", '
                         'off: "Reports: add OPENROUTER_API_KEY" },\n'),
    "local_writer.py": "",
    ".env": "OPENROUTER_API_KEY=sk-or-x\n",
}


def install(tmp_path, newline="\n", **override):
    files = {**ORIGINAL, **override}
    for name, text in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.replace("\n", newline).encode("utf-8"))
    return tmp_path


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_switch_on_script_edits_once_and_keeps_line_endings(tmp_path, newline, capsys):
    root = install(tmp_path, newline)
    assert enable_local_reports.main(root) == 0
    services_py = (root / "services.py").read_bytes().decode()
    assert "writer or make_writer()" in services_py and "def make_writer():" in services_py
    assert "self.writer.on_progress = lambda" in services_py
    assert services_py.count("\r\n") == (services_py.count("\n") if newline == "\r\n" else 0)
    assert "c.writer.hint" in (root / "static/js/app.js").read_text(encoding="utf-8")
    env = (root / ".env").read_text()
    assert "OPENROUTER_API_KEY=sk-or-x" in env and "REPORT_WRITER=local" in env
    assert (root / "services.py.before-local").read_bytes().decode().count("OpenRouterWriter()") == 1
    snapshot = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert enable_local_reports.main(root) == 0
    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == snapshot
    assert "already switched on" in capsys.readouterr().out


def test_switch_on_script_changes_nothing_when_a_file_is_unexpected(tmp_path, capsys):
    root = install(tmp_path, **{"app.py": "something else\n"})
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert enable_local_reports.main(root) == 1
    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == before
    assert "app.py: could not find the line to change" in capsys.readouterr().out


def test_switch_on_script_turns_an_existing_setting_to_local(tmp_path):
    root = install(tmp_path, **{".env": "REPORT_WRITER=openrouter\nX=1\n"})
    enable_local_reports.main(root)
    assert (root / ".env").read_text() == "REPORT_WRITER=local\nX=1\n"
