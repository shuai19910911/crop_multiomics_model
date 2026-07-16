#!/usr/bin/env python3
"""Render the public training-status and candidate-architecture figures."""

from __future__ import annotations

import atexit
import csv
import hashlib
import io
import json
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SOURCE_DATE_EPOCH", "0")

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image, ImageDraw, ImageFont

SNAPSHOT_ACTIVE = os.environ.get("CROP_FIGURE_SNAPSHOT_ACTIVE") == "1"
EXECUTED_SCRIPT = Path(__file__).resolve()
LIVE_SCRIPT = Path(os.environ.get("CROP_FIGURE_LIVE_SCRIPT", EXECUTED_SCRIPT)).resolve()
ROOT = Path(os.environ.get("CROP_FIGURE_ROOT", EXECUTED_SCRIPT.parents[2])).resolve()
ASSETS = ROOT / "docs" / "assets"
GENERATION_ROOT = ASSETS / "figure_generations"
CURRENT_POINTER = ASSETS / "figure_current.json"
OUTPUT_DIR: Path | None = None

STATUS_KEYS = {
    "as_of",
    "stage0_status",
    "stage1_governance_authorized",
    "stage1_complete_execution_authorized",
    "stage2_data_promotion_authorized",
    "formal_test_access_authorized",
    "gpu_or_large_download_authorized",
    "model_training_runs",
    "optimizer_updates",
    "gpu_hours",
    "checkpoints",
    "training_curve_rows",
    "note",
}
ZERO_FIELDS = (
    "model_training_runs",
    "optimizer_updates",
    "gpu_hours",
    "checkpoints",
    "training_curve_rows",
)
INPUT_NAMES = (
    "training_status.json",
    "training_curve_source.csv",
    "model_architecture_gpt_source.png",
)
SCRIPT_INPUT_NAME = "scripts/figures/render_public_figures.py"
OUTPUT_NAMES = (
    "training_progress.png",
    "training_progress.pdf",
    "model_architecture_python.png",
    "model_architecture_python.pdf",
    "model_architecture_gpt.png",
    "model_architecture_gpt.pdf",
)
GPT_POLICY_BANNER = (
    "PLANNED / NOT YET VERIFIED | Concept only: frozen splits -> external seal -> "
    "leakage audit -> one-shot claim (none exists yet)"
)

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 8,
        "pdf.fonttype": 42,
        "axes.linewidth": 0.8,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "legend.frameon": False,
    }
)

NAVY = "#173B66"
BLUE = "#4C78A8"
TEAL = "#2A9D8F"
PURPLE = "#7C6BB0"
GREEN = "#6FA85F"
ORANGE = "#E69F5B"
RED = "#C43D4E"
LIGHT_BLUE = "#EEF5FC"
LIGHT_PURPLE = "#F3EFFA"
LIGHT_GREEN = "#EFF7EC"
LIGHT_ORANGE = "#FFF3E8"
LIGHT_RED = "#FFF2F2"
GRAY = "#5B6573"


def _identity(file_stat: os.stat_result) -> tuple[int, int, int, int]:
    return file_stat.st_dev, file_stat.st_ino, file_stat.st_size, file_stat.st_mtime_ns


def read_stable_bytes(path: Path) -> bytes:
    path_before = path.lstat()
    if stat.S_ISLNK(path_before.st_mode) or not stat.S_ISREG(path_before.st_mode):
        raise ValueError(f"input must be a regular non-symlink file: {path}")
    with path.open("rb") as handle:
        fd_before = os.fstat(handle.fileno())
        if _identity(path_before) != _identity(fd_before):
            raise ValueError(f"input changed while opening: {path}")
        data = handle.read()
        fd_after = os.fstat(handle.fileno())
    path_after = path.lstat()
    if _identity(fd_before) != _identity(fd_after) or _identity(fd_after) != _identity(path_after):
        raise ValueError(f"input changed while reading: {path}")
    if len(data) != fd_after.st_size:
        raise ValueError(f"input size changed while reading: {path}")
    return data


def read_training_rows(source_bytes: bytes | None = None) -> list[dict[str, str]]:
    if source_bytes is None:
        source_bytes = read_stable_bytes(ASSETS / "training_curve_source.csv")
    handle = io.StringIO(source_bytes.decode("utf-8"), newline="")
    reader = csv.DictReader(handle)
    expected = ["run_id", "step", "split", "metric", "value", "checkpoint_selected"]
    if reader.fieldnames != expected:
        raise ValueError(f"training source columns must be {expected}")
    return list(reader)


def read_zero_training_status(
    rows: list[dict[str, str]], status_bytes: bytes | None = None
) -> dict[str, object]:
    if status_bytes is None:
        status_bytes = read_stable_bytes(ASSETS / "training_status.json")
    status = json.loads(status_bytes.decode("utf-8"))
    if not isinstance(status, dict) or set(status) != STATUS_KEYS:
        raise ValueError("training_status.json has missing or unexpected fields")
    if type(status["as_of"]) is not str or not status["as_of"]:
        raise ValueError("training status as_of must be a non-empty string")
    if type(status["note"]) is not str or not status["note"]:
        raise ValueError("training status note must be a non-empty string")
    if status["stage0_status"] != "COMPLETE":
        raise ValueError("zero-observation figure requires stage0_status=COMPLETE")
    expected_authorization = {
        "stage1_governance_authorized": True,
        "stage1_complete_execution_authorized": False,
        "stage2_data_promotion_authorized": False,
        "formal_test_access_authorized": False,
        "gpu_or_large_download_authorized": False,
    }
    for key, expected in expected_authorization.items():
        if type(status[key]) is not bool or status[key] is not expected:
            raise ValueError(f"zero-observation figure has incompatible {key}")
    for key in ZERO_FIELDS:
        if type(status[key]) is not int or status[key] != 0:
            raise ValueError(f"zero-observation figure requires integer {key}=0")
    if len(rows) != status["training_curve_rows"]:
        raise ValueError("training source row count does not match training_status.json")
    return status


def save_figure(fig: plt.Figure, stem: str) -> None:
    destination = OUTPUT_DIR or ASSETS
    fig.savefig(destination / f"{stem}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(
        destination / f"{stem}.pdf",
        bbox_inches="tight",
        facecolor="white",
        metadata={"Creator": "Crop Multi-Omics Model", "CreationDate": None, "ModDate": None},
    )
    plt.close(fig)


def render_training_progress(
    rows: list[dict[str, str]] | None = None,
    status: dict[str, object] | None = None,
) -> None:
    if rows is None:
        rows = read_training_rows()
    if status is None:
        status = read_zero_training_status(rows)

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.2))
    fig.subplots_adjust(left=0.08, right=0.98, top=0.74, bottom=0.25, wspace=0.30)
    fig.suptitle(
        "Training progress — no model training started",
        y=0.97,
        fontsize=15,
        weight="bold",
        color=NAVY,
    )
    fig.text(
        0.5,
        0.865,
        f"{status['model_training_runs']} runs  •  {status['optimizer_updates']} optimizer updates  •  "
        f"{status['gpu_hours']} GPU hours  •  {status['checkpoints']} checkpoints",
        ha="center",
        va="center",
        fontsize=9,
        color=GRAY,
    )

    panel_specs = [
        (axes[0], "A", "Optimization trace", "Mean mini-batch loss\n(lower is better)"),
        (
            axes[1],
            "B",
            "Validation trace",
            "Frozen validation metric\n(task-specific; not yet defined)",
        ),
    ]
    for ax, letter, title, ylabel in panel_specs:
        ax.set_title(f"{letter}   {title}", loc="left", fontsize=11, weight="bold", color=NAVY)
        ax.set_xlabel("Training step (optimizer updates)")
        ax.set_ylabel(ylabel)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([0])
        ax.set_yticks([])
        ax.grid(axis="x", color="#D8DEE8", linewidth=0.6)
        ax.text(
            0.5,
            0.56,
            "NO OBSERVATIONS",
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=14,
            weight="bold",
            color=RED,
        )
        ax.text(
            0.5,
            0.42,
            "Training is gated by evidence, data, license,\narchitecture and statistical contracts.",
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=8.5,
            color=GRAY,
        )

    fig.text(
        0.5,
        0.035,
        f"Stage 0 governance: {status['stage0_status']}  |  Stage 1 bounded setup/smoke: authorized; "
        "complete execution: blocked.\nStage 2, formal test, GPU and large downloads: not authorized.\n"
        "Source CSV contains a header only; no simulated loss or validation points are shown.",
        ha="center",
        va="bottom",
        fontsize=7.5,
        color=GRAY,
    )
    save_figure(fig, "training_progress")


def box(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    text: str,
    *,
    face: str,
    edge: str,
    fontsize: float = 7.5,
    weight: str = "normal",
    radius: float = 0.12,
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle=f"round,pad=0.03,rounding_size={radius}",
        linewidth=1.2,
        edgecolor=edge,
        facecolor=face,
    )
    ax.add_patch(patch)
    ax.text(
        x + width / 2,
        y + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        color=NAVY,
        weight=weight,
    )


def arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = "#374151",
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=10,
            linewidth=1.25,
            color=color,
            shrinkA=1,
            shrinkB=1,
        )
    )


def render_python_architecture() -> None:
    fig, ax = plt.subplots(figsize=(15.5, 9.2))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9.4)
    ax.axis("off")
    ax.text(
        8,
        9.12,
        "Candidate architecture — not frozen",
        ha="center",
        va="center",
        fontsize=16,
        weight="bold",
        color=NAVY,
    )
    ax.text(1.25, 8.62, "Candidate inputs", ha="center", fontsize=9, weight="bold", color=NAVY)
    ax.text(
        4.0,
        8.62,
        "Modality-specific\ntokenizers & encoders",
        ha="center",
        fontsize=9,
        weight="bold",
        color=NAVY,
    )

    inputs = [
        ("Genome & variants", LIGHT_PURPLE, PURPLE),
        ("Transcriptome", LIGHT_BLUE, BLUE),
        ("Regulatory / epigenome", LIGHT_GREEN, GREEN),
        ("Proteome / metabolome", LIGHT_ORANGE, ORANGE),
        ("Environment &\nexperiment", "#EAF8F7", TEAL),
    ]
    y_values = [7.55, 6.38, 5.21, 4.04, 2.87]
    for (label, face, edge), y in zip(inputs, y_values, strict=True):
        box(ax, 0.25, y, 2.05, 0.72, label, face=face, edge=edge, weight="bold")
        encoder = label.replace(" & ", " / ") + "\ntokenizer / encoder"
        box(ax, 2.85, y, 2.35, 0.72, encoder, face=face, edge=edge, fontsize=7.0)
        arrow(ax, (2.31, y + 0.36), (2.83, y + 0.36))
        arrow(ax, (5.21, y + 0.36), (5.67, y + 0.36))

    box(ax, 5.7, 2.45, 2.65, 5.82, "", face="#F5F9FD", edge=NAVY)
    ax.text(
        7.025,
        7.85,
        "Condition-aware\nhierarchical fusion",
        ha="center",
        va="center",
        fontsize=11,
        weight="bold",
        color=NAVY,
    )
    box(ax, 6.0, 6.62, 2.05, 0.62, "Cross-modal alignment", face=LIGHT_BLUE, edge=BLUE, fontsize=7.2)
    box(ax, 6.0, 5.65, 2.05, 0.62, "Missing-modality gating", face=LIGHT_PURPLE, edge=PURPLE, fontsize=7.2)
    box(
        ax,
        6.0,
        4.36,
        2.05,
        0.92,
        "Biological hierarchy\ngene → sample → tissue\n→ environment",
        face=LIGHT_GREEN,
        edge=GREEN,
        fontsize=7.0,
    )
    ax.text(
        7.025,
        3.18,
        "Dimensions, parameter count\nand final topology: TBD\nafter evidence review",
        ha="center",
        va="center",
        fontsize=7.2,
        color=GRAY,
        style="italic",
    )

    box(ax, 8.8, 5.35, 2.95, 2.78, "", face="#FBF9FE", edge=PURPLE)
    ax.text(10.275, 7.78, "Candidate pretraining objectives", ha="center", fontsize=7.7, weight="bold", color=NAVY)
    box(ax, 9.08, 6.95, 2.39, 0.48, "Masked reconstruction", face=LIGHT_PURPLE, edge=PURPLE, fontsize=6.8)
    box(ax, 9.08, 6.24, 2.39, 0.48, "Cross-modal matching", face=LIGHT_PURPLE, edge=PURPLE, fontsize=6.8)
    box(ax, 9.08, 5.53, 2.39, 0.48, "Contrastive alignment", face=LIGHT_PURPLE, edge=PURPLE, fontsize=6.8)
    arrow(ax, (8.36, 6.95), (8.78, 6.95))

    box(ax, 9.08, 3.33, 2.39, 0.88, "Task representations", face="#EAF8F7", edge=TEAL, fontsize=8.0, weight="bold")
    arrow(ax, (8.36, 4.20), (9.06, 3.78))

    task_specs = [
        ("Molecular-state prediction", 12.45, 6.02),
        ("Phenotype & G×E prediction", 12.45, 4.88),
        ("Gene / variant prioritization", 12.45, 3.74),
        ("Cross-species & low-shot transfer", 12.45, 2.60),
    ]
    for label, x, y in task_specs:
        box(ax, x, y, 3.05, 0.78, label, face="#EAF8F7", edge=TEAL, fontsize=7.0, weight="bold")
    for _, x, y in task_specs:
        arrow(ax, (11.49, 3.78), (x - 0.02, y + 0.39))

    box(ax, 0.55, 0.35, 14.9, 1.35, "", face=LIGHT_RED, edge=RED)
    governance = [
        ("External-test firewall", 0.85),
        ("Identity & label seal", 4.45),
        ("Zero-access audit", 8.05),
        ("One-shot claim", 11.65),
    ]
    for label, x in governance:
        box(ax, x, 0.72, 2.45, 0.64, label, face="white", edge=RED, fontsize=7.6, weight="bold")
    for start, end in [(3.31, 4.43), (6.91, 8.03), (10.51, 11.63)]:
        arrow(ax, (start, 1.04), (end, 1.04), color=RED)
    ax.text(
        8,
        0.16,
        "Planned / not yet verified: formal external-test bytes, labels, predictions and metrics stay outside training and model selection.",
        ha="center",
        fontsize=7.2,
        color=RED,
    )

    save_figure(fig, "model_architecture_python")


def render_gpt_architecture(source_bytes: bytes | None = None) -> None:
    if source_bytes is None:
        source_bytes = read_stable_bytes(ASSETS / "model_architecture_gpt_source.png")
    destination = OUTPUT_DIR or ASSETS
    with Image.open(io.BytesIO(source_bytes)) as source:
        image = source.convert("RGB")

    width, height = image.size
    draw = ImageDraw.Draw(image)
    left, right = int(width * 0.05), int(width * 0.95)
    top, bottom = int(height * 0.735), int(height * 0.785)
    border = max(2, width // 700)
    draw.rounded_rectangle(
        (left, top, right, bottom),
        radius=max(8, height // 90),
        fill=(255, 248, 248),
        outline=(196, 61, 78),
        width=border,
    )
    font_path = font_manager.findfont(
        font_manager.FontProperties(family="DejaVu Sans", weight="bold")
    )
    font_size = max(12, int(height * 0.024))
    while True:
        font = ImageFont.truetype(font_path, font_size)
        text_box = draw.textbbox((0, 0), GPT_POLICY_BANNER, font=font)
        if text_box[2] - text_box[0] <= right - left - 24 or font_size <= 12:
            break
        font_size -= 1
    draw.text(
        ((left + right) / 2, (top + bottom) / 2),
        GPT_POLICY_BANNER,
        fill=(150, 24, 40),
        font=font,
        anchor="mm",
    )
    image.save(destination / "model_architecture_gpt.png", "PNG", dpi=(300, 300))
    image.save(
        destination / "model_architecture_gpt.pdf",
        "PDF",
        resolution=300.0,
        creator="Crop Multi-Omics Model",
        creationDate=None,
        modDate=None,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def input_path(name: str) -> Path:
    return EXECUTED_SCRIPT if name == SCRIPT_INPUT_NAME else ASSETS / name


def snapshot_inputs() -> dict[str, bytes]:
    return {
        name: read_stable_bytes(input_path(name))
        for name in (*INPUT_NAMES, SCRIPT_INPUT_NAME)
    }


def preflight_inputs(
    snapshot: dict[str, bytes],
) -> tuple[list[dict[str, str]], dict[str, object]]:
    if set(snapshot) != {*INPUT_NAMES, SCRIPT_INPUT_NAME}:
        raise ValueError("input snapshot has missing or unexpected fields")
    rows = read_training_rows(snapshot["training_curve_source.csv"])
    status = read_zero_training_status(rows, snapshot["training_status.json"])
    with Image.open(io.BytesIO(snapshot["model_architecture_gpt_source.png"])) as image:
        image.verify()
    return rows, status


def validate_staged_outputs(staging: Path) -> None:
    for name in OUTPUT_NAMES:
        path = staging / name
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"missing or empty staged output: {name}")
        if path.suffix == ".png":
            with Image.open(path) as image:
                image.verify()
        else:
            data = path.read_bytes()
            if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-1024:]:
                raise ValueError(f"invalid staged PDF: {name}")


def build_manifest_core(
    staging: Path,
    snapshot: dict[str, bytes],
    status: dict[str, object],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "READY",
        "as_of": status["as_of"],
        "inputs": {name: sha256_bytes(data) for name, data in snapshot.items()},
        "outputs": {name: sha256(staging / name) for name in OUTPUT_NAMES},
    }


def revalidate_inputs(snapshot: dict[str, bytes]) -> None:
    for name, expected in snapshot.items():
        if read_stable_bytes(input_path(name)) != expected:
            raise ValueError(f"input drifted after snapshot: {name}")
    if read_stable_bytes(LIVE_SCRIPT) != snapshot[SCRIPT_INPUT_NAME]:
        raise ValueError(f"live script drifted from executed snapshot: {SCRIPT_INPUT_NAME}")


def canonical_json(data: dict[str, object]) -> bytes:
    return (json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def write_synced(path: Path, data: bytes, mode: int = 0o644) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.fchmod(descriptor, mode)
    finally:
        os.close(descriptor)


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def fsync_file(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def prepare_generation(
    staging: Path,
    snapshot: dict[str, bytes],
    status: dict[str, object],
) -> tuple[str, dict[str, object]]:
    core = build_manifest_core(staging, snapshot, status)
    generation_id = sha256_bytes(canonical_json(core))
    manifest = {**core, "generation_id": generation_id}
    (staging / "figure_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (staging / "READY").write_text(generation_id + "\n", encoding="utf-8")
    return generation_id, manifest


def verify_generation(path: Path, manifest: dict[str, object]) -> None:
    expected_names = {*OUTPUT_NAMES, "figure_manifest.json", "READY"}
    if not path.is_dir() or {entry.name for entry in path.iterdir()} != expected_names:
        raise ValueError(f"generation has an invalid file set: {path}")
    if any(entry.is_symlink() or not entry.is_file() for entry in path.iterdir()):
        raise ValueError(f"generation contains a non-regular file: {path}")
    observed = json.loads((path / "figure_manifest.json").read_text(encoding="utf-8"))
    if observed != manifest:
        raise ValueError(f"generation manifest mismatch: {path}")
    outputs = manifest["outputs"]
    if not isinstance(outputs, dict):
        raise ValueError("generation outputs must be a mapping")
    for name, expected_hash in outputs.items():
        if type(name) is not str or type(expected_hash) is not str or sha256(path / name) != expected_hash:
            raise ValueError(f"generation output mismatch: {name}")
    generation_id = manifest["generation_id"]
    if (path / "READY").read_text(encoding="utf-8") != f"{generation_id}\n":
        raise ValueError(f"generation READY mismatch: {path}")


def publish_generation(
    staging: Path,
    generation_id: str,
    manifest: dict[str, object],
) -> Path:
    GENERATION_ROOT.mkdir(parents=True, exist_ok=True)
    destination = GENERATION_ROOT / generation_id
    try:
        destination.mkdir(mode=0o700)
    except FileExistsError:
        verify_generation(destination, manifest)
        return destination

    install_names = (*OUTPUT_NAMES, "figure_manifest.json", "READY")
    for name in install_names[:-1]:
        os.link(staging / name, destination / name)
        os.chmod(destination / name, 0o444)
        fsync_file(destination / name)
    os.link(staging / "READY", destination / "READY")
    os.chmod(destination / "READY", 0o444)
    fsync_file(destination / "READY")
    fsync_directory(destination)
    os.chmod(destination, 0o555)
    fsync_directory(GENERATION_ROOT)
    verify_generation(destination, manifest)
    return destination


def publish_current_pointer(generation: Path, manifest: dict[str, object]) -> None:
    pointer = {
        "schema_version": 1,
        "status": "READY",
        "generation_id": manifest["generation_id"],
        "generation_path": generation.relative_to(ASSETS).as_posix(),
        "manifest_sha256": sha256(generation / "figure_manifest.json"),
    }
    descriptor, temporary_name = tempfile.mkstemp(prefix=".figure-current-", dir=ASSETS)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(json.dumps(pointer, indent=2, sort_keys=True).encode("utf-8") + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
            os.fchmod(handle.fileno(), 0o644)
        os.replace(temporary, CURRENT_POINTER)
        fsync_directory(ASSETS)
    finally:
        temporary.unlink(missing_ok=True)


def exec_captured_script() -> None:
    script_bytes = read_stable_bytes(LIVE_SCRIPT)
    snapshot_dir = Path(tempfile.mkdtemp(prefix="hermes-figure-script-"))
    snapshot_script = snapshot_dir / LIVE_SCRIPT.name
    try:
        write_synced(snapshot_script, script_bytes, 0o500)
        environment = os.environ.copy()
        environment.update(
            {
                "CROP_FIGURE_SNAPSHOT_ACTIVE": "1",
                "CROP_FIGURE_LIVE_SCRIPT": str(LIVE_SCRIPT),
                "CROP_FIGURE_ROOT": str(ROOT),
                "CROP_FIGURE_SNAPSHOT_DIR": str(snapshot_dir),
            }
        )
        os.execve(sys.executable, [sys.executable, "-B", str(snapshot_script)], environment)
    except Exception:
        shutil.rmtree(snapshot_dir, ignore_errors=True)
        raise


def main() -> None:
    global OUTPUT_DIR
    ASSETS.mkdir(parents=True, exist_ok=True)
    previous_output_dir = OUTPUT_DIR
    with tempfile.TemporaryDirectory(prefix=".figure-staging-", dir=ASSETS) as temp_dir:
        staging = Path(temp_dir)
        snapshot = snapshot_inputs()
        rows, status = preflight_inputs(snapshot)
        OUTPUT_DIR = staging
        try:
            render_training_progress(rows, status)
            render_python_architecture()
            render_gpt_architecture(snapshot["model_architecture_gpt_source.png"])
        finally:
            OUTPUT_DIR = previous_output_dir
        validate_staged_outputs(staging)
        generation_id, manifest = prepare_generation(staging, snapshot, status)
        revalidate_inputs(snapshot)
        generation = publish_generation(staging, generation_id, manifest)
        publish_current_pointer(generation, manifest)
    print(f"rendered immutable figure generation {generation_id}")


if __name__ == "__main__":
    if not SNAPSHOT_ACTIVE:
        exec_captured_script()
    snapshot_dir = os.environ.get("CROP_FIGURE_SNAPSHOT_DIR")
    if snapshot_dir:
        atexit.register(shutil.rmtree, snapshot_dir, ignore_errors=True)
    main()
