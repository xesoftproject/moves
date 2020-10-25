# simple moves rest server

rest endpoint that convert to push notifications to apache activemq (amazon-mq)
+ a simple demo of web subscription using stomp.js

## install - prerequisities

to avoid using amazon-mq, you need a local running apache active-mq. Get it from
http://activemq.apache.org/components/classic/download/

for the ease of testing, change the port: open
`apache-activemq-5.16.0\conf\activemq.xml` and change the `stomp`
and `ws` ports to `12346` and `12347`, as in:

```xml
<transportConnector name="stomp" uri="stomp://0.0.0.0:12346?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
<transportConnector name="ws" uri="ws://0.0.0.0:12347?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
```


## install - windows

```bat
python -mvenv VENV
VENV\Script\Activate
python -mpip install path\to\moves 
```

## install - linux

```sh
python -mvenv VENV
. VENV/Script/Activate
python -mpip install path/to/moves 
```

## executables

`moves-rest` rest interface to push stuff on STOMP broker
`moves-web` basic web server - hosts .html files and stuff

## run the P.O.C. locally

open 3 terminals and run

```bat
apache-activemq-5.16.0\bin\activemq start
```

```bat
moves-rest
```

```bat
moves-web
```

then point the browser to `http://localhost:8080/`

when you click on "Big red button" a list item should appear on the right side.

what has happened?

the button "emulates" `transcribe`, that will call the `moves-rest` api
to send the inferred speech.

(missing: the rest api should talk to the chess engine and calculate the next
move)

The "next move" is sent to an active-mq queue.

The "right side" is listening on the same queue, and will show the output.


(missing: the listening is a piece movement, and should be interpreted)
