import subprocess
import numpy as np
from PIL import Image
import chess

def main():

    board  = f"boards/green.png"
    pieces = f"pieces/neo"
    size = 100
    mg = MoveGenerator(size, board, pieces)

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-video_size", f"{size*8}x{size*8}",
        "-framerate", "30",
        "-i", "-",
        "-c:v", "libvpx-vp9", "-crf", "35",
        "out.webm"
    ]

    ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    board_img = Image.open(board)
    board_size = size * 8
    board_img = board_img.resize((board_size, board_size), Image.Resampling.LANCZOS)

    generator = mg.move_generator("wq.png", 0, 700)
    for data in generator:
        ffmpeg_process.stdin.write(data)

    ffmpeg_process.stdin.close()
    ffmpeg_process.wait()

class MoveGenerator:

    def __init__(self, square_size, board_file, piece_folder):
        self.square_size = square_size
        self.piece_folder = piece_folder

        board_img = Image.open(board_file)
        board_size = square_size * 8
        board_img = board_img.resize((board_size, board_size), Image.Resampling.LANCZOS)
        if board_img.mode != "RGBA":
            board_img = board_img.convert("RGBA")
        self.board_img = board_img

    def move_generator(self, piece, starting_square, ending_square, frames=30, dutycycle=0.25):

        # open piece image
        piece_img = Image.open(self.piece_folder + "/" + piece)
        piece_img = piece_img.resize((self.square_size, self.square_size), Image.Resampling.LANCZOS)
        if piece_img.mode != "RGBA":
            piece_img = piece_img.convert("RGBA")

        # calculate how the piece will move
        # piece will only move for dutycycle% of the total frames
        movement_frames = int(np.floor(frames * dutycycle))
        pause_frames = frames - movement_frames
        # smoothstep function: https://en.wikipedia.org/wiki/Smoothstep
        smoothstep = np.linspace(0, 1, movement_frames)
        smoothstep = 3*smoothstep**2 - 2*smoothstep**3
        movement_array = starting_square + (ending_square - starting_square) * smoothstep
        # make final movement array
        pause_array = np.full(pause_frames, ending_square)
        final_array = np.concat([movement_array, pause_array])

        for frame in range(frames):
            board_copy = self.board_img.copy()
            board_copy.paste(piece_img, (int(final_array[frame]), 0), piece_img)
            board_copy = board_copy.convert("RGB")
            yield board_copy.tobytes()

if __name__ == "__main__":
    main()
