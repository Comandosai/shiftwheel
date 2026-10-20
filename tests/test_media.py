"""ShiftWheel: tests for the ffmpeg argument builders and real conversions."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from dragshift import media
from dragshift.util import category

FF = media.find_ffmpeg()
needs_ff = pytest.mark.skipif(FF is None, reason="ffmpeg not installed")


def test_category_media():
    assert category("a.MP4") == "video" and category("b.mov") == "video" and category("c.webm") == "video"
    assert category("a.mp3") == "audio" and category("x.m4a") == "audio" and category("x.wav") == "audio"
    assert category("a.gif") == "image"  # gif stays an image source


def test_targets():
    assert "MP4" not in media.targets_for("video", ".mp4")
    assert set(media.targets_for("video", ".mov")) >= {"MP4", "WEBM", "GIF", "MP3", "M4A", "WAV"}
    assert media.targets_for("audio", ".wav") == ["MP3", "M4A"]
    assert media.targets_for("text", ".txt") == []


def test_convert_args_mp4():
    a = media.build_convert_args("in.mov", "out.mp4", "mp4")
    assert a[a.index("-i") + 1] == "in.mov" and a[-1] == "out.mp4"
    assert a[a.index("-c:v") + 1] == "libx264" and "+faststart" in a and "yuv420p" in a


def test_convert_args_audio_and_webm_gif():
    mp3 = media.build_convert_args("a.wav", "a.mp3", "MP3")
    assert "-vn" in mp3 and "libmp3lame" in mp3
    assert "pcm_s16le" in media.build_convert_args("a.mp3", "a.wav", "WAV")
    w = media.build_convert_args("v.mp4", "v.webm", "WEBM")
    assert "libvpx-vp9" in w and "libopus" in w
    g = media.build_convert_args("v.mp4", "v.gif", "GIF")
    assert "-an" in g and "palettegen" in g[g.index("-filter_complex") + 1]
    with pytest.raises(ValueError):
        media.build_convert_args("a", "b", "XYZ")


def test_compress_extract_trim_concat_args():
    c = media.build_compress_args("v.mov", "o.mp4", "Small")
    assert c[c.index("-crf") + 1] == "32" and "720" in c[c.index("-vf") + 1]
    e = media.build_extract_audio_args("v.mp4", "o.m4a")
    assert "-vn" in e and e[e.index("-c:a") + 1] == "aac"
    t = media.build_trim_args("v.mp4", "o.mp4", 1, 2.5)
    assert t[t.index("-ss") + 1] == "1.000" and t[t.index("-to") + 1] == "2.500"
    with pytest.raises(ValueError):
        media.build_trim_args("v", "o", 3, 1)
    lst = media.build_concat_list(["/tmp/it's.mp4"])
    assert lst == "file '/tmp/it'\\''s.mp4'\n"


def test_missing_ffmpeg(monkeypatch, tmp_path):
    monkeypatch.setattr(media, "_candidates", lambda: [tmp_path / "nope"])
    with pytest.raises(Exception, match="brew install ffmpeg"):
        media.require_ffmpeg()


# ---------------------------------------------------------------- real files
def _probe(p):
    fp = shutil.which("ffprobe") or str(Path(FF).with_name("ffprobe"))
    r = subprocess.run([fp, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(p)],
                       capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


@pytest.fixture(scope="module")
def clip(tmp_path_factory):
    d = tmp_path_factory.mktemp("m")
    v = d / "clip.mp4"
    subprocess.run([FF, "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=321x241:rate=25",
                    "-f", "lavfi", "-i", "sine=frequency=440", "-t", "2", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-vf", "scale=320:240", "-c:a", "aac", "-shortest", str(v)], check=True)
    return v


@needs_ff
@pytest.mark.parametrize("target,codec", [("MOV", "h264"), ("WEBM", "vp9"), ("GIF", "gif"),
                                          ("MP3", "mp3"), ("M4A", "aac"), ("WAV", "pcm_s16le")])
def test_real_video_convert(clip, target, codec):
    out = media.convert(clip, target)[0]
    assert out.suffix == "." + target.lower() and out.stat().st_size > 0
    assert codec in [s["codec_name"] for s in _probe(out)["streams"]]


@needs_ff
def test_real_compress_extract_trim_join(clip):
    c = media.compress(clip, "Small")[0]
    assert c.exists() and "Compressed" in c.name
    a = media.extract_audio(clip)[0]
    assert [s["codec_type"] for s in _probe(a)["streams"]] == ["audio"]
    t = media.trim(clip, 0, 1)[0]
    assert float(_probe(t)["format"]["duration"]) < 1.6
    j = media.concat([str(clip), str(clip)])[0]
    assert float(_probe(j)["format"]["duration"]) > 3.5


@needs_ff
def test_real_audio_convert(tmp_path):
    w = tmp_path / "tone.wav"
    subprocess.run([FF, "-loglevel", "error", "-f", "lavfi", "-i", "sine", "-t", "1", str(w)], check=True)
    for t in ("MP3", "M4A"):
        assert media.convert(w, t)[0].stat().st_size > 0
    assert not list(tmp_path.glob("*.part*"))
