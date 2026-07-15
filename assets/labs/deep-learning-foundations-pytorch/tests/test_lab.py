from __future__ import annotations

from pathlib import Path

from dl_foundations.data import make_xor_gaussians
from dl_foundations.train import autograd_demo, load_checkpoint_accuracy, train_model


def test_dataset_shapes_and_balance() -> None:
    bundle = make_xor_gaussians(n_per_quadrant=20, seed=11)
    assert bundle.train_x.shape[1] == 2
    assert bundle.train_y.ndim == 1
    assert bundle.train_x.shape[0] == bundle.train_y.shape[0]
    assert 0.35 <= bundle.train_y.mean().item() <= 0.65
    assert bundle.test_x.shape[0] > 0


def test_autograd_matches_finite_difference() -> None:
    demo = autograd_demo()
    assert demo["max_abs_error_vs_finite_difference"] < 2e-3


def test_mlp_beats_linear_on_nonlinear_task(tmp_path: Path) -> None:
    linear = train_model("linear", tmp_path / "linear", epochs=80, learning_rate=0.03)
    mlp = train_model("mlp", tmp_path / "mlp", epochs=120, learning_rate=0.03)
    assert mlp.test.accuracy >= 0.90
    assert mlp.test.accuracy - linear.test.accuracy >= 0.25


def test_checkpoint_roundtrip(tmp_path: Path) -> None:
    result = train_model("mlp", tmp_path / "mlp", epochs=40, learning_rate=0.03)
    loaded_acc = load_checkpoint_accuracy(Path(result.checkpoint))
    assert abs(loaded_acc - result.test.accuracy) < 1e-6
