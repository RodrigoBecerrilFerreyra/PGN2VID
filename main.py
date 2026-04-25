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

    generator = mg.move_generator("wn.png", "g1", "f3")
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

    def move_generator(self, piece, start_square, end_square, frames=30, dutycycle=0.25):

        # convert algebraic notation to board coordinates
        starting_square = self.alg2coords(start_square)
        ending_square = self.alg2coords(end_square)

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
        movement_array_x = starting_square[0] + (ending_square[0] - starting_square[0]) * smoothstep
        movement_array_y = starting_square[1] + (ending_square[1] - starting_square[1]) * smoothstep

        # make final movement array
        pause_array_x = np.full(pause_frames, ending_square[0])
        pause_array_y = np.full(pause_frames, ending_square[1])
        final_array_x = np.concat([movement_array_x, pause_array_x])
        final_array_y = np.concat([movement_array_y, pause_array_y])

        for frame in range(frames):
            board_copy = self.board_img.copy()
            board_copy.paste(piece_img, (int(final_array_x[frame]), int(final_array_y[frame])), piece_img)
            board_copy = board_copy.convert("RGB")
            yield board_copy.tobytes()

    def alg2coords(self, board_coords):

        if len(board_coords) != 2:
            raise ValueError(f"Expected coordinate of length 2, got {len(board_coords)}.")

        file = board_coords[0]
        rank = int(board_coords[1])
        if rank < 1 or rank > 8:
            raise ValueError(f"Rank {rank} out of range.")

        board_coords = board_coords.lower()
        file_map = {
            "a": 0,
            "b": 1,
            "c": 2,
            "d": 3,
            "e": 4,
            "f": 5,
            "g": 6,
            "h": 7
        }

        return (file_map[file]*self.square_size, (8-rank)*self.square_size)

if __name__ == "__main__":
    main()
