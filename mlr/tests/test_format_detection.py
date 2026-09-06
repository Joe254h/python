"""Detection of a model's thinking format from its tokenizer.

The real Gemma 4 tokenizer was unreachable when this was written, so these
tests stand in for it: mock tokenizers shaped like the conventions real
thinking models actually use. They pin down the behaviour that matters --
that a template which opens the reasoning block itself is recognised as such,
because getting that wrong fails silently in two directions at once (every
generation scored as malformed, and training that teaches a doubled marker).
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mlr.format_guard import (ThinkingFormat, detect_thinking_format, parse,
                              FormatError, GEMMA4_THINKING)


class MockTokenizer:
    """Chat template with the knobs real thinking models vary."""

    def __init__(self, open_tok, close_tok, specials, *,
                 emits_open_in_prompt=True, supports_enable_thinking=True,
                 empty_block_when_off=True):
        self.open_tok, self.close_tok = open_tok, close_tok
        self.all_special_tokens = list(specials)
        self.additional_special_tokens = []
        self.added_tokens_decoder = {}
        self.emits_open_in_prompt = emits_open_in_prompt
        self.supports_enable_thinking = supports_enable_thinking
        self.empty_block_when_off = empty_block_when_off
        self.chat_template = f"...{open_tok}...{close_tok}..."

    def apply_chat_template(self, messages, tokenize=False,
                            add_generation_prompt=False, enable_thinking=None):
        if enable_thinking is not None and not self.supports_enable_thinking:
            raise TypeError("unexpected keyword argument 'enable_thinking'")
        out = "<start_of_turn>user\n" + messages[-1]["content"] + "<end_of_turn>\n"
        if add_generation_prompt:
            out += "<start_of_turn>model\n"
            if self.emits_open_in_prompt:
                out += self.open_tok
                if enable_thinking is False and self.empty_block_when_off:
                    out += self.close_tok
        return out


class Detection(unittest.TestCase):
    def test_gemma4_style_channel_template(self):
        tok = MockTokenizer("<|channel|>thought\n", "<|end_channel|>",
                            ["<start_of_turn>", "<end_of_turn>",
                             "<|channel|>", "<|end_channel|>"])
        fmt = detect_thinking_format(tok)
        self.assertIsNotNone(fmt)
        self.assertEqual(fmt.open_token, "<|channel|>thought\n")
        self.assertEqual(fmt.close_token, "<|end_channel|>")
        self.assertTrue(fmt.open_emitted_by_template)

    def test_think_tag_template(self):
        tok = MockTokenizer("<think>\n", "</think>",
                            ["<start_of_turn>", "<end_of_turn>", "<think>", "</think>"])
        fmt = detect_thinking_format(tok)
        self.assertIsNotNone(fmt)
        self.assertEqual(fmt.close_token, "</think>")
        self.assertTrue(fmt.open_emitted_by_template)

    def test_template_that_does_not_open_the_block(self):
        # Model emits both markers itself; nothing extra in the prompt.
        tok = MockTokenizer("<think>", "</think>",
                            ["<start_of_turn>", "<think>", "</think>"],
                            emits_open_in_prompt=False)
        fmt = detect_thinking_format(tok)
        self.assertIsNotNone(fmt)
        self.assertEqual(fmt.close_token, "</think>")
        self.assertEqual(fmt.open_token, "<think>")
        self.assertFalse(fmt.open_emitted_by_template)

    def test_returns_none_rather_than_guessing(self):
        # No reasoning-named tokens at all: an honest failure beats a wrong answer.
        tok = MockTokenizer("", "", ["<start_of_turn>", "<end_of_turn>"],
                            emits_open_in_prompt=False)
        self.assertIsNone(detect_thinking_format(tok))

    def test_tokenizer_without_enable_thinking_kwarg(self):
        # The diff cannot run, so open_emitted_by_template has to be settled by
        # noticing that a plain generation prompt ends with the opening marker.
        tok = MockTokenizer("<think>", "</think>",
                            ["<think>", "</think>", "<start_of_turn>"],
                            supports_enable_thinking=False)
        fmt = detect_thinking_format(tok)
        self.assertIsNotNone(fmt)
        self.assertEqual(fmt.close_token, "</think>")
        self.assertTrue(fmt.open_emitted_by_template,
                        "prompt ends with the opening marker, so the template opens the block")

    def test_no_kwarg_and_model_emits_both_stays_false(self):
        tok = MockTokenizer("<think>", "</think>",
                            ["<think>", "</think>", "<start_of_turn>"],
                            supports_enable_thinking=False, emits_open_in_prompt=False)
        fmt = detect_thinking_format(tok)
        self.assertIsNotNone(fmt)
        self.assertFalse(fmt.open_emitted_by_template)


class Resolution(unittest.TestCase):
    def test_detection_overrides_a_wrong_constant(self):
        # This is the Kaggle failure: the configured guess does not match the
        # real tokenizer. Detection must win rather than raising.
        tok = MockTokenizer("<|channel|>thought\n", "<|end_channel|>",
                            ["<|channel|>", "<|end_channel|>", "<start_of_turn>"])
        resolved = GEMMA4_THINKING.resolve_from_tokenizer(tok)
        self.assertEqual(resolved.close_token, "<|end_channel|>")
        self.assertNotEqual(resolved.close_token, GEMMA4_THINKING.close_token)

    def test_raises_only_when_genuinely_unknown(self):
        tok = MockTokenizer("", "", ["<start_of_turn>"], emits_open_in_prompt=False)
        tok.chat_template = "no reasoning markers here"
        with self.assertRaises(FormatError) as ctx:
            GEMMA4_THINKING.resolve_from_tokenizer(tok)
        self.assertIn("inspect_chat_template", str(ctx.exception))


class PromptOpenedBlocks(unittest.TestCase):
    """The bug the Kaggle traceback was hiding."""

    FMT = ThinkingFormat("<|channel|>thought\n", "<|end_channel|>",
                         open_emitted_by_template=True)

    def test_generation_without_an_opening_marker_parses(self):
        # What the model actually emits when the template opened the block.
        out = "Kwanza, 3 x 12 = 36.<|end_channel|>Jibu ni 36."
        p = parse(out, self.FMT)
        self.assertTrue(p.ok, p.errors)
        self.assertEqual(p.thinking, "Kwanza, 3 x 12 = 36.")
        self.assertEqual(p.answer, "Jibu ni 36.")

    def test_same_text_fails_when_the_template_does_not_open_the_block(self):
        strict = ThinkingFormat("<|channel|>thought\n", "<|end_channel|>")
        p = parse("Kwanza, 3 x 12 = 36.<|end_channel|>Jibu ni 36.", strict)
        self.assertFalse(p.ok)
        self.assertIn("missing opening delimiter", p.errors)

    def test_training_target_omits_the_marker_the_template_supplies(self):
        target = self.FMT.training_target("Kwanza, 3 x 12 = 36.", "Jibu ni 36.")
        self.assertFalse(target.startswith(self.FMT.open_token),
                         "training target must not duplicate the template's marker")
        self.assertEqual(target, "Kwanza, 3 x 12 = 36.<|end_channel|>Jibu ni 36.")
        # Round-trip: what we train on is what we can parse back.
        self.assertTrue(parse(target, self.FMT).ok)

    def test_training_target_keeps_the_marker_when_the_model_must_emit_it(self):
        strict = ThinkingFormat("<think>", "</think>")
        self.assertEqual(strict.training_target("a", "b"), "<think>a</think>b")

    def test_a_duplicated_marker_is_still_caught(self):
        out = "text <|channel|>thought\nmore<|end_channel|>answer"
        self.assertFalse(parse(out, self.FMT).ok)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class RealGemma4Tokenizer(unittest.TestCase):
    """Built from an actual google/gemma-4-E4B-it dump (transformers 5.0.0).

    Every string below was copied from a real run, not inferred. This is the
    regression test that stops the format constants drifting back to a guess.
    """

    SPECIALS = ['<tool_response|>', '<|tool_response>', '<tool_call|>', '<|tool_call>',
                '<channel|>', '<|channel>', '<|image|>', '<|video|>', '<|think|>',
                '<|audio|>', '<image|>', '<|audio>', '<audio|>', '<|image>',
                '<|turn>', '<turn|>', '<tool|>', '<|tool>', '<mask>', '<unk>',
                '<eos>', '<|"|>', '<pad>', '<bos>']

    ON = ('<bos><|turn>system\n<|think|>\n<turn|>\n<|turn>user\n'
          '__PROBE__<turn|>\n<|turn>model\n')
    OFF = '<bos><|turn>user\n__PROBE__<turn|>\n<|turn>model\n'

    TEMPLATE = (
        "{%- macro strip_thinking(text) -%}\n"
        "{%- for part in text.split('<channel|>') -%}\n"
        "{%- if '<|channel>' in part -%}\n"
        "{%- set enable_thinking = enable_thinking | default(false) -%}\n"
        "{%- if enable_thinking -%}\n"
        "{{- '<|think|>\\n' -}}\n"
        "{%- set thinking_text = message.get('reasoning') or message.get('reasoning_content') -%}\n"
        "{%- if thinking_text and thinking_gate -%}\n"
        "{{- '<|channel>thought\\n' + thinking_text + '\\n<channel|>' -}}\n"
        "{%- elif ns.prev_message_type == 'tool_response' and enable_thinking -%}\n"
        "{{- '<|channel>thought\\n' -}}\n"
    )

    class Tok:
        def __init__(self, outer):
            self.all_special_tokens = list(outer.SPECIALS)
            self.additional_special_tokens = []
            self.added_tokens_decoder = {}
            self.chat_template = outer.TEMPLATE
            self._on, self._off = outer.ON, outer.OFF

        def apply_chat_template(self, messages, tokenize=False,
                                add_generation_prompt=False, enable_thinking=None):
            return self._on if enable_thinking else self._off

    def setUp(self):
        self.tok = self.Tok(self)

    def test_detects_the_real_delimiters(self):
        fmt = detect_thinking_format(self.tok, name="gemma4")
        self.assertIsNotNone(fmt, "detection must not fail on the real tokenizer")
        self.assertEqual(fmt.open_token, "<|channel>thought\n")
        self.assertEqual(fmt.close_token, "<channel|>")

    def test_model_emits_both_markers_itself(self):
        # The generation prompt ends at '<|turn>model\n' -- no channel is open,
        # so the model must emit the opening marker and a training target must
        # include it.
        fmt = detect_thinking_format(self.tok, name="gemma4")
        self.assertFalse(fmt.open_emitted_by_template)
        self.assertTrue(self.ON.endswith("<|turn>model\n"))

    def test_detection_agrees_with_the_shipped_constants(self):
        self.assertEqual(detect_thinking_format(self.tok, name="gemma4"),
                         GEMMA4_THINKING)

    def test_round_trip_on_a_realistic_generation(self):
        fmt = detect_thinking_format(self.tok, name="gemma4")
        generated = ("<|channel>thought\nKwanza, 3 x 12 = 36 kwa jumla."
                     "\n<channel|>Jibu ni 36.")
        p = parse(generated, fmt)
        self.assertTrue(p.ok, p.errors)
        self.assertEqual(p.thinking, "Kwanza, 3 x 12 = 36 kwa jumla.")
        self.assertEqual(p.answer, "Jibu ni 36.")

    def test_thinking_is_enabled_by_a_system_token_not_an_open_channel(self):
        # enable_thinking=True injects <|think|> into a system turn. It does NOT
        # pre-open a channel -- which is why the render-diff heuristic alone
        # could not settle this and the template source had to be read.
        self.assertIn("<|think|>", self.ON)
        self.assertNotIn("<|think|>", self.OFF)
        self.assertNotIn("<|channel>", self.ON)
