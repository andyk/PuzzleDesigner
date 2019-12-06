from main import PhysicalThing

class JumpinGameBoard(PhysicalThing):
    def __init__(self, height, width, success_state):
        PhysicalThing.__init__(self, "A jump'In Game Board")
        self.height = height
        self.width = width
        # success state and curr_state are both dict of (X,Y) -> piece
        self.success_state = success_state
        self.curr_state = {}

    def step(self, piece, new_location):
        # Mushrooms cannot move
        # Foxes can only slide across consecutive adjacent slots along their axis
        if self.is_legal_move(piece, new_location):
            reward = -1
            piece.move(new_location)
        if self.success_state == self:
            reward = 100
        return (self.pieces, reward, , None)


class JumpinPiece(PhysicalThing):
    """A piece has X,Y coordinates representing their position on the board"""
    def __init__(self, game_board, legal_moves, x, y):
        PhysicalThing.__init__(self, "A jump'In Game Piece")
        game_board.pieces[(x,y)] = self
        self.game_board = game_board
        self.x = x
        self.y = y

    def move(self, dir, num_spaces):
        assert dir == 'U' or dir == 'D' or dir == 'L' or dir == 'R'
        if self.x ==


class Bunny(JumpinPiece):
    def __init__(self, game_board, x, y):
        JumpinPiece.__init__(self, game_board, "BUNNY")

class Fox(JumpinPiece):
    def __init__(self, game_board, x, y):
        JumpinPiece.__init__(self, game_board, "FOX")
    def move(self, dir, num_spaces):


class Mushroom(JumpinPiece):
    def __init__(self, game_board, x, y):
        JumpinPiece.__init__(self, game_board, "MUSHROOM")
    # Mushrooms cannot move
    def move(self, dir, num_spaces):
        return (self.x, self.y)