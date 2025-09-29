import cv2, os, shlex, subprocess
from typing import Union


def split_video_to_frames(video_path, output_dir, step=30, prefix="frame"):
    """
    Split a video into frames every X frames and save them to a directory.

    Args:
        video_path (str): Path to the input video file (e.g., "video.mp4").
        output_dir (str): Directory to save extracted frames.
        step (int): Save one frame every `step` frames.
        prefix (str): Prefix for saved frame filenames.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video file {video_path}")

    frame_count = 0
    saved_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        if frame_count % step == 0:  # Save every Xth frame
            frame_filename = os.path.join(output_dir, f"{prefix}_{saved_count:05d}.png")
            cv2.imwrite(frame_filename, frame)
            saved_count += 1

        frame_count += 1

    cap.release()


def _to_seconds(ts: Union[str, int, float]) -> float:
    if isinstance(ts, (int, float)):
        return float(ts)
    parts = ts.split(":")
    parts = [float(p) for p in parts]
    parts = parts[::-1]  # seconds, minutes, hours...
    seconds = 0.0
    for i, v in enumerate(parts):
        seconds += v * (60**i)
    return seconds


def trim_video_ffmpeg(
    input_path: str,
    output_path: str,
    start: Union[str, int, float],
    end: Union[str, int, float],
    reencode: bool = False,
) -> None:
    """
    Trim `input_path` between `start` and `end` into `output_path`.

    start, end: "HH:MM:SS" or seconds (int/float).
    reencode: if False the function attempts stream-copy (fast). If stream-copy
              fails for some formats or you need frame-accurate editing, set True
              to re-encode (slower but generally more compatible).
    """
    s = _to_seconds(start)
    e = _to_seconds(end)
    if e <= s:
        raise ValueError("end must be greater than start")

    duration = e - s

    if reencode:
        # Re-encode for maximum accuracy / compatibility
        cmd = (
            f"ffmpeg -y -ss {s:.3f} -i {shlex.quote(input_path)} "
            f"-t {duration:.3f} -c:v libx264 -c:a aac -strict experimental {shlex.quote(output_path)}"
        )
    else:
        # Try stream copy (fast). Note: may only cut on keyframes for some codecs.
        cmd = (
            f"ffmpeg -y -i {shlex.quote(input_path)} -ss {s:.3f} "
            f"-t {duration:.3f} -c copy {shlex.quote(output_path)}"
        )

    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if proc.returncode != 0:
        # If stream-copy failed and we didn't reencode, try again with reencode.
        if not reencode:
            cmd2 = (
                f"ffmpeg -y -ss {s:.3f} -i {shlex.quote(input_path)} "
                f"-t {duration:.3f} -c:v libx264 -c:a aac -strict experimental {shlex.quote(output_path)}"
            )
            proc2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
            if proc2.returncode != 0:
                raise RuntimeError(f"ffmpeg failed:\n{proc.stderr}\n{proc2.stderr}")
            return
        raise RuntimeError(f"ffmpeg failed:\n{proc.stderr}")


if __name__ == "__main__":

    INPUT = "test.mp4"
    OUTPUT = "test1.mp4"

    trim_video_ffmpeg(INPUT, OUTPUT, "00:00", "00:01", reencode=True)
