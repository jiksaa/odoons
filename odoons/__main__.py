from odoons.main import Odoons

import logging


def main():
    logging.basicConfig(level=logging.INFO)
    Odoons().exec()


if __name__ == '__main__':
    main()
