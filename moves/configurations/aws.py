# web server port (where you point your browser at)
WEB_PORT = 8080

# the rest hostname
REST_HOSTNAME = 'www.xesoft.ml'

# rest server port (where the POST goes)
REST_PORT = 5000

# ws port (where the js consumer listen to)
WS_PORT = 61619

# stomp port (where the producer send messages)
STOMP_PORT = 61614

# the amq hostname
AMQ_HOSTNAME = 'b-e05495a3-40d2-4782-b15d-2a9ae104e344-1.mq.eu-west-1.amazonaws.com'

# the amq credentials
AMQ_USERNAME = 'XesoftBroker'
AMQ_PASSCODE = 'XesoftBroker'

# "the" name of the queue (TODO: move to a dedicated queeue x user)
AMQ_QUEUE = '/queue/test'

# stockfish executable path (if not in $PATH)
STOCKFISH = '/usr/games/stockfish'

CERTFILE = '/etc/letsencrypt/live/www.xesoft.ml/cert.pem'
KEYFILE = '/etc/letsencrypt/live/www.xesoft.ml/privkey.pem'
