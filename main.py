import subprocess
from PIL import Image

board  = f"boards/green.png"
pieces = f"pieces/neo"
size = 100

ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-f", "rawvideo",
    "-pix_fmt", "rgb24",
    "-video_size", f"{size*8}x{size*8}",
    "-framerate", "60",
    "-i", "-",
    "-c:v", "libvpx-vp9", "-crf", "35",
    "out.webm"
]

ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

board_img = Image.open(board)
board_size = size * 8
board_img = board_img.resize((board_size, board_size), Image.Resampling.LANCZOS)

if board_img.mode != "RGBA":
    board_img = board_img.convert("RGBA")

queen = pieces + "/wq.png"
queen_img = Image.open(queen)
queen_img = queen_img.resize((size, size), Image.Resampling.LANCZOS)
if queen_img.mode != "RGBA":
    queen_img = queen_img.convert("RGBA")

for x in range(700):
    board_copy = board_img.copy()
    board_copy.paste(queen_img, (x, 0), queen_img)
    board_copy = board_copy.convert("RGB")
    ffmpeg_process.stdin.write(board_copy.tobytes())

ffmpeg_process.stdin.close()
ffmpeg_process.wait()
