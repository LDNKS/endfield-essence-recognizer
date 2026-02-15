from __future__ import annotations

import argparse
import json
import statistics
import time
from datetime import datetime
from pathlib import Path

from endfield_essence_recognizer.core.window.hdr_capture import reset_capture
from endfield_essence_recognizer.core.window.windows_utils import (
    _get_client_rect,
    _screenshot_by_hdrcapture,
    _screenshot_by_win32ui,
    get_support_window,
)


def _measure_ms(func, iterations: int) -> list[float]:
    values: list[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        _ = func()
        values.append((time.perf_counter() - t0) * 1000.0)
    return values


def _summary(samples: list[float]) -> dict[str, float]:
    samples_sorted = sorted(samples)
    p50 = samples_sorted[int((len(samples_sorted) - 1) * 0.50)]
    p95 = samples_sorted[int((len(samples_sorted) - 1) * 0.95)]
    return {
        "count": float(len(samples)),
        "mean_ms": statistics.fmean(samples),
        "min_ms": min(samples),
        "p50_ms": p50,
        "p95_ms": p95,
        "max_ms": max(samples),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark legacy GDI vs hdrcapture screenshot performance"
    )
    parser.add_argument("--title", default="Endfield", help="window title to match")
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--iterations", type=int, default=40)
    args = parser.parse_args()

    output_dir = Path("tests/screenshot/capture")
    output_dir.mkdir(parents=True, exist_ok=True)

    window = get_support_window([args.title])
    if window is None:
        raise RuntimeError(f"Cannot find window titled '{args.title}'")

    client_rect = _get_client_rect(window)

    # Warmup legacy path
    for _ in range(args.warmup):
        _ = _screenshot_by_win32ui(client_rect)

    reset_capture()

    # Measure first shot separately for HDR path (includes session creation)
    t0 = time.perf_counter()
    hdr_first = _screenshot_by_hdrcapture()
    hdr_first_ms = (time.perf_counter() - t0) * 1000.0

    # Warmup remaining HDR captures
    for _ in range(max(args.warmup - 1, 0)):
        _ = _screenshot_by_hdrcapture()

    legacy_samples = _measure_ms(
        lambda: _screenshot_by_win32ui(client_rect), args.iterations
    )
    hdr_samples = _measure_ms(_screenshot_by_hdrcapture, args.iterations)

    legacy_img = _screenshot_by_win32ui(client_rect)
    hdr_img = hdr_first

    result = {
        "window_title": args.title,
        "resolution": {
            "legacy": [legacy_img.shape[1], legacy_img.shape[0]],
            "hdr": [hdr_img.shape[1], hdr_img.shape[0]],
        },
        "warmup": args.warmup,
        "iterations": args.iterations,
        "legacy_gdi": _summary(legacy_samples),
        "hdr_capture_first_shot_ms": hdr_first_ms,
        "hdr_capture_steady": _summary(hdr_samples),
    }

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = output_dir / f"capture_benchmark_{ts}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"Saved benchmark report: {out}")


if __name__ == "__main__":
    main()
