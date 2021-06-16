from os import name

from pkg_resources import resource_filename

# the rest hostname
HOSTNAMES = ['localhost']

# stockfish executable path (if not in $PATH)
STOCKFISH = ('/usr/games/stockfish'
             if name == 'posix'
             else '/Users/vito.detullio/Desktop/work stuff/bu media contest/stockfish_12_win_x64_bmi2/stockfish_20090216_x64_bmi2.exe')

CERTFILE = resource_filename('moves', 'localhost.crt')
KEYFILE = resource_filename('moves', 'localhost.key')
