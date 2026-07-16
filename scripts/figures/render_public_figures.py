#!/usr/bin/env python3
"""Render the public training-status and candidate-architecture figures."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "assets"

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


def read_training_rows() -> list[dict[str, str]]:
    source = ASSETS / "training_curve_source.csv"
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        expected = ["run_id", "step", "split", "metric", "value", "checkpoint_selected"]
        if reader.fieldnames != expected:
            raise ValueError(f"training source columns must be {expected}")
        return list(reader)


def save_figure(fig: plt.Figure, stem: str) -> None:
    fig.savefig(ASSETS / f"{stem}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(ASSETS / f"{stem}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def render_training_progress() -> None:
    rows = read_training_rows()
    status = json.loads((ASSETS / "training_status.json").read_text(encoding="utf-8"))
    if len(rows) != status["training_curve_rows"]:
        raise ValueError("training source row count does not match training_status.json")

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
        "0 runs  •  0 optimizer updates  •  0 GPU hours  •  0 checkpoints",
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
        "Stage 0 governance: COMPLETE  |  Stage 1 governance: authorized  |  Stage 2, formal test, GPU and large downloads: not authorized.\n"
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
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=fontsize, color=NAVY, weight=weight)


def arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], *, color: str = "#374151") -> None:
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
    ax.text(8, 9.12, "Candidate architecture — not frozen", ha="center", va="center", fontsize=16, weight="bold", color=NAVY)
    ax.text(1.25, 8.62, "Candidate inputs", ha="center", fontsize=9, weight="bold", color=NAVY)
    ax.text(4.0, 8.62, "Modality-specific\ntokenizers & encoders", ha="center", fontsize=9, weight="bold", color=NAVY)

    inputs = [
        ("Genome & variants", LIGHT_PURPLE, PURPLE),
        ("Transcriptome", LIGHT_BLUE, BLUE),
        ("Regulatory / epigenome", LIGHT_GREEN, GREEN),
        ("Proteome / metabolome", LIGHT_ORANGE, ORANGE),
        ("Environment & experiment", "#EAF8F7", TEAL),
    ]
    y_values = [7.55, 6.38, 5.21, 4.04, 2.87]
    for (label, face, edge), y in zip(inputs, y_values, strict=True):
        box(ax, 0.25, y, 2.05, 0.72, label, face=face, edge=edge, weight="bold")
        encoder = label.replace(" & ", " / ") + "\ntokenizer / encoder"
        box(ax, 2.85, y, 2.35, 0.72, encoder, face=face, edge=edge, fontsize=7.0)
        arrow(ax, (2.31, y + 0.36), (2.83, y + 0.36))
        arrow(ax, (5.21, y + 0.36), (5.67, y + 0.36))

    box(ax, 5.7, 2.45, 2.65, 5.82, "", face="#F5F9FD", edge=NAVY)
    ax.text(7.025, 7.85, "Condition-aware\nhierarchical fusion", ha="center", va="center", fontsize=11, weight="bold", color=NAVY)
    box(ax, 6.0, 6.62, 2.05, 0.62, "Cross-modal alignment", face=LIGHT_BLUE, edge=BLUE, fontsize=7.2)
    box(ax, 6.0, 5.65, 2.05, 0.62, "Missing-modality gating", face=LIGHT_PURPLE, edge=PURPLE, fontsize=7.2)
    box(ax, 6.0, 4.36, 2.05, 0.92, "Biological hierarchy\ngene → sample → tissue\n→ environment", face=LIGHT_GREEN, edge=GREEN, fontsize=7.0)
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
        ("Strict evaluation firewall", 0.85),
        ("Frozen splits", 4.45),
        ("External test seal", 8.05),
        ("Leakage audit", 11.65),
    ]
    for label, x in governance:
        box(ax, x, 0.72, 2.45, 0.64, label, face="white", edge=RED, fontsize=7.6, weight="bold")
    for start, end in [(3.31, 4.43), (6.91, 8.03), (10.51, 11.63)]:
        arrow(ax, (start, 1.04), (end, 1.04), color=RED)
    ax.text(8, 0.16, "Evaluation artifacts are isolated from all training and model-selection inputs.", ha="center", fontsize=7.2, color=RED)

    save_figure(fig, "model_architecture_python")


def export_gpt_pdf() -> None:
    source = ASSETS / "model_architecture_gpt.png"
    with Image.open(source) as image:
        image.convert("RGB").save(ASSETS / "model_architecture_gpt.pdf", "PDF", resolution=300.0)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    render_training_progress()
    render_python_architecture()
    export_gpt_pdf()
    print("rendered training_progress, model_architecture_python, and model_architecture_gpt PDF")


if __name__ == "__main__":
    main()
