"""PuzzleDesigner is an API for creating complex puzzles, with a focus on escape rooms."""

from graphviz import Digraph
from collections import defaultdict


class Graph:
    """Utility class."""
    def __init__(self):
        self.nodes = set()
        self.edges = defaultdict(set)


class Thing:
    """ A Thing can be inspected to potentially yield discoveries. A discovery is usually another
    Thing. Things can represent non-physical items (information) or physical items, like a lock,
    key, chair, etc.

    This is intended to be similar to a logical space, which is more general than a strict 3D Euclidean thing,
    but should suffice to represent physical thing and its contents, in that it can both
    represent and contain physical things.

    We track a Thing's `parts` and `contents` separately, even though they are
    related concepts. This is a bit nuanced. Conceptually, composition of
    things has a time/dependency component to. We differentiate the two concepts below:

    *A Thing's `contents`*
    ThingA can have contents which represent other things (e.g. ThingB)
    that can only be discovered after ThingA has been discovered. For example,
    a room must be discovered before the table inside of it can be discovered.
    The dependency (i.e. logical ordering in the DAG) in this case is: thingB depends on
    (is a child of) its container (thingA).

    *A Thing's `parts`*
    On the other hand a thing can be combined with other things to build a composite thing.
    If thing2 is built by combining thing1 with other things, then the the logical ordering of events
    is that you need to have thing1 before you can build thing2, so the dependency (logical ordering)
    in that case is: thing2 (composite item) depends on (is a child of) its 'parts` (including thing1)
    """

    def __init__(self, description, contents=[], parts=[], inspect_handler=None, interactive_mode=False):
        """
        :param description: Text that describes this thing (this can hint at discoveries)
        :param contents: list of other Things contained by this Thing which can
            potentially be discovered (via the `inspect()` function which uses
            the inspect_handler param).
        :param parts: list of other Things that are composed of this thing
        :param inspect_handler: A function that takes an intention and contents of this thing and
            returns a list of zero or more discoveries (each discovery can be another Thing)
        :param interactive_mode: Flag for printing narrative text.
        """
        self.description = description
        if contents:
            if not isinstance(contents, list):
                contents = [contents]
            for c in contents:
                assert isinstance(c, Thing), "contents obj should be of type Thing, not {0}".format(type(c))
        self._contents = contents

        # We track the other things self is `part_of` *and* its sub-`parts`
        self.part_of = set()  # Other composite things that this Thing is a part of.
        for part in parts:
            assert isinstance(part, Thing)
            part.part_of.add(self)  # add a link from the constituent parts to this Thing.
        self.parts = parts
        if not isinstance(parts, list):
            self.parts = [parts]

        if inspect_handler:
            self.inspect_handler = inspect_handler
        else:
            self.inspect_handler = lambda intention, conts: conts  # Return all contents
        self.interactive_mode = interactive_mode


    @property
    def contents(self):
        return self.inspect()

    def inspect(self, intention=None):
        """Handles an intention to inspect within a Thing. Calls the inspect_handler function."""
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
        """Save a file representing the DAG associated with this Thing."""
        def get_shape(thing_element):
            if isinstance(thing_element, Door):
                return "doubleoctagon"
            elif isinstance(thing_element, Key):
                return "oval"
            else:
                return "octagon"

        gv_graph = Digraph(comment='DAG of Puzzle Thing')
        g = self.generate_dag()  # get back a Graph object
        for node in g.nodes:
            gv_graph.node(node.description, shape=get_shape(node))
        for parent, children in g.edges.items():
            for child in children:
                gv_graph.edge(parent.description, child.description)
        gv_graph.render(filename, view=True)
        print("rendered graph")

    def generate_dag(self, graph=None):
        """return a dot representation of the DAG associated with this Thing
        that will start at this thing and have edges to any things that it
        contains by calling generate_dag on its contents, and then recursing."""

        if graph:
            for child in self._contents:
                graph.nodes.add(child)
                graph.edges[self].add(child)
                if isinstance(child, Key):
                    if child.lock:
                        graph.edges[child].add(child.lock)
                child.generate_dag(graph)  # recursive call
            for part_of_obj in self.part_of:
                graph.nodes.add(part_of_obj)
                graph.edges[self].add(part_of_obj)
                if isinstance(part_of_obj, Key):
                    if part_of_obj.lock:
                        graph.edges[part_of_obj].add(part_of_obj.lock)
                part_of_obj.generate_dag(graph)  # recursive call
            return graph
        else:
            g = Graph()
            g.nodes.add(self)
            return self.generate_dag(g)

    def __repr__(self):
        return self.description


class Room(Thing):
    def __init__(self, description, contents=[], parts=[], inspect_handler=None, interactive_mode=False):
        Thing.__init__(self, description, contents, parts, inspect_handler, interactive_mode)


class PhysicalThing(Thing):
    """A physical thing in the world that has properties."""
    def __init__(self, description, contents=[], parts=[], inspect_handler=None, interactive_mode=False):
        Thing.__init__(self, description, contents, parts, inspect_handler, interactive_mode)

    def __repr__(self):
        return "a physical thing, {0}".format(self.description)


class Key(PhysicalThing):
    def __init__(self, description, contents=[], parts=[], inspect_handler=None, interactive_mode=False, lock=None):
        """Lock is an optional value to track the lock that this artifact unlocks."""
        PhysicalThing.__init__(self, description, contents, parts, inspect_handler, interactive_mode)
        self.lock = lock

    def __repr__(self):
        return "a key in the shape of {0}".format(self.description)


class Lock:
    """A Lock can be `unlock()`ed by being provided with a correct key.
    A lock can be applied to a thing to keep the contents unavailable till the key is provided.
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


class Door(Thing, Lock):
    def __init__(self, description, thing_behind_door, key=None, key_test=None, interactive_mode=False):
        """
        A Door with a Lock on it that prevents access to thing behind it when locked.
        A door always has exactly 1 item in its contents, that is its thing.
        When unlocked, can be opened to return a new thing that can be explored.
        When locked, the inspect function returns None.

        :param description: see definition of Thing.
        :param thing: Thing to be returned if this Door is unlocked.
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
        Thing.__init__(self, description, contents=[thing_behind_door])
        self._key = key
        if key:
            key.lock = self

    def open(self):
        return self.contents[0] if self.unlocked else None


# Demonstrate how to compose some primitive classes to represent a riddle.
class Riddle(Thing):
    # A riddle is a Thing who's whose description is a prompt and contents are success.
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
# An escape room is a Locked Thing (the thing outside of the room is what's locked in this case).
def setup_escape_room_example():
    print("\nSetting up a simple single-room escape room...")

    # Create an escape room.
    # Goal of this escape room is to enter a serial killer's lair, find his priceless perfume, and
    # escape before the before police arrive.

    # Create the keys that will be used to lock our things.
    final_key = Key("bottle of ultimate perfume")

    # Create the final locked door that will need to be unlocked to exit the escape room.
    exit_door = Door(
        description="a door that looks like an exit.",
        thing_behind_door=Thing("freedom into the outside world"),
        key=final_key,
        key_test=lambda k: True if k == final_key else False,
        interactive_mode=True)

    # The overall escape experience consists of 5 different rooms that solvers progress through.
    room_5 = Thing(description="room 5 - a slide leads into an empty room",
                   contents=[exit_door],
                   interactive_mode=True)  # Room contains two items.
    room_5_key = Key("room 5 key")
    room_5_door = Door("large tank that you can stand in", thing_behind_door=room_5, key=room_5_key)
    room_4 = Room("room 4 - Library", contents=[room_5_door, room_5_key, final_key], interactive_mode=True)
    room_4_key = Key("room 4 key")
    room_4_door = Door("Door to room 4 - door with keyhole", thing_behind_door=room_4, key=room_4_key)
    room_3 = Room("room 3 - woman room", contents=[room_4_door, room_4_key])
    room_3_key = Key("room 3 key")
    room_3_door = Door("Door to room 3 - hole in wall covered by planks", thing_behind_door=room_3, key=room_3_key)
    room_2 = Room("room 2 - basement", contents=[room_3_door, room_3_key])

    ##### Contents of Room 1 #####
    key_handle = PhysicalThing("key handle with no teeth")
    small_compartment = Thing("small compartment", contents=key_handle)
    door_to_small_compartment = Door("door to small compartment",
                                     thing_behind_door=small_compartment,
                                     key_test=lambda x: x.contains("slide"))
    chair_arm = PhysicalThing("arm of chair", contents=door_to_small_compartment)
    chair = PhysicalThing(description="chair with arms", contents=chair_arm)
    # Different bottles hidden around room 1
    scents = []
    key_tines = []
    perfume_bottles = []
    for i in range(5):
        scents.append(Thing("scent {0} - smell of flowers".format(i)))
        key_tines.append(Key("small piece of metal {0}, hole on end".format(i)))
        perfume_bottles.append(PhysicalThing("perfume bottle {0}".format(i), contents=[scents[i], key_tines[i]]))

    # Bottle 0 in cabinet
    cabinet = PhysicalThing("cabinet", contents=[perfume_bottles[0]])
    cabinet_key = Key("cabinet key")
    cabinet_door = Door("cabinet door", thing_behind_door=cabinet, key=cabinet_key)
    room_2_key = Key("assembled room 2 key", parts=key_tines + scents + [key_handle])
    room_2_door = Door("door to room 2 - door with keyhole",
                       thing_behind_door=room_2,
                       key=room_2_key,
                       key_test=lambda k: room_2_key in k.parts and key_handle in k.parts)

    # Bottle 1 in chest on counter
    chest_with_drawers = PhysicalThing("chest with drawers", contents=perfume_bottles[1])
    perfume_tray = PhysicalThing("perfume tray")
    counter = PhysicalThing("counter", contents=[perfume_tray, chest_with_drawers])

    room_1 = Room("Room 1 - storefront", contents=[room_2_door, chair, counter, cabinet_door, cabinet_key] + perfume_bottles[1:])
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
