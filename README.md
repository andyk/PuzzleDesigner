# PuzzleDesigner
An API for designing puzzles, with a focus on escape rooms as a type of puzzle.

## Installing/running
So far, this only requires Python. I use a conda env for dev (but that isn't a dependency yet).
* git checkout and `cd` into the repo
* run `$ python main.py` at your command line

## Goals & Vision

The idea is to codify some of the real esape rooms we've done.

In escape rooms, puzzles in various forms (e.g. find a hidden object, solve a riddle, decode a cipher)
are used as keys to locked spaces, which in turn often contain a key (or part of a composite key) for
other locked spaces. Sometimes locked spaces contain other smaller locked spaces (for some definition
of smaller). It seems we should be able to capture these dependencies into an architecture 
and reason about their properties.

The goal of this architectural API is to help us reason about what makes a puzzle a puzzle, how do
the various related concepts (e.g., locks, keys, riddles, puzzles, solutions, ciphers, etc.)
all relate to each other.

Can we ultimately create a data structure that captures sophisticated layered/nested DAGs of puzzles. 
Can we automate (or at least facilitate and ease) the design and creation of new puzzles and escape
rooms that are enjoyable and challenging but balanced?

This includes understanding and capturing the design constraints of puzzles and escape rooms, including
the puzzle difficulty and balance, potential parallelism for teams working together, hint systems,
and how to associate story-telling components (characters, back-story, plot, etc.) with puzzles.
