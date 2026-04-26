import subprocess
import numpy as np
from PIL import Image
import chess.pgn

def main():

    board_file  = f"boards/green.png"
    pieces_dir = f"pieces/neo"
    size = 100

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

    with open("game (with time).pgn", "r") as infile:
        game = chess.pgn.read_game(infile)

    mg = MoveGenerator(size, board_file, pieces_dir, game)

    for move in game.mainline_moves():
        
        print(mg.board.san(move))
        generator = mg.generate_moves(mg.board.piece_at(move.from_square), move.from_square, move.to_square)
        for data in generator:
            ffmpeg_process.stdin.write(data)
        mg.board.push(move)

    ffmpeg_process.stdin.close()
    ffmpeg_process.wait()

class MoveGenerator:

    def __init__(self, square_size, board_file, piece_folder, game):
        self.square_size = square_size
        self.game = game
        self.board = game.board()

        board_img = Image.open(board_file)
        board_size = square_size * 8
        board_img = board_img.resize((board_size, board_size), Image.Resampling.LANCZOS)
        if board_img.mode != "RGBA":
            board_img = board_img.convert("RGBA")
        self.board_img = board_img

        # open all the pieces and resize them
        self.pieces = {
            f"w{chess.PAWN}": Image.open(piece_folder + "/wp.png"),
            f"w{chess.KNIGHT}": Image.open(piece_folder + "/wn.png"),
            f"w{chess.BISHOP}": Image.open(piece_folder + "/wb.png"),
            f"w{chess.ROOK}": Image.open(piece_folder + "/wr.png"),
            f"w{chess.QUEEN}": Image.open(piece_folder + "/wq.png"),
            f"w{chess.KING}": Image.open(piece_folder + "/wk.png"),
            f"b{chess.PAWN}": Image.open(piece_folder + "/bp.png"),
            f"b{chess.KNIGHT}": Image.open(piece_folder + "/bn.png"),
            f"b{chess.BISHOP}": Image.open(piece_folder + "/bb.png"),
            f"b{chess.ROOK}": Image.open(piece_folder + "/br.png"),
            f"b{chess.QUEEN}": Image.open(piece_folder + "/bq.png"),
            f"b{chess.KING}": Image.open(piece_folder + "/bk.png")
        }

        for key in self.pieces:
            self.pieces[key] = self.pieces[key].resize((square_size, square_size), Image.Resampling.LANCZOS)
            if self.pieces[key].mode != "RGBA":
                self.pieces[key] = self.pieces[key].convert("RGBA")

    def generate_moves(self, piece, start_square, end_square, frames=30, dutycycle=0.25):

        # convert algebraic notation to board coordinates
        starting_square = self.chess2coords(start_square)
        ending_square = self.chess2coords(end_square)

        # open piece image
        piece_name = "w" if piece.color else "b"
        piece_name += str(piece.piece_type)
        piece_img = self.pieces[piece_name]

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

        # TODO: you don't have to regenerate frames when there's no movement
        board_setup = self.setup_board(exclude_square=start_square)
        for frame in range(frames):
            board_copy = board_setup.copy()
            board_copy.paste(piece_img, (int(final_array_x[frame]), int(final_array_y[frame])), piece_img)
            board_copy = board_copy.convert("RGB")
            yield board_copy.tobytes()

    def setup_board(self, exclude_square=None):

        board_copy = self.board_img.copy()

        for square in chess.SQUARES:
            if square == exclude_square:
                continue

            piece = self.board.piece_at(square)
            if piece is None:
                continue

            piece_name = "w" if piece.color else "b"
            piece_name += str(piece.piece_type)
            piece_img = self.pieces[piece_name]

            x, y = self.chess2coords(square)

            board_copy.paste(piece_img, (x, y), piece_img)
        
        return board_copy

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

    def chess2coords(self, chess_square):

        file = chess.square_file(chess_square)
        rank = chess.square_rank(chess_square)
        return (file * self.square_size, (7-rank) * self.square_size)

if __name__ == "__main__":
    main()
