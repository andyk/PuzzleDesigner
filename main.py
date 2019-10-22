"""PuzzleDesigner is an API for creating complex pluzzles, with a focus on escape rooms."""

class Space:
    """ A Space can be inspected to potentially yield discoveries. A discovery is another Space.
    Spaces can represent non-physical items (information) or physical items, like a lock, key,
    chair, etc.

    This is intended to be a logical space, which is more general than a strict 3D Euclidean space,
    but should suffice to represent physical space and its contents, in that it can both
    represent and contain physical things."""

    def __init__(self, description, contents=[], inspect_handler=None, interactive_mode=False):
        """
        :param description: Text that describes this space (this can hint at discoveries)
        :param contents: list of things, e.g., other Spaces, contained by this space
            which can potentially be discovered (via the `inspect()` function which uses
            the inspect_handler param).
        :param inspect_handler: A function that takes an intention and contents of this space and
            returns a list of zero or more discoveries (each discovery can be another Space)
        :param interactive_mode: Flag for printing narrative text.
        """
        self.description = description
        if contents:
            assert isinstance(contents, list)
        self._contents = contents
        if inspect_handler:
            self.inspect_handler = inspect_handler
        else:
            self.inspect_handler = lambda intention, conts: conts  # Return all contents
        self.interactive_mode = interactive_mode

    @property
    def contents(self):
        return self.inspect()

    def inspect(self, intention=None):
        """Handles an intention to inspect within a Space. Calls the inspect_handler function."""
        discoveries = self.inspect_handler(intention, self._contents)
        if self.interactive_mode:
            print("You {0}.".format(intention or "inspect"))
            if discoveries:
                print("You discover the following:")
                [print("  {0}".format(d)) for d in discoveries]
            else:
                print("You don't discover anything")
        return discoveries

    def __repr__(self):
        return self.description

class Lock:
    """A Lock is a thing that can be `unlock()`ed by being provided with a correct key.
    A lock can be applied to a space to keep the contents unavailable till the key is provided.
    A puzzle can be thought of a specific type (or instance) of lock. A puzzle has a solution
    like a lock has a key.

    This class does not specify how a key is tested. The user provides a function that this
    class uses to test for success."""

    def __init__(self, key_test, interactive_mode=False):
        """
        :param key_test: A function that takes a potential key, tests to see if the provided
        key is the correct key, and returns true if the key worked (and also changes the state
        of the lock to represent an unlocked lock)
        :param interactive_mode: Flag for printing narrative text.
        """
        self.key_test = key_test
        self.interactive_mode = interactive_mode
        self._locked = True

    @property
    def locked(self):
        return self._locked

    @property
    def unlocked(self):
        return not self._locked

    def unlock(self, key_attempt):
        """Returns True on succcessful unlock or if lock was already unlocked,
           returns false on failed unlock."""
        if self.key_test(key_attempt):
            self._locked = False
            if self.interactive_mode:
                print("unlock successful")
        elif self.interactive_mode:
            print("unlock failed")
        return self.unlocked


class SpaceIsLocked(Exception):
    pass

class LockedSpace(Space, Lock):
    def __init__(self, description, contents, key_test, interactive_mode=False):
        """
        A Space with a Lock on it that prevents access to its contents when locked.
        When unlocked, that can contain arbitrary contents.

        When this space is locked, the inspect function returns None. If the lock

        :param description: see definition of Space.
        :param contents: Space to be returned if this LockedSpace is unlocked.
        :param key_test: Function that takes a key and returns True if the key unlocks
            the contents of this object, else False.
        :param interactive_mode: Flag for printing narrative text.
        """
        Lock.__init__(self, key_test, interactive_mode)
        Space.__init__(self,
                       description,
                       contents,
                       inspect_handler=lambda i, c: None if self.locked else contents,
                       interactive_mode=interactive_mode)

    def inspect(self, intention=None):
        return Space.inspect(self, intention) if self.unlocked else None


class Key:
    def __init__(self, description):
        self.description = description

    def __repr__(self):
        return "a key in the shape of {0}".format(self.description)


# Demonstrate how to compose some primitive classes to represent a riddle.
class Riddle(Space):
    # A riddle is a Space who's whose description is a prompt and contents are success.
    # A riddle contains a Lock whose key is the riddle's solution. The lock is used to
    # test potential solutions and, for a correct solution, provide the contents, which
    # are success, which manifest as printing and returning a string that says "success".
    def __init__(self, prompt, solution_test):
        def solution_handler(attempt, _):
            if self.solution_test(attempt):
                self.lock = Lock(self.solution_test)  # Reset lock.
                return ["yes!"]
            else:
                return ["wrong, try again"]

        super().__init__(description=prompt,
                         contents=[],  # Empty, using inspect_handler for attempted solutions.
                         inspect_handler=solution_handler)
        self.solution_test = solution_test
        self.lock = Lock(self.solution_test)

    def solve(self, attempt):
        return self.inspect(attempt)

#########################
# Example Usages
#########################

###############
def riddle_example():
    riddle = Riddle(prompt="I have 2 hands but can't grasp things. What am I?",
                    solution_test=lambda x: True if x.lower().find("clock") == 0 else False)

    print("\nListening to and then solving a riddle...")
    discoveries = riddle.inspect("listen to riddle")
    print("testing solution 'baby': {0}".format(riddle.solve("baby")))
    print("testing solution 'clock': {0}".format(riddle.solve("clock")))

###############
# An escape room is a Locked Space (the space outside of the room is what's locked in this case).
def setup_escape_room_example():
    print("\nSetting up a simple single-room escape room...")

    # Create an escape room.
    # Goal of this escape room is to enter a serial killer's lair, find his priceless perfume, and
    # escape before the before police arrive.

    # Create the keys that will be used to lock our spaces.
    final_key = Key("bottle of ultimate perfume")

    # Create the final locked door that will need to be unlocked to exit the escape room.
    exit_door = LockedSpace(
        description="A door that looks like an exit.",
        contents=[Space("Freedom into the outside world")],
        key_test=lambda k: True if k == final_key else False,
        interactive_mode=True)

    # Create the main room that you start in and have to escape from.
    perfumer_room = Space(description="main lair",
                          contents=[exit_door, final_key],
                          interactive_mode=True)  # Room contains two items.

    return perfumer_room

def play_escape_room_example(room):
    print("\nPlaying our example escape room...")
    discoveries = room.inspect("look around")
    exit = discoveries[0]
    room_key = discoveries[1]
    print("the door {0}".format("is locked" if exit.locked else "is unlocked"))
    exit.contents  # This is a convenience wrapper around inspect()
    exit.unlock(room_key)
    print("the door {0}".format("is locked" if exit.locked else "is unlocked"))
    exit.inspect("look at exit door")

if __name__ == "__main__":
    riddle_example()

    room = setup_escape_room_example()
    play_escape_room_example(room)
