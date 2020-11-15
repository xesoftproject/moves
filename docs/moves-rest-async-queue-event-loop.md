# `moves-rest` async queue event loop

the idea is to split the architecture of `moves-rest` in a set of rest
endpoint interacting with an "event loop" tied to the game

User -> /start_new_game:
a new event loop is created - a long lived one.
 - The /update interact with the event loop sending user interactions
 - automatically the game engine (stockfish in this case) send cpu interactions
 - every n millis the queue is read, two (three?) things happens:
    # the moves are applied
    # the moves and the results are notified on amq
    # the moves and results are also notified back to the game engine?

## goal

allow games with cpu-vs-cpu / human-vs-human and everything in between.
We need a way to ensure
1) the start could be from the cpu
2) the user should be able to "pause" the game
3) a "reproducibility" of the games

## architecture

we need a way to create "long lived", background stuff (queue? processes?
threads?) and communicate with them, and destroy them (the user should be able
to exit the game, the game simply ends, etc)

### switching from flask to `quart-trio`

an idea is to use the implicit event loop offered by continuations.


## open points

have just ONE event loop? one per game type? one per game?
For now we settle to one event loop per game. We need to investigate potential
problems of latency in case of a single shared event loop and complexity in case
of one per game.
