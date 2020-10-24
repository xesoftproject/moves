from coilmq import start

from . import configurations

def main():
    raise start._main(port=configurations.PUSH_PORT)

main()
