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


def _install_fake_torch():
    """Minimal torch.nn stand-in: enough for isinstance checks."""
    if "torch" in sys.modules and hasattr(sys.modules["torch"], "nn"):
        return sys.modules["torch"].nn
    torch = types.ModuleType("torch")
    nn = types.ModuleType("torch.nn")

    class Module:
        pass

    class Linear(Module):
        def __init__(self, name="Linear"):
            self._n = name

        def __repr__(self):
            return f"{type(self).__name__}()"

    class Embedding(Module):
        pass

    nn.Module, nn.Linear, nn.Embedding = Module, Linear, Embedding
    torch.nn = nn
    sys.modules["torch"], sys.modules["torch.nn"] = torch, nn
    return nn


nn = _install_fake_torch()

from mlr.training import discover_lora_targets, CANONICAL_PROJECTIONS  # noqa: E402


class ClippableLinear(nn.Module):
    """Stands in for Gemma4ClippableLinear: a wrapper peft cannot replace."""


class FakeGemma4:
    """Module tree mirroring the names a real run reported."""

    def __init__(self, n_layers=2):
        self.mods = [("", nn.Module()), ("model", nn.Module()),
                     ("model.embed_tokens", nn.Embedding()),
                     ("lm_head", nn.Linear())]
        for i in range(n_layers):
            base = f"model.layers.{i}"
            # Attention projections are WRAPPED: the real Linear is one deeper.
            for proj in ("q_proj", "k_proj", "v_proj", "o_proj"):
                self.mods.append((f"{base}.self_attn.{proj}", ClippableLinear()))
                self.mods.append((f"{base}.self_attn.{proj}.linear", nn.Linear()))
            # MLP projections are plain.
            for proj in ("gate_proj", "up_proj", "down_proj"):
                self.mods.append((f"{base}.mlp.{proj}", nn.Linear()))
            # Gemma 4 extras that a standard QLoRA recipe leaves alone.
            self.mods.append((f"{base}.per_layer_input_gate", nn.Linear()))
            self.mods.append((f"{base}.per_layer_projection", nn.Linear()))
            self.mods.append((f"{base}.altup.correction_coefs", nn.Linear()))

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

    def test_raises_rather_than_silently_adapting_nothing(self):
        class Empty:
            def named_modules(self):
                return iter([("", nn.Module()), ("lm_head", nn.Linear())])
        with self.assertRaises(RuntimeError):
            discover_lora_targets(Empty())


if __name__ == "__main__":
    unittest.main(verbosity=2)
