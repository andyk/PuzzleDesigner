"""PuzzleDesigner is an API for creating complex puzzles, with a focus on escape rooms."""

from graphviz import Digraph

class Space:
    """ A Space can be inspected to potentially yield discoveries. A discovery is usually another
    Space. Spaces can represent non-physical items (information) or physical items, like a lock,
    key, chair, etc.

    This is intended to be a logical space, which is more general than a strict 3D Euclidean space,
    but should suffice to represent physical space and its contents, in that it can both
    represent and contain physical things."""

    def __init__(self, description, contents=[], inspect_handler=None, interactive_mode=False):
        """
        :param description: Text that describes this space (this can hint at discoveries)
        :param contents: list of other Spaces contained by this space which can
            potentially be discovered (via the `inspect()` function which uses
            the inspect_handler param).
        :param inspect_handler: A function that takes an intention and contents of this space and
            returns a list of zero or more discoveries (each discovery can be another Space)
        :param interactive_mode: Flag for printing narrative text.
        """
        self.description = description
        if contents:
            if not isinstance(contents, list):
                contents = [contents]
            for c in contents:
                assert isinstance(c, Space), "contents obj should be of type Space, not {0}".format(type(c))
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

    def save_dag_file(self, filename):
        """Save a file representing the DAG associated with this Space."""
        self.generate_dag().render(filename, view=True)

    def generate_dag(self, graph=None):
        """return a dot representation of the DAG associated with this Space
        that will start at this space and have edges to any spaces that it
        contains by calling generate_dag on it's contents, and then recursing."""
        def get_shape(space_element):
            if isinstance(space_element, Door):
                return "doubleoctagon"
            elif isinstance(space_element, Key):
                return "trapezium"
            else:
                return "octagon"

        if graph:
            for child in self._contents:
                graph.node(child.description, shape=get_shape(child))
                graph.edge(self.description, child.description)
                print(self.description)
                child.generate_dag(graph)
                if isinstance(child, Key):
                    if child.lock:
                        graph.edge(child.description, child.lock.description)
            #TODO: Add a way to visualize composite keys/artifacts correctlyin the DAG
            #for parent in self._parents:
            return graph
        else:
            new_graph = Digraph(comment='DAG of Puzzle Space')
            new_graph.node(self.description, shape=get_shape(self))
            return self.generate_dag(new_graph)

    def __repr__(self):
        return self.description


class Room(Space):
    def __init__(self, description, contents=[], inspect_handler=None, interactive_mode=False):
        Space.__init__(self, description, contents, inspect_handler, interactive_mode)


class Artifact(Space):
    """A physical thing in the world that has properties."""
    def __init__(self, description, contents=[], inspect_handler=None, interactive_mode=False):
        Space.__init__(self, description, contents, inspect_handler, interactive_mode)

    def __repr__(self):
        return "an artifact, {0}".format(self.description)


class Key(Artifact):
    def __init__(self, description, contents=[], inspect_handler=None, interactive_mode=False, lock=None):
        """Lock is an optional value to track the lock that this artifact unlocks."""
        Artifact.__init__(self, description, contents, inspect_handler, interactive_mode)
        self.lock = lock

    def __repr__(self):
        return "a key in the shape of {0}".format(self.description)


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

class AssembledArtifact(Lock, Artifact):
    """"A lock that is unlocked when the necessary parts are present"""

    def __init__(self, description, parts, key=None, key_test=None, interactive_mode=False):
        """:param parts: a list of other artifacts that were assembled into this one."""
        assert isinstance(parts, list)
        Lock.__init__(self, key_test, interactive_mode)
        Artifact.__init__(self, description, contents=parts)


class Door(Space, Lock):
    def __init__(self, description, space, key=None, key_test=None, interactive_mode=False):
        """
        A Door with a Lock on it that prevents access to space behind it when locked.
        A door always has exactly 1 item in its contents, that is its space.
        When unlocked, can be opened to return a new space that can be explored.
        When locked, the inspect function returns None.

        :param description: see definition of Space.
        :param space: Space to be returned if this Door is unlocked.
        :param key_test: Function that takes a key and returns True if the key unlocks
            the contents of this object, else False.
        :param interactive_mode: Flag for printing narrative text.
        """
        self.description = description
        if not key_test:
            if key:
                def key_test(x): return x is key
            else:
                raise Exception("at least one of key and key_test required.")
        Lock.__init__(self, key_test, interactive_mode)
        Space.__init__(self, description, contents=[space])
        self._key = key
        if key:
            key.lock = self

    def open(self):
        return self.space if self.unlocked else None


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
    exit_door = Door(
        description="a door that looks like an exit.",
        space=Space("freedom into the outside world"),
        key=final_key,
        key_test=lambda k: True if k == final_key else False,
        interactive_mode=True)

    # The overall escape experience consists of 5 different rooms that solvers progress through.
    room_5 = Space(description="room 5 - a slide and an empty room that the slide leads into",
                   contents=[exit_door],
                   interactive_mode=True)  # Room contains two items.
    room_5_key = Key("room 5 key")
    room_5_door = Door("large tank that you can stand in", space=room_5, key=room_5_key)
    room_4 = Room("room 4 - Library", contents=[room_5_door, final_key], interactive_mode=True)
    room_4_key = Key("room 4 key")
    room_4_door = Door("Door to room 4 - door with keyhole", space=room_4, key=room_4_key)
    room_3 = Room("room 3 - woman room", contents=[room_4_door])
    room_3_key = Key("room 3 key")
    room_3_door = Door("Door to room 3 - hole in wall covered by planks", space=room_3, key=room_3_key)
    room_2 = Room("room 2 - basement", contents=[room_3_door])

    ##### Contents of Room 1 #####
    key_handle = Artifact("A key with no teeth but a cylinder where teeth would normally be")
    small_compartment = Space("small compartment", contents=key_handle)
    door_to_small_compartment = Door("door to small compartment",
                                     space=small_compartment,
                                     key_test=lambda x: x.contains("slide"))
    chair_arm = Artifact("arm of chair", contents=door_to_small_compartment)
    chair = Artifact(description="chair with arms", contents=chair_arm)
    counter = Artifact("counter")
    scent_1 = Space("smell 1 - smell of flowers")
    key_tine_1 = Key("small piece of metal, rectangular with hollow hole on one end")
    perfume_bottle = Artifact("perfume bottle 1", contents=[scent_1, key_tine_1])
    cabinet = Space("cabinet", contents=[perfume_bottle])
    cabinet_key = Key("cabinet key")
    cabinet_door = Door("cabinet door", space=cabinet, key=cabinet_key)
    room_2_key = Key("assembled room 2 key")
    # TODO: add a way to representing assembling something as a special type of Door
    #       that returns an assembled artifact that visualizes in the DAG correctly
    #room_2_key = AssembledKey("assembled room 2 key", parents=[key_tine_1, key_handle])
    #room_2_key_assemble_lock = Lock(lambda k: room_2_key in k.contents and key_handle in k.contents)
    room_2_door = Door("door to room 2 - door with keyhole",
                       space=room_2,
                       key=room_2_key,
                       key_test=lambda k: room_2_key in k.contents and key_handle in k.contents)
    # TODO: add 3 other perfume bottles hidden around room 1
    room_1 = Room("Room 1 - storefront", contents=[room_2_door, chair, counter, cabinet_door, cabinet_key])
    return room_1

def play_escape_room_example(room):
    print("\nPlaying our example escape room...")
    discoveries = room.inspect("look around")
    exit_door = discoveries[0]
    room_key = discoveries[1]
    print("the door {0}".format("is locked" if exit_door.locked else "is unlocked"))
    exit_door.contents  # This is a convenience wrapper around inspect()
    exit_door.unlock(room_key)
    print("the door {0}".format("is locked" if exit_door.locked else "is unlocked"))
    exit_door.open()

if __name__ == "__main__":
    riddle_example()

    room = setup_escape_room_example()
    room.save_dag_file("example_dag.gv")
    play_escape_room_example(room)
