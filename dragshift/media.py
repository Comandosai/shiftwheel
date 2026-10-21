"""Video / audio via an external ffmpeg binary (ShiftWheel addition).

ffmpeg is NOT linked into the app: we only run it as a separate process.
Lookup order: %SHIFTWHEEL_FFMPEG%/$SHIFTWHEEL_FFMPEG, a binary bundled with the app
(PyInstaller data dir ffmpeg/ffmpeg[.exe]), Homebrew (macOS) or winget/choco/scoop
(Windows), then PATH.

The argument builders are pure functions (no I/O) so they can be unit-tested
on any OS."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from .util import UserError, sibling

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".aiff", ".aif"}

VIDEO_TARGETS = ["MP4", "MOV", "WEBM", "GIF", "MP3", "M4A", "WAV"]
AUDIO_TARGETS = ["MP3", "M4A", "WAV"]
AUDIO_ONLY = {"MP3", "M4A", "WAV"}

# compression presets: name -> (crf for x264, max height, audio kbps)
COMPRESS_PRESETS = {"High": (23, None, 160), "Medium": (28, 1080, 128), "Small": (32, 720, 96)}


# ---------------------------------------------------------------- locate ffmpeg
IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
EXE = "ffmpeg.exe" if IS_WIN else "ffmpeg"


def _platform_paths(env=os.environ, is_win: bool = IS_WIN) -> list[Path]:
    """Well-known install locations (Homebrew on macOS; winget/choco/scoop on Windows)."""
    if not is_win:
        return [Path("/opt/homebrew/bin/ffmpeg"), Path("/usr/local/bin/ffmpeg")]
    out: list[Path] = []
    la, home = env.get("LOCALAPPDATA"), env.get("USERPROFILE")
    if la:
        out.append(Path(la) / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe")
        out += sorted((Path(la) / "Microsoft" / "WinGet" / "Packages").glob("*FFmpeg*/*/bin/ffmpeg.exe"))
    pd = env.get("ProgramData") or "C:\\ProgramData"
    out.append(Path(pd) / "chocolatey" / "bin" / "ffmpeg.exe")
    if home:
        out.append(Path(home) / "scoop" / "shims" / "ffmpeg.exe")
    pf = env.get("ProgramFiles") or "C:\\Program Files"
    out += [Path(pf) / "ffmpeg" / "bin" / "ffmpeg.exe", Path("C:/ffmpeg/bin/ffmpeg.exe")]
    return out


def _candidates() -> list[Path]:
    c: list[Path] = []
    env = os.environ.get("SHIFTWHEEL_FFMPEG")
    if env:
        c.append(Path(env))
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    c += [base / "ffmpeg" / EXE, base.parent / "Resources" / "ffmpeg" / EXE]
    c += _platform_paths()
    w = shutil.which("ffmpeg")
    if w:
        c.append(Path(w))
    return c


def find_ffmpeg() -> str | None:
    for p in _candidates():
        if p.is_file() and (IS_WIN or os.access(p, os.X_OK)):
            return str(p)
    return None


def install_hint() -> str:
    if IS_WIN:
        return "ffmpeg not found. Install it with:  winget install Gyan.FFmpeg"
    if IS_MAC:
        return "ffmpeg not found. Install it with:  brew install ffmpeg"
    return "ffmpeg not found. Install it with your package manager (e.g. apt install ffmpeg)"


def require_ffmpeg() -> str:
    f = find_ffmpeg()
    if not f:
        raise UserError(install_hint())
    return f


# ---------------------------------------------------------------- pure builders
def media_kind(path: str | Path) -> str | None:
    e = Path(path).suffix.lower()
    return "video" if e in VIDEO_EXTS else "audio" if e in AUDIO_EXTS else None


def targets_for(kind: str, src_ext: str) -> list[str]:
    cur = src_ext.lower().lstrip(".").upper()
    cur = {"M4V": "MP4", "AIF": "AIFF"}.get(cur, cur)
    lst = VIDEO_TARGETS if kind == "video" else AUDIO_TARGETS if kind == "audio" else []
    return [t for t in lst if t != cur]


def _audio_codec(target: str, kbps: int = 192) -> list[str]:
    return {"MP3": ["-c:a", "libmp3lame", "-b:a", f"{kbps}k"],
            "M4A": ["-c:a", "aac", "-b:a", f"{kbps}k"],
            "WAV": ["-c:a", "pcm_s16le"]}[target]


def build_convert_args(src: str, out: str, target: str) -> list[str]:
    """ffmpeg args (without the binary) to convert src -> out in `target` format."""
    t = target.upper()
    a = ["-hide_banner", "-nostdin", "-y", "-i", str(src)]
    if t in AUDIO_ONLY:
        a += ["-vn"] + _audio_codec(t)
    elif t in ("MP4", "MOV"):
        a += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
              "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:a", "aac", "-b:a", "160k"]
        if t == "MP4":
            a += ["-movflags", "+faststart"]
    elif t == "WEBM":
        a += ["-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0", "-row-mt", "1",
              "-c:a", "libopus", "-b:a", "128k"]
    elif t == "GIF":
        a += ["-an", "-filter_complex",
              "fps=12,scale='min(640,iw)':-2:flags=lanczos,split[a][b];"
              "[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
              "-loop", "0"]
    else:
        raise ValueError(f"Unsupported target {target}")
    return a + [str(out)]


def build_compress_args(src: str, out: str, preset: str = "Medium") -> list[str]:
    crf, max_h, abr = COMPRESS_PRESETS[preset]
    a = ["-hide_banner", "-nostdin", "-y", "-i", str(src), "-c:v", "libx264", "-preset", "slow",
         "-crf", str(crf), "-pix_fmt", "yuv420p"]
    vf = f"scale=-2:'min({max_h},ih)'" if max_h else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
    a += ["-vf", vf, "-c:a", "aac", "-b:a", f"{abr}k", "-movflags", "+faststart"]
    return a + [str(out)]


def build_extract_audio_args(src: str, out: str, target: str = "M4A") -> list[str]:
    return ["-hide_banner", "-nostdin", "-y", "-i", str(src), "-vn"] + _audio_codec(target.upper()) + [str(out)]


def build_trim_args(src: str, out: str, start: float, end: float) -> list[str]:
    if end <= start:
        raise ValueError("end must be after start")
    return ["-hide_banner", "-nostdin", "-y", "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", str(src),
            "-c", "copy", str(out)]


def build_concat_list(paths: list[str]) -> str:
    """Contents of an ffmpeg concat-demuxer list file."""
    # forward slashes work for ffmpeg on every OS and avoid backslash-escape issues on Windows
    return "".join("file '" + Path(p).resolve().as_posix().replace("'", "'\\''") + "'\n" for p in paths)


def build_concat_args(list_file: str, out: str) -> list[str]:
    return ["-hide_banner", "-nostdin", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c", "copy", str(out)]


# ---------------------------------------------------------------- runners
def _run(args: list[str], out: Path) -> list[Path]:
    exe = require_ffmpeg()
    tmp = out.with_name(out.stem + ".part" + out.suffix)
    args = args[:-1] + [str(tmp)]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if IS_WIN else 0  # no console flash
    r = subprocess.run([exe, *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       creationflags=flags)
    if r.returncode != 0 or not tmp.exists() or tmp.stat().st_size == 0:
        tmp.unlink(missing_ok=True)
        tail = (r.stderr or "").strip().splitlines()[-3:]
        raise UserError("ffmpeg failed: " + " / ".join(tail))
    os.replace(tmp, out)
    return [out]


def convert(src: str | Path, target: str) -> list[Path]:
    out = sibling(src, ext="." + target.lower())
    return _run(build_convert_args(str(src), str(out), target), out)


def compress(src: str | Path, preset: str = "Medium") -> list[Path]:
    out = sibling(src, "Compressed", ext=".mp4")
    return _run(build_compress_args(str(src), str(out), preset), out)


def extract_audio(src: str | Path, target: str = "M4A") -> list[Path]:
    out = sibling(src, "Audio", ext="." + target.lower())
    return _run(build_extract_audio_args(str(src), str(out), target), out)


def trim(src: str | Path, start: float, end: float) -> list[Path]:
    out = sibling(src, "Trimmed")
    return _run(build_trim_args(str(src), str(out), start, end), out)


def concat(paths: list[str]) -> list[Path]:
    """Join files with identical codecs (stream copy)."""
    if len(paths) < 2:
        raise UserError("Select at least two files to join")
    out = sibling(paths[0], "Joined")
    lst = out.with_suffix(".txt.tmp")
    lst.write_text(build_concat_list(paths), encoding="utf-8")
    try:
        return _run(build_concat_args(str(lst), str(out)), out)
    finally:
        lst.unlink(missing_ok=True)
