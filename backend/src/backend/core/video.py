import io
import json
import logging
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 200 * 1024 * 1024
MAX_DURATION_SECONDS = 60
MAX_OUTPUT_BYTES = 30 * 1024 * 1024

_MAX_SHORT_SIDE = 720
_MAX_FPS = 60
_CRF = 23
_AUDIO_KBPS = 128
# Share of the 30MB budget the capped bitrate aims for. The rest absorbs the container, the VBV
# buffer's overshoot and x264 not landing exactly on its target.
_BUDGET_SHARE = 0.9

# Sized for a small host (Render: 512MB RAM, a fraction of a CPU). Measured on 20s of busy
# 1080p60 going to 720p60: preset `medium` on every core peaked at 650MB and took 134 CPU-seconds;
# `veryfast` on 2 threads peaked at 230MB in 69 CPU-seconds, same file size and quality, since the
# 30MB cap rather than the preset is what limits a clip like that.
_THREADS = 2

# One encode at a time: two at once would double the memory and just make both slower, and a
# burst of uploads would starve the API's own threads.
_encoder = ThreadPoolExecutor(max_workers=1, thread_name_prefix="video-encode")


@dataclass
class VideoInfo:
    duration: float | None
    fps: float
    has_audio: bool


@dataclass
class EncodedClip:
    video: bytes
    poster: bytes


def save_upload(file: UploadFile) -> Path:
    """Copies an upload to a temp file ffmpeg can read by path, enforcing `MAX_UPLOAD_BYTES`.
    The caller owns the file from here on (the request's own spooled copy is gone once the
    response is sent, long before the background encode runs)."""
    suffix = Path(file.filename or "").suffix[:10]
    with tempfile.NamedTemporaryFile(prefix="squadup-clip-", suffix=suffix, delete=False) as handle:
        path = Path(handle.name)
    try:
        with path.open("wb") as handle:
            copied = 0
            while chunk := file.file.read(1024 * 1024):
                copied += len(chunk)
                if copied > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        f"Videos can be up to {MAX_UPLOAD_BYTES // (1024 * 1024)}MB.",
                    )
                handle.write(chunk)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def _parse_rate(rate: str | None) -> float:
    try:
        num, _, den = (rate or "0/1").partition("/")
        return float(num) / float(den or 1)
    except (ValueError, ZeroDivisionError):
        return 0.0


def probe(path: Path) -> VideoInfo:
    """Reads what the encode needs to know, and rejects anything ffmpeg can't treat as a video
    (a renamed file, a still image, audio only) before a post row is ever written."""
    unreadable = HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "That file isn't a readable video")
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
            capture_output=True,
            check=True,
            timeout=30,
        )
        data = json.loads(result.stdout)
    except (subprocess.SubprocessError, json.JSONDecodeError) as exc:
        raise unreadable from exc

    # ffprobe reports a still image as a one-frame video stream; its demuxer gives it away.
    format_name = (data.get("format") or {}).get("format_name") or ""
    if format_name == "image2" or format_name.endswith("_pipe"):
        raise unreadable

    streams = data.get("streams") or []
    video = next(
        (s for s in streams if s.get("codec_type") == "video" and not (s.get("disposition") or {}).get("attached_pic")),
        None,
    )
    if not video:
        raise unreadable

    duration = None
    for source in (data.get("format") or {}, video):
        try:
            duration = float(source["duration"])
            break
        except (KeyError, TypeError, ValueError):
            continue
    if duration is not None and duration > MAX_DURATION_SECONDS + 0.5:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Clips can be up to {MAX_DURATION_SECONDS} seconds long.",
        )

    fps = _parse_rate(video.get("avg_frame_rate")) or _parse_rate(video.get("r_frame_rate"))
    has_audio = any(s.get("codec_type") == "audio" for s in streams)
    return VideoInfo(duration=duration, fps=fps, has_audio=has_audio)


def _video_filter(info: VideoInfo) -> str:
    # Shorter side down to 720 (never up), so a vertical phone clip comes out 720 wide rather
    # than 720 tall. ffmpeg has already applied the phone's rotation flag by this point, so
    # iw/ih are the dimensions as displayed. Even sizes, because yuv420p needs them.
    short = _MAX_SHORT_SIDE
    scale = (
        f"scale=w='if(gte(iw,ih),-2,trunc(min({short},iw)/2)*2)'"
        f":h='if(gte(iw,ih),trunc(min({short},ih)/2)*2,-2)'"
    )
    filters = [scale]
    if info.fps > _MAX_FPS + 0.5:
        filters.append(f"fps={_MAX_FPS}")
    # 8-bit 4:2:0 is the only H.264 flavour every browser decodes; 10-bit HDR phone footage
    # would otherwise come out as High 10 and play as a black box.
    filters.append("format=yuv420p")
    return ",".join(filters)


def _encode(src: Path, dest: Path, info: VideoInfo, budget_bytes: int) -> None:
    """Capped CRF: CRF 23 decides the quality, and `-maxrate` only steps in when holding that
    quality would push the file past the budget for this clip's length. Short or simple clips
    come out well under 30MB; long, busy ones get the most bitrate that still fits."""
    duration = min(info.duration or MAX_DURATION_SECONDS, MAX_DURATION_SECONDS)
    audio_kbps = _AUDIO_KBPS if info.has_audio else 0
    video_kbps = max(500, int(budget_bytes * 8 / 1000 / duration) - audio_kbps)

    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-threads", str(_THREADS), "-filter_threads", "1",
        "-i", str(src),
        "-t", str(MAX_DURATION_SECONDS),
        "-map", "0:v:0",
        "-vf", _video_filter(info),
        "-c:v", "libx264", "-preset", "veryfast", "-threads", str(_THREADS), "-profile:v", "high",
        "-crf", str(_CRF), "-maxrate", f"{video_kbps}k", "-bufsize", f"{video_kbps * 2}k",
    ]  # fmt: skip
    if info.has_audio:
        command += ["-map", "0:a:0", "-c:a", "aac", "-b:a", f"{_AUDIO_KBPS}k", "-ac", "2"]
    command += ["-movflags", "+faststart", str(dest)]

    result = subprocess.run(command, capture_output=True, check=False, timeout=20 * 60)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr.decode(errors='replace')[-2000:]}")


def _poster(clip: Path, info: VideoInfo) -> bytes:
    """A WebP still from about a second in (or the middle of a shorter clip) for the player to
    show before it loads, so the feed doesn't fetch any video until someone presses play."""
    seek = min(1.0, (info.duration or 0) / 2)
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-ss", f"{seek:.2f}", "-i", str(clip), "-frames:v", "1", "-f", "image2pipe", "-c:v", "png", "-",
    ]  # fmt: skip
    result = subprocess.run(command, capture_output=True, check=True, timeout=60)
    buffer = io.BytesIO()
    Image.open(io.BytesIO(result.stdout)).convert("RGB").save(buffer, format="WEBP", quality=80)
    return buffer.getvalue()


def encode_clip(src: Path, info: VideoInfo) -> EncodedClip:
    """720p, up to 60fps, H.264/AAC MP4 with `+faststart` (playback starts before the whole file
    arrives), guaranteed at most `MAX_OUTPUT_BYTES`. If the first pass still overshoots, which
    the capped bitrate makes rare, it goes again with a smaller budget."""
    workdir = Path(tempfile.mkdtemp(prefix="squadup-encode-"))
    try:
        output = workdir / "clip.mp4"
        budget = int(MAX_OUTPUT_BYTES * _BUDGET_SHARE)
        for _ in range(3):
            _encode(src, output, info, budget)
            size = output.stat().st_size
            if size <= MAX_OUTPUT_BYTES:
                return EncodedClip(video=output.read_bytes(), poster=_poster(output, info))
            budget = int(budget * MAX_OUTPUT_BYTES / size * 0.9)
        raise RuntimeError(f"Encoded clip is still {size} bytes, over the {MAX_OUTPUT_BYTES} cap")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def submit(job, *args) -> None:
    """Queues `job` on the single encode worker. Errors are logged here as a backstop; the job
    itself is expected to record its own failure on the post."""

    def run() -> None:
        try:
            job(*args)
        except Exception:
            logger.exception("Video job failed")

    _encoder.submit(run)
