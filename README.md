# simple moves rest server

rest endpoint that exposes user actions and send push notifications to amazon-mq
+ a simple demo of web game


## install - prerequisities

To play chess you need a chess engine, like stockfish. Get it from
<https://stockfishchess.org/download/>


## install - windows

```bat
python -mvenv VENV
VENV\Script\Activate
python -mpip install path\to\moves
```

## install - linux

```sh
python -mvenv VENV
. VENV/bin/activate
python -mpip install path/to/moves
```

## executables

`moves-rest` rest interface to push stuff on STOMP broker

## run the P.O.C. locally

open a terminal and run

```bat
moves-rest
```

- or -

launch `python moves/rest`

The REST endpoint root is at <https://localhost:8443/>
