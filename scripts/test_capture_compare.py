from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2

from endfield_essence_recognizer.core.window.windows_utils import (
    _get_client_rect,
    _screenshot_by_hdrcapture,
    _screenshot_by_win32ui,
    get_support_window,
)


def main() -> None:
    output_dir = Path("tests/screenshot/capture")
    output_dir.mkdir(parents=True, exist_ok=True)

    window = get_support_window(["Endfield"])
    if window is None:
        raise RuntimeError("Cannot find window titled 'Endfield'")

    client_rect = _get_client_rect(window)
    legacy_image = _screenshot_by_win32ui(client_rect)
    hdr_image = _screenshot_by_hdrcapture()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    legacy_path = output_dir / f"legacy_gdi_{ts}.png"
    hdr_path = output_dir / f"hdrcapture_{ts}.png"

    ok_legacy = cv2.imwrite(str(legacy_path), legacy_image)
    ok_hdr = cv2.imwrite(str(hdr_path), hdr_image)
    if not ok_legacy or not ok_hdr:
        raise RuntimeError("Failed to write capture comparison images")

    print(f"Saved legacy capture: {legacy_path}")
    print(f"Saved HDR capture:    {hdr_path}")
    print(f"Legacy shape: {legacy_image.shape}")
    print(f"HDR shape:    {hdr_image.shape}")


if __name__ == "__main__":
    main()
