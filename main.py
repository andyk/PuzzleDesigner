"""PuzzleDesigner is an API for creating complex pluzzles, with a focus on escape rooms."""


class Space:
    """ A space can be explored and contains potential discoveries within.
    Discoveries can be non-physical items (information) or physical items.
    A Space can contain things like Locks, Keys, and other Spaces.
    This is intended to be more of a logical space than a strict 3D euclidian space
    but should suffice to represent a physical space in that it can contain physical things.
    """
    def __init__(self, description, contents, inspect_handler=None, interactive_mode=False):
        """
        :param description: Text that describes this space (this probably hints at discoveries)
        :param contents: dictionary of potential discoveries (name-value pairs) contained
            by this space.
        :param inspect_handler: A function that takes an intention and contents of this space and
            returns a dict of zero or more discoveries (probably a subset of contents)
        """
        self.description = description
        assert isinstance(contents, dict)
        self.contents = contents
        if inspect_handler:
            self.inspect_handler = inspect_handler
        else:
            self.inspect_handler = lambda intention, conts: conts  # Return all contents
        self.interactive_mode = interactive_mode

    def inspect(self, intention):
        """Handles an intention to inspect within a Space. Calls the inspect_handler function."""
        discoveries = self.inspect_handler(intention, self.contents)
        if self.interactive_mode:
            print("You {0}.".format(intention))
            if discoveries:
                print("You discover the following:")
                [print("  {0}".format(d)) for d in discoveries]
            else:
                print("You don't discover anything")
        return discoveries


class Puzzle:
    """A puzzle is a thing that can be solved by being provided with a correct solution."""
    def __init__(self, solution_test, interactive_mode=False):
        """
        :param solution_test: A function that takes a solution attempt, test to see if the solution
            is correct, and returns a results depending on the correctness of the attempt.
        :param interactive_mode: Flag for printing narrative text.
        """
        self.solution_test = solution_test
        self.interactive_mode = interactive_mode

    def solve(self, solution_attempt):
        return self.solution_test(solution_attempt)


class LockedSpace(Space, Puzzle):
    def __init__(self, description, contents, key_test, interactive_mode=False):
        """
        Represents locked item that can contain arbitrary contents. A Lock is similar to a
        Puzzle in that it can be solved ("unlocked"), but it is more complex. It is also similar
        to a space in that it has contents.

        :param name: Short name of lock.
        :param description: Text describing the lock.
        :param contents: Space returned if the attempt_unlock() succeeds.
        :param key_test: Function that takes a key and returns True if the key unlocks
            the contents of this object, else False.
        """
        Space.__init__(description, contents, interactive_mode)

        assert(isinstance(contents, Space))
        self.contents = contents
        self.key_test = key_test
        self.interactive_mode = interactive_mode

    def attempt_unlock(self, attempt_key):
        if self.key_test(attempt_key):
            if self.interactive_mode:
                print("You successfully unlocked {0} revealing {1}".format(self.contents))
            return self.contents
        else:
            if self.interactive_mode: print("Unlock attempt failed.")
            return None

    def __repr__(self):
        return self.description

class Key:
    def __init__(self, description):
        self.description = description
    def __repr__(self):
        return "<KEY: {0}>".format(self.description)


#########################
# Example Usages
#########################

###############
def riddle_example():
    # Demonstrate how to compose our classes to represent a riddle.
    class Riddle(Space, Puzzle):
        def __init__(self, description, prompt, solution_test):

            Space.__init__(self,
                           description,
                           contents={"prompt": prompt},
                           interactive_mode=True)
            Puzzle.__init__(self, solution_test, interactive_mode=True)

    riddle = Riddle(description="Simple riddle",
                    prompt="I have 2 hands but can't grasp things. What am I?",
                    solution_test=lambda x: "Correct!" if x.lower().find("clock") == 0 else "Wrong")

    print("Listening to and then solving a riddle...\n")
    discoveries = riddle.inspect("listen to riddle")
    print("testing solution 'baby': {0}".format(riddle.solve("baby")))
    print("testing solution 'clock': {0}".format(riddle.solve("clock")))

###############
# An escape room is a Locked Space (the space outside of the room is what's locked in this case).
def setup_escape_room_example():
    print("Setting up and then solving a simple single-room escape room...\n")

    # Create an escape room.
    # Goal of this escape room is to enter a serial killer's lair, find his priceless perfume, and
    # escape before the before police arrive.

    # Create the keys that will be used to lock our spaces.
    final_key = Key("Bottle of ultimate perfume")

    # Create the final locked door that will need to be unlocked to exit the escape room.
    exit_door = Lock(
        key_test=lambda k: True if k == final_key else False,
        contents=Space({"exit": "Freedom into the outside world"}),
        name="the exit from Perfumer's lair",
        description="A door that looks like an exit.",
        interactive_mode=True)

    # Create the main room that you start in and have to escape from.
    perfumer_room = Space("main lair",
                          {"exit": exit_door, "key": final_key}, # Room contains two items.
                          inspect_handler=lambda intent, contents: contents) # Return all contents.

    return perfumer_room

def play_escape_room_example(room):
    # Play the room
    discoveries = room.inspect("look around")
    room_key = discoveries["key"]
    exit = discoveries["exit"]
    unlock_results = exit.attempt_unlock(room_key)

if __name__ == "__main__":
    print("Riddle example:\n")
    riddle_example()
    #print("\n\nSetting up escape room example:\n")
    #room = setup_escape_room_example()
    #print("\nNow playing the example escape room.")
    #play_escape_room_example(room)
