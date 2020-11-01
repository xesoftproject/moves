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
`moves-web` basic web server - hosts .html files and stuff

## run the P.O.C. locally

open 2 terminals and run

```bat
moves-rest
```

```bat
moves-web
```

then point the browser to <http://localhost:8080/>

You should see a simple web page with a way to play chess.
You can start a new game, then a chess board should appair.
You are the white, you start. Choose your move and click on move to make a move
Your move, and then the cpu one, appears below the chess table.

What has happened?

The buttons "emulates" `transcribe` interactions, that will call the
`moves-rest` api to send the inferred speech.

the rest api talk to the chess engine and calculate the next move.

All the moves are sent to an active-mq queue.

The page is is listening on the same queue, and will show the output.
