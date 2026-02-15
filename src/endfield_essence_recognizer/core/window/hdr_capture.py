"""Lifecycle management for hdrcapture window session."""

import atexit
import threading
from typing import Any, Protocol


class CaptureHandle(Protocol):
    def capture(self) -> Any: ...

    def close(self) -> None: ...


try:
    import hdrcapture
except Exception:  # pragma: no cover - optional runtime dependency
    hdrcapture = None


class _HdrCaptureSession:
    def __init__(self) -> None:
        if hdrcapture is None:
            raise RuntimeError("hdrcapture is not available")
        self._owner_thread_id = threading.get_ident()
        self._capture = hdrcapture.capture.window("Endfield.exe", index=0, mode="auto")

    def close(self) -> None:
        if threading.get_ident() != self._owner_thread_id:
            raise RuntimeError(
                "hdrcapture capture must be closed on the thread that created it"
            )
        self._capture.close()

    @property
    def capture(self) -> CaptureHandle:
        return self._capture


_TLS = threading.local()


def _get_session() -> _HdrCaptureSession:
    session = getattr(_TLS, "session", None)
    if session is None:
        session = _HdrCaptureSession()
        _TLS.session = session
    return session


def get_capture() -> CaptureHandle:
    return _get_session().capture


def reset_capture() -> None:
    session = getattr(_TLS, "session", None)
    if session is not None:
        try:
            session.close()
        except BaseException:
            pass
        finally:
            _TLS.session = None


atexit.register(reset_capture)

__all__ = ["get_capture", "reset_capture"]
