"""Camera / motion effect library keyed by musical intensity."""

from __future__ import annotations

# intensity bands: calm | mid | hot
EFFECTS: dict[str, dict[str, object]] = {
    # Calm — slow, lyrical
    "slow_drift": {"band": "calm", "zoom_mul": 0.7, "shake": 0.0},
    "breathe_zoom": {"band": "calm", "zoom_mul": 0.85, "shake": 0.0},
    "film_pan_left": {"band": "calm", "zoom_mul": 0.55, "shake": 0.0},
    "film_pan_right": {"band": "calm", "zoom_mul": 0.55, "shake": 0.0},
    "film_pan_up": {"band": "calm", "zoom_mul": 0.5, "shake": 0.0},
    "film_pan_down": {"band": "calm", "zoom_mul": 0.5, "shake": 0.0},
    "zoom_out_soft": {"band": "calm", "zoom_mul": 0.9, "shake": 0.0},
    # Mid — storytelling motion
    "zoom_in": {"band": "mid", "zoom_mul": 1.0, "shake": 0.02},
    "zoom_out": {"band": "mid", "zoom_mul": 1.0, "shake": 0.0},
    "diagonal_in": {"band": "mid", "zoom_mul": 1.05, "shake": 0.03},
    "orbit_drift": {"band": "mid", "zoom_mul": 0.95, "shake": 0.02},
    "pulse_zoom": {"band": "mid", "zoom_mul": 1.1, "shake": 0.04},
    "push_in_pan": {"band": "mid", "zoom_mul": 1.15, "shake": 0.02},
    # Hot — intense / chorus / dense lyrics
    "punch_in": {"band": "hot", "zoom_mul": 1.35, "shake": 0.06},
    "snap_zoom": {"band": "hot", "zoom_mul": 1.45, "shake": 0.08},
    "shake_light": {"band": "hot", "zoom_mul": 1.0, "shake": 0.1},
    "shake_hard": {"band": "hot", "zoom_mul": 1.15, "shake": 0.18},
    "shake_zoom": {"band": "hot", "zoom_mul": 1.25, "shake": 0.14},
    "whip_pan_left": {"band": "hot", "zoom_mul": 0.8, "shake": 0.1},
    "whip_pan_right": {"band": "hot", "zoom_mul": 0.8, "shake": 0.1},
    "crash_zoom": {"band": "hot", "zoom_mul": 1.55, "shake": 0.12},
}

_CALM = [k for k, v in EFFECTS.items() if v["band"] == "calm"]
_MID = [k for k, v in EFFECTS.items() if v["band"] == "mid"]
_HOT = [k for k, v in EFFECTS.items() if v["band"] == "hot"]


def band_for_intensity(intensity: float) -> str:
    """Map 0..1 musical intensity to calm/mid/hot."""
    if intensity < 0.33:
        return "calm"
    if intensity < 0.66:
        return "mid"
    return "hot"


def pick_effect(intensity: float, index: int, role: str = "") -> str:
    """Choose a motion effect; rotate within the intensity band for variety."""
    role_l = (role or "").lower()
    # Role nudges band
    if "chorus" in role_l or "hook" in role_l:
        intensity = min(1.0, intensity + 0.25)
    elif "bridge" in role_l:
        intensity = min(1.0, intensity + 0.1)
    elif "intro" in role_l or "outro" in role_l:
        intensity = max(0.0, intensity - 0.15)

    band = band_for_intensity(intensity)
    pool = {"calm": _CALM, "mid": _MID, "hot": _HOT}[band]
    return pool[index % len(pool)]


def zoompan_filter(
    motion: str,
    zoom: float,
    frames: int,
    width: int,
    height: int,
    intensity: float = 0.5,
) -> str:
    """Build ffmpeg zoompan (+ optional post FX) for one shot."""
    meta = EFFECTS.get(motion, EFFECTS["slow_drift"])
    z_amp = max(0.04, min(0.55, zoom * float(meta["zoom_mul"])))
    z_end = 1.0 + z_amp
    z_inc = z_amp / max(1, frames)
    shake = float(meta["shake"]) * (0.6 + 0.8 * intensity)
    last = max(1, frames - 1)

    # Default centered zoom-in
    z = f"min(1+on*{z_inc:.6f},{z_end:.4f})"
    x = "(iw-iw/zoom)/2"
    y = "(ih-ih/zoom)/2"

    if motion == "slow_drift":
        z = f"min(1+on*{z_inc * 0.55:.6f},{1 + z_amp * 0.75:.4f})"
        x = f"(iw-iw/zoom)*(0.5+0.12*sin(on/28))"
        y = f"(ih-ih/zoom)*(0.5+0.08*cos(on/36))"
    elif motion == "breathe_zoom":
        # gentle in-out pulse
        z = f"1+{z_amp * 0.5:.4f}+{z_amp * 0.5:.4f}*sin(on/{max(8, frames // 3)})"
        x = "(iw-iw/zoom)/2"
        y = "(ih-ih/zoom)/2"
    elif motion == "film_pan_left":
        z = f"min(1+on*{z_inc * 0.35:.6f},{1 + z_amp * 0.45:.4f})"
        x = f"(iw-iw/zoom)*(1-on/{last})"
        y = "(ih-ih/zoom)/2"
    elif motion == "film_pan_right":
        z = f"min(1+on*{z_inc * 0.35:.6f},{1 + z_amp * 0.45:.4f})"
        x = f"(iw-iw/zoom)*(on/{last})"
        y = "(ih-ih/zoom)/2"
    elif motion == "film_pan_up":
        z = f"min(1+on*{z_inc * 0.3:.6f},{1 + z_amp * 0.4:.4f})"
        x = "(iw-iw/zoom)/2"
        y = f"(ih-ih/zoom)*(1-on/{last})"
    elif motion == "film_pan_down":
        z = f"min(1+on*{z_inc * 0.3:.6f},{1 + z_amp * 0.4:.4f})"
        x = "(iw-iw/zoom)/2"
        y = f"(ih-ih/zoom)*(on/{last})"
    elif motion == "zoom_out_soft":
        # start zoomed, pull out
        z = f"max({z_end:.4f}-on*{z_inc:.6f},1.0)"
        x = "(iw-iw/zoom)/2"
        y = "(ih-ih/zoom)/2"
    elif motion == "zoom_in":
        z = f"min(1+on*{z_inc:.6f},{z_end:.4f})"
    elif motion == "zoom_out":
        z = f"max({z_end:.4f}-on*{z_inc:.6f},1.0)"
    elif motion == "diagonal_in":
        z = f"min(1+on*{z_inc * 1.1:.6f},{z_end:.4f})"
        x = f"(iw-iw/zoom)*(on/{last})"
        y = f"(ih-ih/zoom)*(on/{last})"
    elif motion == "orbit_drift":
        z = f"min(1+on*{z_inc * 0.7:.6f},{1 + z_amp * 0.9:.4f})"
        x = f"(iw-iw/zoom)*(0.5+0.22*sin(on/18))"
        y = f"(ih-ih/zoom)*(0.5+0.18*cos(on/22))"
    elif motion == "pulse_zoom":
        z = f"min(1+on*{z_inc * 1.05:.6f},{z_end:.4f})"
        x = f"(iw-iw/zoom)*(0.5+0.06*sin(on/10))"
        y = "(ih-ih/zoom)/2"
    elif motion == "push_in_pan":
        z = f"min(1+on*{z_inc * 1.2:.6f},{z_end:.4f})"
        x = f"(iw-iw/zoom)*(0.3+0.4*on/{last})"
        y = "(ih-ih/zoom)/2"
    elif motion == "punch_in":
        z = f"min(1+on*{z_inc * 1.5:.6f},{z_end:.4f})"
    elif motion == "snap_zoom":
        # fast early zoom then hold-ish
        z = f"min(1+pow(on/{last}\\,0.45)*{z_amp:.4f},{z_end:.4f})"
    elif motion == "crash_zoom":
        z = f"min(1+pow(on/{last}\\,0.35)*{z_amp:.4f},{z_end:.4f})"
        x = f"(iw-iw/zoom)*(0.5+{shake:.3f}*sin(on*1.3))"
        y = f"(ih-ih/zoom)*(0.5+{shake:.3f}*cos(on*1.1))"
    elif motion == "shake_light":
        z = f"min(1+on*{z_inc * 0.6:.6f},{1 + z_amp * 0.7:.4f})"
        x = f"(iw-iw/zoom)*(0.5+{shake:.3f}*sin(on*1.4))"
        y = f"(ih-ih/zoom)*(0.5+{shake:.3f}*cos(on*1.7))"
    elif motion == "shake_hard":
        z = f"min(1+on*{z_inc:.6f},{z_end:.4f})"
        x = f"(iw-iw/zoom)*(0.5+{shake:.3f}*sin(on*2.2)+{shake * 0.5:.3f}*sin(on*5.1))"
        y = f"(ih-ih/zoom)*(0.5+{shake:.3f}*cos(on*1.9)+{shake * 0.5:.3f}*cos(on*4.3))"
    elif motion == "shake_zoom":
        z = f"min(1+on*{z_inc * 1.2:.6f},{z_end:.4f})"
        x = f"(iw-iw/zoom)*(0.5+{shake:.3f}*sin(on*1.6))"
        y = f"(ih-ih/zoom)*(0.5+{shake:.3f}*cos(on*1.8))"
    elif motion == "whip_pan_left":
        z = f"min(1+on*{z_inc * 0.5:.6f},{1 + z_amp * 0.6:.4f})"
        # ease-in whip: accelerate across frame
        x = f"(iw-iw/zoom)*(1-pow(on/{last}\\,1.7))"
        y = f"(ih-ih/zoom)*(0.5+0.04*sin(on))"
    elif motion == "whip_pan_right":
        z = f"min(1+on*{z_inc * 0.5:.6f},{1 + z_amp * 0.6:.4f})"
        x = f"(iw-iw/zoom)*pow(on/{last}\\,1.7)"
        y = f"(ih-ih/zoom)*(0.5+0.04*cos(on))"

    # Apply residual shake on non-shake motions when intensity is high
    if shake > 0 and "shake" not in motion and "whip" not in motion and "crash" not in motion:
        x = f"({x})+((iw-iw/zoom)*{shake:.3f}*sin(on*1.5))"
        y = f"({y})+((ih-ih/zoom)*{shake:.3f}*cos(on*1.3))"

    chain = (
        f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={width}x{height}:fps=30,"
        f"format=yuv420p"
    )

    # Intensity-linked optical FX (subtle)
    if intensity >= 0.66:
        # slight contrast punch + micro vignette feel via eq
        chain += ",eq=contrast=1.08:saturation=1.12:brightness=0.02"
    elif intensity <= 0.33:
        chain += ",eq=contrast=0.96:saturation=0.92"

    return chain
