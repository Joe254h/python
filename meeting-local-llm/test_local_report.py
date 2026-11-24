"""Tests for local_report.py against a fake local model server.

    python -m unittest test_local_report -v
"""
import contextlib
import io
import json
import socket
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import local_report as lr


class FakeServer:
    """Answers like Ollama (/api/chat) or an OpenAI-compatible server."""

    def __init__(self, status=200, error_body="", note_words=20,
                 prompt_tokens=500):
        self.requests = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(
                    int(self.headers["Content-Length"])))
                outer.requests.append((self.path, body))
                if status != 200:
                    self.send_response(status)
                    self.end_headers()
                    self.wfile.write(error_body.encode())
                    return
                user = body["messages"][1]["content"]
                if "Write the report in Markdown" in user:
                    text = "<think>plan</think>## Summary\nThe report body."
                elif user.startswith("Meeting:") and "Merge these notes" in user:
                    text = "TOPICS:\n- merged"
                else:
                    text = "TOPICS:\n- " + " ".join(["point"] * note_words)
                if self.path == "/api/chat":
                    reply = {"message": {"role": "assistant", "content": text},
                             "done": True, "done_reason": "stop",
                             "prompt_eval_count": prompt_tokens}
                else:
                    reply = {"choices": [{"message": {"content": text},
                                          "finish_reason": "stop"}]}
                data = json.dumps(reply).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def kinds(self):
        out = []
        for _, body in self.requests:
            user = body["messages"][1]["content"]
            out.append("report" if "Write the report in Markdown" in user
                       else "merge" if "Merge these notes" in user
                       else "section")
        return out


def transcript(words=5000):
    sentences = [f"Speaker {i % 3} said item {i} is agreed today."
                 for i in range(words // 8)]
    return " ".join(sentences)


class ChunkingTests(unittest.TestCase):
    def test_chunks_respect_limit_and_keep_every_word(self):
        text = transcript(5000)
        chunks = lr.split_chunks(text, 600)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(c.split()) <= 600 for c in chunks))
        self.assertEqual(" ".join(chunks).split(), text.split())

    def test_run_on_line_longer_than_a_chunk_is_split(self):
        text = " ".join(["neno"] * 2500)          # no punctuation at all
        chunks = lr.split_chunks(text, 1000)
        self.assertEqual([len(c.split()) for c in chunks], [1000, 1000, 500])

    def test_lines_are_not_split_mid_line(self):
        lines = [f"[00:0{i}:00] line {i} " + "w " * 40 for i in range(6)]
        chunks = lr.split_chunks("\n".join(lines), 100)
        for chunk in chunks:
            for line in chunk.splitlines():
                self.assertTrue(line.startswith("[00:0"))


class TranscriptTests(unittest.TestCase):
    def test_json_segments_get_timestamps_and_speakers(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.json"
            p.write_text(json.dumps({"segments": [
                {"start": 0, "text": " Karibu "},
                {"start": 3725.4, "speaker": "Chair", "text": "Agreed."},
            ]}), encoding="utf-8")
            self.assertEqual(lr.load_transcript(p),
                             "[00:00:00] Karibu\n[01:02:05] Chair: Agreed.")

    def test_json_text_field_and_plain_text(self):
        with tempfile.TemporaryDirectory() as d:
            j = Path(d) / "t.json"
            j.write_text(json.dumps({"text": " hello "}), encoding="utf-8")
            t = Path(d) / "t.txt"
            t.write_text("﻿habari\n", encoding="utf-8")
            self.assertEqual(lr.load_transcript(j), "hello")
            self.assertEqual(lr.load_transcript(t), "habari")

    def test_unknown_json_is_a_clear_error(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.json"
            p.write_text(json.dumps({"words": []}), encoding="utf-8")
            with self.assertRaises(SystemExit) as cm:
                lr.load_transcript(p)
            self.assertIn("'text'", str(cm.exception))


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.server = FakeServer()
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.src = self.dir / "meeting.txt"
        self.src.write_text(transcript(5000), encoding="utf-8")

    def tearDown(self):
        self.server.close()
        self.tmp.cleanup()

    def run_cli(self, *extra):
        return lr.main([str(self.src), "--url", self.server.url,
                        "--chunk-words", "1000", "--title", "Day 5 RCC",
                        *extra])

    def test_ollama_run_sends_num_ctx_and_writes_report(self):
        self.assertEqual(self.run_cli("--num-ctx", "12288"), 0)
        kinds = self.server.kinds()
        self.assertEqual(kinds.count("section"), 5)
        self.assertEqual(kinds[-1], "report")
        for path, body in self.server.requests:
            self.assertEqual(path, "/api/chat")
            self.assertFalse(body["stream"])
            self.assertEqual(body["options"]["num_ctx"], 12288)
        report = (self.dir / "meeting.report.md").read_text(encoding="utf-8")
        self.assertTrue(report.startswith("# Day 5 RCC\n"))
        self.assertIn("AI draft", report)
        self.assertIn("## Summary\nThe report body.", report)
        self.assertNotIn("<think>", report)

    def test_second_run_reuses_finished_sections(self):
        self.run_cli()
        first = len(self.server.requests)
        self.server.requests.clear()
        self.run_cli()
        self.assertEqual(self.server.kinds(), ["report"])
        self.assertGreater(first, 1)

    def test_kiswahili_report_uses_kiswahili_headings(self):
        self.run_cli("--language", "sw")
        _, body = self.server.requests[-1]
        prompt = body["messages"][1]["content"]
        self.assertIn("## Muhtasari", prompt)
        self.assertIn("## Hatua za kuchukua", prompt)
        self.assertIn("Write in Kiswahili", body["messages"][0]["content"])
        report = (self.dir / "meeting.report.md").read_text(encoding="utf-8")
        self.assertIn("Rasimu ya AI", report)

    def test_kiswahili_meeting_english_report(self):
        self.run_cli("--language", "sw", "--report-language", "en")
        _, first = self.server.requests[0]
        self.assertIn("transcript is in Kiswahili; write the notes in English",
                      first["messages"][1]["content"])

    def test_openai_compatible_server(self):
        self.run_cli("--api", "openai", "--model", "local")
        paths = {p for p, _ in self.server.requests}
        self.assertEqual(paths, {"/v1/chat/completions"})

    def test_long_notes_are_merged_before_the_report(self):
        self.server.close()
        self.server = FakeServer(note_words=400)   # 5 x 400 > 1000 budget
        self.run_cli()
        kinds = self.server.kinds()
        self.assertIn("merge", kinds)
        self.assertEqual(kinds[-1], "report")
        _, last = self.server.requests[-1]
        self.assertLess(len(last["messages"][1]["content"].split()), 1500)


class SetupErrorTests(unittest.TestCase):
    def test_server_not_running(self):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        model = lr.LocalModel(url=f"http://127.0.0.1:{port}", timeout=5)
        with self.assertRaises(SystemExit) as cm:
            model.chat("s", "u", 10)
        self.assertIn("Open the Ollama app", str(cm.exception))

    def test_model_not_downloaded(self):
        server = FakeServer(status=404,
                            error_body='{"error":"model \'x\' not found"}')
        try:
            model = lr.LocalModel(url=server.url)
            with self.assertRaises(SystemExit) as cm:
                model.chat("s", "u", 10)
            self.assertIn(f"ollama pull {lr.DEFAULT_MODEL}",
                          str(cm.exception))
        finally:
            server.close()

    def test_warns_when_a_section_nearly_fills_the_window(self):
        server = FakeServer(prompt_tokens=7800)
        try:
            model = lr.LocalModel(url=server.url, num_ctx=8192)
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                model.chat("s", "u", 1200)
            self.assertIn("may have been cut", err.getvalue())
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                lr.LocalModel(url=server.url, num_ctx=16384).chat("s", "u",
                                                                  1200)
            self.assertEqual(err.getvalue(), "")
        finally:
            server.close()

    def test_check_mode(self):
        server = FakeServer()
        try:
            self.assertEqual(lr.main(["--check", "--url", server.url]), 0)
            self.assertEqual(len(server.requests), 1)
        finally:
            server.close()


if __name__ == "__main__":
    unittest.main()
