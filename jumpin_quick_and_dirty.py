# Imperative implementation of the puzzle game called Jumpin'In(TM).
# Authors: Rob C and Andy K
# We had tried a recursive solution but it was a bit harder to debug
# --
# To run, execute the following at the command line: python jumpin_quick_and_dirty.py

from collections import deque

# make this false for the DFS search implementation, which runs about 3 times faster (2s vs 6s)
# but finds a solution path that is 200 times longer (12915 vs 63)
bfs = True

# mushroom0, mushroom1, mushroom2
static_state = [[3, 0], [2, 2], [4, 4]]
# piece_id: 0=bunny0, 1=bunny1, 2=bunny2, 3=fox0, 4=fox1
initial_moveable_state = [[3, 1], [4, 2], [0, 3], [0, 1, 0], [2, 3, 0]]
# board is square
board_size = 5

# a list of 5 integer pairs
visited = {}


def change_position(position, direction):
    new_position = position.copy()
    if direction is 0:
        new_position[0] = position[0] + 1
    elif direction is 1:
        new_position[1] = position[1] + 1
    elif direction is 2:
        new_position[0] = position[0] - 1
    elif direction is 3:
        new_position[1] = position[1] - 1
    return new_position


def is_occupied(state, pos):
    x = pos[0]
    y = pos[1]
    for piece in static_state + state:
        if x == piece[0] and y == piece[1]:
            return True
        if len(piece) == 3:
            if piece[2] == 0 and x == piece[0] + 1 and y == piece[1]:
                return True
            elif piece[2] == 1 and x == piece[0] and y == piece[1] + 1:
                return True
    return False


def is_on_board(pos):
    return pos[0] >= 0 and pos[0] < board_size and \
           pos[1] >= 0 and pos[1] < board_size


# returns a new state or None if the move was invalid
def transform_state(curr_state, piece_id, direction):
    new_state = curr_state.copy()
    if piece_id < 3:
        # Bunny case
        # check that the immediate neighbor is occupied
        neighbor_position = change_position(curr_state[piece_id], direction)
        if not (is_on_board(neighbor_position) and \
                is_occupied(curr_state, neighbor_position)):
            return None

        # keep calling change_position till reach an empty space or the edge
        while True:
            neighbor_position = change_position(neighbor_position, direction)
            if not is_on_board(neighbor_position):
                return None
            if not is_occupied(curr_state, neighbor_position):
                break
        new_state[piece_id] = neighbor_position
    else:
        # Fox case
        fox_position = curr_state[piece_id]
        orientation = fox_position[2]
        if orientation != direction % 2:
            return None

        new_head = change_position(fox_position, direction)
        # This is some tricky shit below
        new_tail = change_position(new_head, orientation)
        if direction == 0 or direction == 1:
            check_position = new_tail
        else:
            check_position = new_head
        if not is_on_board(check_position) or is_occupied(curr_state, check_position):
            return None
        new_state[piece_id] = new_head
    return new_state


def solved(state):
    solved = True
    for bunny_num in [0, 1, 2]:
        solved = solved and state[bunny_num] in [[0, 0], [0, 4], [2, 2], [4, 0], [4, 4], None]
    return solved


def pretty_print_move(move):
    print(["bunny0", "bunny1", "bunny2", "fox0", "fox1"][move[0]] + " moved " +
          ["right", "down", "left", "up"][move[1]])


def pretty_print_state(movable_state):
    all_state = movable_state + static_state
    for y in range(board_size):
        for x in range(board_size):
            piece_found = False
            for piece_index, piece in enumerate(all_state):
                if piece[0] == x and piece[1] == y:
                    print(["b0", "b1", "b2", "f0", "f1", "m0", "m1", "m2"][piece_index], end=" ")
                    piece_found = True
                if piece_index in [3, 4]:  # It's a fox...
                    # ... and it's head is next to us and this is the tail (according to the
                    # position of the head and orientation of the fox.
                    if (piece[2] == 0 and piece[0] == x - 1 and piece[1] == y) or \
                            (piece[2] == 1 and piece[0] == x and piece[1] == y - 1):
                        print(["b0", "b1", "b2", "f0", "f1", "m0", "m1", "m2"][piece_index],
                              end=" ")
                        piece_found = True
            if not piece_found:
                print("o  ", end="")
        print()
    print()


def find_solution(initial_state):
    stack = deque([(initial_state, None)])
    last_move = None
    while stack:
        if bfs:
            curr_state, last_move = stack.popleft()
        else:
            curr_state, last_move = stack.pop()

        if solved(curr_state):
            print("solution found! Final board state:")
            pretty_print_state(curr_state)
            pretty_print_move(last_move)
            break

        if str(curr_state) in visited:
            continue
        visited[str(curr_state)] = last_move

        # piece_id will be an index 0-4
        for piece_id in range(len(curr_state)):
            for direction in range(4):
                test_state = transform_state(curr_state, piece_id, direction)
                if test_state:
                    # print("moving {} from {} in direction {}".format(piece_id, curr_state[piece_id], direction))
                    stack.append((test_state, (piece_id, direction)))

    solution_path_depth = 0
    while last_move:
        solution_path_depth += 1
        curr_state = transform_state(curr_state, last_move[0], (last_move[1] + 2) % 4)
        last_move = visited[str(curr_state)]
        if solution_path_depth < 2:
            pretty_print_state(curr_state)
            pretty_print_move(last_move)
            print()
        if not last_move:
            print("...{} states not shown...\n".format(solution_path_depth-2))
            print("initial state:")
            pretty_print_state(initial_moveable_state)
    print("solution path length: {}".format(solution_path_depth))


find_solution(initial_moveable_state)