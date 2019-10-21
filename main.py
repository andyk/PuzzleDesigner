"""PuzzleDesigner is an API for creating complex pluzzles, with a focus on escape rooms."""

class Puzzle:
    def __init__(self, solution_test, inspect_handler):
        """:param solution_test: A function that returns True for correct solution, else False."""
        self.solution_test = solution_test
        self.inspect_handler = inspect_handler

    def inspect(self, intention):
        return self.inspect_handler(intention)

    def solve(self, solution_attempt):
       return True if self.solution_test(solution_attempt) else False

class LockedSpace(Puzzle):
    def __init__(self, key_test, contents, name, description):
        super(key_test)
        self.contents = contents
        self.name = name
        self.description = description

    def attempt_unlock(self, attempt_key):
        if super.solve(attempt_key):
            return self.contents

class Key:
    def __init(self, description):
        self.description = description

#########################
# Example Usage
#########################

# A riddle is a puzzle.
riddle = Puzzle(solution_test=lambda x: True if x.lower().find("clock") == 0 else False,
                inspect_handler=lambda x: "I have 2 hands but can't grasp things. What am I?")

print(riddle.inspect("listen to riddle"))
print("testing solution 'baby': {0}".format(riddle.solve("baby")))
print("testing solution 'clock': {0}".format(riddle.solve("clock")))

# An escape room is a Locked Space (the outside of the overall room is the locked space)
#LockedSpace("perfumer")
