import os
import logging

logger = logging.getLogger("Linux.Platform")

def get_session_type():
    session = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if session == "wayland":
        return "wayland"
    
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"

    return "x11"

def apply_click_through(window_id):
    session = get_session_type()
    if session == "x11":
        from .x11 import apply_click_through as x11_apply
        x11_apply(window_id)
    else:
        from .wayland import apply_click_through as wayland_apply
        wayland_apply(window_id)

def setup_overlay_window(window_instance):
    session = get_session_type()
    if session == "wayland":
        try:
            from .wayland import setup_window as wayland_setup
            wayland_setup(window_instance)
            return
        except ImportError:
            logger.warning("Wayland setup requested but wayland.py not found falling back to X11 setup")
    
    from .x11 import setup_window
    setup_window(window_instance)
