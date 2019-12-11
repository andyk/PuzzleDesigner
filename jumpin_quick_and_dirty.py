# Imperative implementation of the puzzle game called Jump In(TM) -- https://www.smartgames.eu/uk/one-player-games/jumpin.
# Authors: Rob C and Andy K
# We had tried a recursive solution but it was a bit harder to debug
# --
# To run, execute the following at the command line: python jumpin_quick_and_dirty.py

import random
from collections import deque
from enum import Enum
from copy import copy, deepcopy
from functools import reduce
import numpy as np

import logging
#logging.basicConfig(level=logging.INFO)

class Direction(Enum):
    R, D, L, U = 0, 1, 2, 3

    def on_same_axis(self, other_direction):
        return self.value % 2 == other_direction.value % 2

    def opposite(self):
        return Direction((self.value + 2) % len(Direction))

def test_direction_on_same_axis():
    assert Direction.R.on_same_axis(Direction.L) and Direction.L.on_same_axis(Direction.R)
    assert not Direction.R.on_same_axis(Direction.U) and not Direction.R.on_same_axis(Direction.D)
    assert not Direction.L.on_same_axis(Direction.U) and not Direction.L.on_same_axis(Direction.D)
    assert Direction.U.on_same_axis(Direction.D) and Direction.D.on_same_axis(Direction.U)
    assert not Direction.U.on_same_axis(Direction.R) and not Direction.U.on_same_axis(Direction.L)
    assert not Direction.D.on_same_axis(Direction.R) and not Direction.D.on_same_axis(Direction.L)

def test_direction_opposite():
    assert Direction.R.opposite() == Direction.L and Direction.L.opposite() == Direction.R
    assert Direction.D.opposite() == Direction.U and Direction.U.opposite() == Direction.D

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @classmethod
    def from_tuple(cls, t):
        return cls(t[0], t[1])

    # Probably not the most efficient, but lets us use this as a key in a dict.
    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __str__(self):
        return "Position({},{})".format(self.x, self.y)

    def as_tuple(self):
        return self.x, self.y

    # num_spots is how many spots shifted the returned position should be relative to this position.
    def get_relative_position(self, direction, num_spots=1):
        assert isinstance(direction, Direction), "`direction` param must be type Direction"
        new_position = copy(self)
        if direction is Direction.R:
            new_position.x = self.x + num_spots
        elif direction is Direction.D:
            new_position.y = self.y + num_spots
        elif direction is Direction.L:
            new_position.x = self.x - num_spots
        elif direction is Direction.U:
            new_position.y = self.y - num_spots
        return new_position


def test_position_get_relative_position():
    assert Position(1, 1).get_relative_position(Direction.R, 2) == Position(3,1)


class Piece:
    # head is the Position of the head. The piece may cover more than one square, but the
    #      position of the head is special. Use `all_positions()` to access all positions
    #      covered by the piece.
    # orientation is the direction that the parts of the piece cover relative to (self.x,self.y),
    #             i.e., the piece's head is at (self.x, self.y), the body/tail extend out from the
    #             head in the direction of `orientation`.
    def __init__(self, id, x, y, width=1, orientation=Direction.R):
        self.id = id
        self.head = Position(x, y)
        self.width = width
        self.orientation = orientation

    @property
    def x(self):
        return self.head.x

    @property
    def y(self):
        return self.head.y

    @property
    def all_positions(self):
        if self.width == 1:
            return [self.head]
        else:
            return [self.head.get_relative_position(self.orientation, i) for i in range(self.width)]

    # Moves a piece and returns the new position of the moved piece.
    def move(self, direction, num_spots):
        self.head = self.head.get_relative_position(direction, num_spots)
        return self.head

    # get's a position relative to the head of this piece.
    def get_relative_position(self, direction, num_spots=1):
        return self.head.get_relative_position(direction, num_spots)

    def __repr__(self):
        return self.id


def test_piece_move():
    rand_x, rand_y, rand_num_spots = np.random.randint(100), np.random.randint(100), np.random.randint(100)
    p = Piece("test_piece", rand_x, rand_y)
    p.move(Direction.R, rand_num_spots)
    assert p.x == (rand_x + rand_num_spots)
    assert p.y == rand_y
    p.move(Direction.D, rand_num_spots)
    assert p.x == rand_x + rand_num_spots
    assert p.y == rand_y + rand_num_spots

class Mushroom(Piece):
    def __init__(self, id, x, y):
        super().__init__(id, x, y)


class Bunny(Piece):
    def __init__(self, id, x, y):
        super().__init__(id, x, y)


# `pos` is the position of the fox's head.
class Fox(Piece):
    def __init__(self, id, x, y, orientation):
        super().__init__(id, x, y, 2, orientation)


# A BoardState only tracks the pieces that are on a board. It does not track the size of the board.
class BoardState:
    def __init__(self, size, mushrooms, bunnies, foxes):
        self.size = size
        pieces = set()
        # make sure all elements are Pieces and that their positions on the board don't overlap.
        positions_seen = set()
        for i in mushrooms + bunnies + foxes:
            assert isinstance(i, Piece)
            if i.id in pieces:
                raise Exception("All pieces must have unique ids.")
            if positions_seen.intersection(i.all_positions):
                raise Exception("All pieces must have unique positions.")
            else:
                [positions_seen.add(p) for p in i.all_positions]
        if mushrooms:
            assert reduce(lambda x, y: x * y, [isinstance(m, Mushroom) for m in mushrooms])
        if bunnies:
            assert reduce(lambda x, y: x * y, [isinstance(b, Bunny) for b in bunnies])
        if foxes:
            assert reduce(lambda x, y: x * y, [isinstance(f, Fox) for f in foxes])
        self.mushrooms = mushrooms
        self.bunnies = bunnies
        self.foxes = foxes

    def __hash__(self):
        return hash(tuple([(p.id, p.x, p.y) for p in self.mushrooms + self.bunnies + self.foxes]))

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    # A dict of all the pieces on the board with key = piece.id
    @property
    def pieces_dict(self):
        return dict([(i.id, i) for i in self.mushrooms + self.bunnies + self.foxes])

    @property
    def movable_pieces(self):
        return self.bunnies + self.foxes

    # this class can be directly treated as an iterator.
    def __iter__(self):
        return iter(self.mushrooms + self.bunnies + self.foxes)

    # Attempt to move a piece. If the move was successful, then return the new state with the piece in the
    # new position. Else, return None.
    def attempt_move(self, piece_id, direction):
        new_state = deepcopy(self)
        new_piece = new_state.pieces_dict[piece_id]  # the equivalent piece in the new_state
        if isinstance(new_piece, Bunny):
            # check to be sure that the Bunny's immediate neighbor is occupied
            neighbor_pos = new_piece.get_relative_position(direction)
            if not (new_state.is_on_board(neighbor_pos) and new_state.is_occupied(neighbor_pos)):
                return None

            # keep calling change_position till reach an empty space or the edge
            num_hops = 0
            while True:
                num_hops += 1
                target_position = new_piece.get_relative_position(direction, num_hops)
                if not new_state.is_on_board(target_position):
                    return None
                if not new_state.is_occupied(target_position):
                    # move the bunny to the new position
                    new_piece.head = target_position
                    break
        else:  # Fox case
            if not new_piece.orientation.on_same_axis(direction):
                return None

            for pos in new_piece.all_positions:
                p = pos.get_relative_position(direction)
                if new_state.is_occupied(p, ignore_piece_with_id=new_piece.id):
                    return None
                if not new_state.is_on_board(p):
                    return None
            # move the fox one step in `direction`
            new_piece.head = new_piece.get_relative_position(direction)
        logging.debug("returning from attempt_move(%s, %s)" % (piece, direction))
        logging.debug("old state:\n" + str(curr_state))
        logging.debug("new (changed) state:\n" + str(new_state))
        return new_state

    # return a list of all empty positions from current board state.
    def empty_positions(self):
        avail_pos = set()
        for x in range(self.size):
            for y in range(self.size):
                avail_pos.add(Position(x, y))
        for piece in self:
            assert piece.x < self.size and piece.y < self.size
            for pos in piece.all_positions:
                avail_pos.remove(pos)
        return list(avail_pos)

    def random_empty_positions(self, num=1):
        r = self.empty_positions()
        random.shuffle(r)
        return r[:num]

    # Return a list of up to `num` unique lists, each of which contain consecutive positions of
    # length `width`, or return an empty list if none are found. If fewer than `num` are found,
    # return all that are found.
    def consecutive_random_empty_positions(self, num, width=2):
        assert 0 < width <= self.size
        empty_positions = set(self.empty_positions())
        all_found = []
        for x in range(self.size):
            for y in range(self.size):
                # from curr pos (x,y): first try looking down the col, then try looking right across the row
                for row_search in [True, False]:
                    new_found = []
                    for k in range(width):  # look at every position in this potential consecutive set of them
                        curr_pos = Position(x + (k * row_search), y + (k * (not row_search)))
                        if not self.is_on_board(curr_pos) or curr_pos not in empty_positions:  # this slot is not a candidate
                            new_found = []
                            break
                        new_found.append(curr_pos)
                    if new_found:
                        all_found.append(new_found)
                    # since we are adding this set if positions to our list of successes, we need to remove them
                    # from the set of empty_positions so that we don't return any position more than once.
                    for n in new_found:
                        empty_positions.remove(n)
                    if len(all_found) == num:
                        return all_found
        return all_found

    def is_occupied(self, pos, ignore_piece_with_id=None):
        for piece in self:
            if piece.id != ignore_piece_with_id and pos in piece.all_positions:
                return True
        return False

    def is_on_board(self, pos):
        return 0 <= pos.x < self.size and 0 <= pos.y < self.size

    def solved(self):
        solved = True
        for bunny in self.bunnies:
            solved = solved and (bunny.x, bunny.y) in [(0, 0), (0, 4), (2, 2), (4, 0), (4, 4)]
        return solved

    def pretty_print(self):
        print(self)

    def __str__(self):
        text = ""
        for y in range(self.size):
            for x in range(self.size):
                piece_found = False
                for piece in self:
                    for position in piece.all_positions:
                        if position.x == x and position.y == y:
                            text += piece.id + " "
                            piece_found = True
                if not piece_found:
                    text += "o  "
            text += "\n"
        return text


def test_boardstate_init():
    # some simple sanity checks of constructor
    test_mush = Mushroom("mush_id", 1, 2)
    assert BoardState(5, [test_mush], [], []).pieces_dict["mush_id"] == test_mush
    b = BoardState(5, [Mushroom("m0", 0, 0)], [Bunny("b0", 0, 1)], [Fox("f0", 0, 2, Direction.R)])
    assert "m0" in b.pieces_dict.keys()
    b.mushrooms.append(test_mush)
    assert test_mush in b.mushrooms

def test_boardstate_empty_positions():
    b = BoardState(1, [], [], [])
    assert b.empty_positions() == [Position(0, 0)]

def test_boardstate_random_empty_positions():
    b = BoardState(5, [Mushroom("m0", 0, 0)], [], [])
    rand_positions = b.random_empty_positions(24)
    assert len(rand_positions) == 24
    assert Position(0, 0) not in rand_positions

def test_boardstate_consecutive_random_empty_positions():
    b = BoardState(2, [], [], [Fox("f0", 0, 0, Direction.D)])
    slots = b.consecutive_random_empty_positions(1)
    assert len(slots) == 1
    assert len(slots[0]) == 2
    assert isinstance(slots[0][0], Position)
    print(slots[0][0], slots[0][1])
    assert Position(1, 0) in slots[0] and Position(1, 1) in slots[0]


class BoardEnv:
    def __init__(self, size=5, num_mushrooms=3, num_bunnies=3, num_foxes=2):
        state = BoardState(size, [], [], [])
        for n, pos in enumerate(state.random_empty_positions(num_mushrooms)):
            state.mushrooms.append(Mushroom("m{}".format(n), pos.x, pos.y))
        for n, pos in enumerate(state.random_empty_positions(num_bunnies)):
            state.bunnies.append(Bunny("b{}".format(n), pos.x, pos.y))
        for n, positions in enumerate(state.consecutive_random_empty_positions(num=num_foxes)):
            assert len(positions) > 0, "state.consecutive_random_empty_positions(num={})) returned empty".format(num_foxes)
            orientation = Direction(np.random.randint(len(Direction)))
            state.foxes.append(Fox("f{}".format(n), positions[0].x, positions[0].y, orientation))
        self.state = state
        self.init_state = state

    @classmethod
    def from_init_state(cls, initial_state):
        assert isinstance(initial_state, BoardState)
        board = cls()
        board.state = initial_state
        board.init_state = initial_state
        return board

    def reset(self):
        self.state = self.init_state
        return self.state

    # returns a new state_observation or None if the move was invalid.
    def step(self, action):
        piece_id, direction = action
        assert not isinstance(self.state.pieces_dict[piece_id], Mushroom)
        new_state = self.state.attempt_move(piece_id, direction)
        done = False
        if new_state:
            self.state = new_state
            done = self.state.solved()
            reward = 100 if done else -1
        else:
            reward = -10
        return self.state, reward, done, None


init_state = BoardState(size=5,
                        mushrooms=[Mushroom("m0", 3, 0), Mushroom("m1", 2, 2), Mushroom("m2", 4, 4)],
                        bunnies=[Bunny("b0", 3, 1), Bunny("b1", 4, 2), Bunny("b2", 0, 3)],
                        foxes=[Fox("f0", 0, 1, Direction.R), Fox("f1", 2, 3, Direction.R)])

#init_state = BoardState(size=5,
#                        mushrooms=[Mushroom("m0", 3, 0), Mushroom("m1", 2, 2), Mushroom("m2", 4, 4)],
#                        bunnies=[Bunny("b0", 2, 0), Bunny("b1", 0, 2), Bunny("b2", 0, 3)],
#                        foxes=[Fox("f0", 0, 1, Direction.R), Fox("f1", 2, 3, Direction.R)])
print("init state:")
print(init_state)

if __name__ == '__main__':
    # false => DFS search implementation, which runs about 3 times faster (2s vs 6s)
    # but finds a solution path that is 200 times longer (12915 vs 63)
    bfs = False
    visited = {}
    visited_move_to_state = {}

    stack = deque([(init_state, None)])
    last_move = None
    i = 0
    while stack:
        if i % 100 == 0:
            print("stack loop iter num %s" % i)
        i += 1
        if bfs:
            curr_state, last_move = stack.popleft()
        else:
            curr_state, last_move = stack.pop()
        assert curr_state
        logging.debug("in loop handling curr_state:\n" + str(curr_state))

        if curr_state.solved():
            print("solution found! Final board state:")
            print(curr_state)
            print("last move was: {}".format(last_move))
            break

        if curr_state in visited.keys():
            logging.debug("curr_state already visited")
            logging.debug(curr_state)
            continue
        # keep track of what move took us to this state
        visited[curr_state] = last_move

        # piece_id will be an index 0-4
        for piece in curr_state.movable_pieces:
            for direction in Direction:
                logging.debug("trying to move %s %s" % (piece, direction))
                next_state = curr_state.attempt_move(piece.id, direction)
                if next_state:
                    stack.append((next_state, (piece.id, direction)))

    # a deterministic policy that maps from state to an action the agent should take
    agent_policy = {}
    solution_path_depth = 0
    while last_move:
        solution_path_depth += 1
        prev_state = curr_state.attempt_move(last_move[0], last_move[1].opposite())
        agent_policy[prev_state] = last_move
        print("saving mapping to policy. This state...")
        print(prev_state)
        print("... should result in this move: (%s %s)\n--\n" % (last_move[0], last_move[1]))
        last_move = visited[prev_state]
        curr_state = prev_state
        if last_move:
            print(curr_state)
            print("{} moved {}".format(last_move[0], last_move[1]))
        if not last_move:
            #print("...{} states not shown...\n".format(solution_path_depth-2))
            print("initial state:")
            init_state.pretty_print()
    print("solution path length: {}".format(solution_path_depth))

    # Now perform a rollout using the policy we just figured out to solve the puzzle.
    # board = BoardEnv()  # use default params to generate a random board. Not sure if it will
    #                     # be solvable or not.
    env = BoardEnv.from_init_state(init_state)
    obs = env.reset()
    print("initial obs from env is:")
    print(obs)
    # keep track of board states and the moves (i.e. actions) that took us to them.
    print("\n==================\n")
    print("OUTPUT FROM FOLLOWING DETERMINISTIC POLICY:")
    for k, v in agent_policy.items():
        print(k, v)
        print()
    total_reward = 0
    while True:
        action = agent_policy[obs]
        print("taking action %s, %s" % (action[0], action[1]))
        obs, reward, done, _ = env.step(action)
        total_reward += reward
        if done:
            break
    print("finished episode with total_reward %s" % total_reward)
