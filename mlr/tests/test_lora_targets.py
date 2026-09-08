"""LoRA target selection, against a mock of Gemma 4's real module structure.

The failure this pins down: Gemma 4 wraps some projections in
Gemma4ClippableLinear, whose inner nn.Linear sits at `...q_proj.linear`. peft
matches target_modules by SUFFIX, so selecting by leaf name picks up both the
wrapper and the inner layer, and peft then refuses the wrapper because it is
not a module type it can replace.

torch is not installed in the environment these tests run in, so a minimal
stand-in is injected. Only isinstance checks and named_modules() are exercised,
which is exactly the surface the function under test uses.
"""

import sys
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _torch_nn():
    """Return torch.nn, preferring a real install.

    Injecting a fake torch into sys.modules when a real one exists poisons it
    for the whole process -- every later import in the run, including
    bitsandbytes, then binds against the stub. That is invisible locally, where
    torch is absent and the stub is correct, and breaks on any machine that has
    the real thing. So: use the real one whenever it imports.
    """
    try:
        import torch.nn as nn
        return nn
    except ImportError:
        pass

    import types
    torch = types.ModuleType("torch")
    nn = types.ModuleType("torch.nn")

    class Module:
        def __init__(self, *a, **k):
            pass

    class Linear(Module):
        # Signature-compatible with torch.nn.Linear so the tests below build
        # the same way against either implementation.
        def __init__(self, in_features=4, out_features=4, bias=True):
            super().__init__()

    class Embedding(Module):
        def __init__(self, num=4, dim=4):
            super().__init__()

    nn.Module, nn.Linear, nn.Embedding = Module, Linear, Embedding
    torch.nn = nn
    sys.modules["torch"], sys.modules["torch.nn"] = torch, nn
    return nn


nn = _torch_nn()

from mlr.training import discover_lora_targets, CANONICAL_PROJECTIONS  # noqa: E402


class ClippableLinear(nn.Module):
    """Stands in for Gemma4ClippableLinear: a wrapper peft cannot replace."""

    def __init__(self):
        super().__init__()


class FakeGemma4:
    """Module tree mirroring the names a real run reported."""

    def __init__(self, n_layers=2):
        self.mods = [("", nn.Module()), ("model", nn.Module()),
                     ("model.embed_tokens", nn.Embedding(4, 4)),
                     ("lm_head", nn.Linear(4, 4))]
        # E4B is multimodal. Its vision and audio encoders reuse the SAME
        # projection names as the language model, so a name-based match sweeps
        # them in -- which a real run did, adapting 406 modules across all three
        # towers for a text-only dataset.
        for i in range(2):
            for proj in ("q_proj", "k_proj", "v_proj", "o_proj"):
                self.mods.append(
                    (f"model.vision_tower.encoder.layers.{i}.self_attn.{proj}",
                     ClippableLinear()))
                self.mods.append(
                    (f"model.vision_tower.encoder.layers.{i}.self_attn.{proj}.linear",
                     nn.Linear(4, 4)))
            for proj in ("gate_proj", "up_proj", "down_proj"):
                self.mods.append(
                    (f"model.vision_tower.encoder.layers.{i}.mlp.{proj}.linear",
                     nn.Linear(4, 4)))
            for proj in ("q_proj", "k_proj", "v_proj"):
                self.mods.append(
                    (f"model.audio_tower.layers.{i}.self_attn.{proj}.linear",
                     nn.Linear(4, 4)))
        for i in range(n_layers):
            base = f"model.layers.{i}"
            # Attention projections are WRAPPED: the real Linear is one deeper.
            for proj in ("q_proj", "k_proj", "v_proj", "o_proj"):
                self.mods.append((f"{base}.self_attn.{proj}", ClippableLinear()))
                self.mods.append((f"{base}.self_attn.{proj}.linear", nn.Linear(4, 4)))
            # MLP projections are plain.
            for proj in ("gate_proj", "up_proj", "down_proj"):
                self.mods.append((f"{base}.mlp.{proj}", nn.Linear(4, 4)))
            # Gemma 4 extras that a standard QLoRA recipe leaves alone.
            self.mods.append((f"{base}.per_layer_input_gate", nn.Linear(4, 4)))
            self.mods.append((f"{base}.per_layer_projection", nn.Linear(4, 4)))
            self.mods.append((f"{base}.altup.correction_coefs", nn.Linear(4, 4)))

    def named_modules(self):
        return iter(self.mods)

    def get(self, name):
        return dict(self.mods)[name]


class TargetSelection(unittest.TestCase):
    def setUp(self):
        self.model = FakeGemma4()
        self.targets = discover_lora_targets(self.model)

    def test_every_target_is_a_type_peft_can_replace(self):
        """The actual bug: a wrapper class reaching peft and being refused."""
        for name in self.targets:
            module = self.model.get(name)
            self.assertIsInstance(
                module, nn.Linear,
                f"{name} is {type(module).__name__}, which peft cannot wrap")

    def test_the_wrapper_itself_is_never_targeted(self):
        for name in self.targets:
            self.assertNotIsInstance(self.model.get(name), ClippableLinear)
        # ...but the Linear inside it IS reached.
        self.assertIn("model.layers.0.self_attn.q_proj.linear", self.targets)

    def test_full_paths_not_leaf_names(self):
        # A leaf name like "linear" would match the wrapper by suffix too.
        for name in self.targets:
            self.assertIn(".", name, f"{name} is a leaf name, not a full path")

    def test_covers_attention_and_mlp(self):
        leaves = {n.rsplit(".", 1)[-1] for n in self.targets}
        paths = " ".join(self.targets)
        for proj in CANONICAL_PROJECTIONS:
            self.assertIn(proj, paths, f"{proj} not adapted")
        self.assertTrue(leaves & {"linear"}, "wrapped projections missed")

    def test_excludes_lm_head_and_embeddings(self):
        joined = " ".join(self.targets)
        self.assertNotIn("lm_head", joined)
        self.assertNotIn("embed_tokens", joined)

    def test_excludes_non_canonical_gemma4_extras(self):
        joined = " ".join(self.targets)
        for extra in ("per_layer_input_gate", "per_layer_projection",
                      "altup.correction_coefs"):
            self.assertNotIn(extra, joined,
                             f"{extra} is not part of a standard QLoRA recipe")

    def test_excludes_the_vision_and_audio_towers(self):
        """A real run adapted 406 modules across all three towers.

        The dataset is text. Adapting a vision or audio encoder spends adapter
        capacity on weights that never see a token of it.
        """
        joined = " ".join(self.targets)
        self.assertNotIn("vision_tower", joined)
        self.assertNotIn("audio_tower", joined)
        self.assertTrue(self.targets, "language-model projections still adapted")
        for name in self.targets:
            self.assertNotIn("vision", name)
            self.assertNotIn("audio", name)

    def test_raises_rather_than_silently_adapting_nothing(self):
        class Empty:
            def named_modules(self):
                return iter([("", nn.Module()), ("lm_head", nn.Linear(4, 4))])
        with self.assertRaises(RuntimeError):
            discover_lora_targets(Empty())


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TrainingArgumentFiltering(unittest.TestCase):
    """TrainingArguments' keyword set moves between transformers versions.

    A real run died on `warmup_ratio`, removed in transformers 5.16. Losing a
    whole training run to an argument that only tunes a warmup schedule is a
    bad trade, so unknown keywords are dropped with a note instead.
    """

    @staticmethod
    def filter_kwargs(wanted, accepted):
        if "kwargs" in accepted:
            return dict(wanted), []
        dropped = sorted(k for k in wanted if k not in accepted)
        return {k: v for k, v in wanted.items() if k in accepted}, dropped

    def test_drops_only_the_unsupported_keyword(self):
        wanted = {"output_dir": "x", "num_train_epochs": 3, "warmup_ratio": 0.03}
        kept, dropped = self.filter_kwargs(
            wanted, {"self", "output_dir", "num_train_epochs"})
        self.assertEqual(dropped, ["warmup_ratio"])
        self.assertEqual(kept, {"output_dir": "x", "num_train_epochs": 3})

    def test_keeps_everything_when_all_are_supported(self):
        wanted = {"output_dir": "x", "warmup_ratio": 0.03}
        kept, dropped = self.filter_kwargs(wanted, {"output_dir", "warmup_ratio"})
        self.assertEqual(dropped, [])
        self.assertEqual(kept, wanted)

    def test_a_kwargs_signature_disables_filtering(self):
        wanted = {"anything": 1}
        kept, dropped = self.filter_kwargs(wanted, {"kwargs"})
        self.assertEqual(dropped, [])
        self.assertEqual(kept, wanted)
