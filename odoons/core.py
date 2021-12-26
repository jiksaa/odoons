"""
Odoons.

Usage:
  odoons [-f=<of>|--file=<of>] init [--skip-config] [--no-requirements]
  odoons [-f=<of>|--file=<of>] update
  odoons [-f=<of>|--file=<of>] install
  odoons [-f=<of>|--file=<of>] config
  odoons migrate <buildoutfile>
  odoons [-f=<of>|--file=<of>] reset
  odoons [-f=<of>|--file=<of>] config
  odoons -h | --help
  odoons --version

Options:
  -h --help              Show this screen.
  --version              Show version.
  -f=<of> --file=<of>    Odoons configuration file [default: odoons.yml].
  --skip-config          Skip Odoo configuration file generation
  --no-requirements.     Skip Python requirements installation process


"""
import argparse

from odoons.utils import printing
from odoons.commands import commands_registry


DEFAULT_YAML_FILE = "odoons.yml"


class Odoons:
    def __init__(self):
        self.__setup_main_parser()

    def __setup_main_parser(self):
        self._parser = argparse.ArgumentParser(prog="Odoons")
        self._parser.add_argument(
            "-f",
            "--file",
            default=DEFAULT_YAML_FILE,
            help="Path to odoons YAML file",
        )
        self._command_parser = self._parser.add_subparsers(title="command", dest="command", help="command to perform")
        self._commands = {}
        for command in commands_registry.keys():
            self._commands[command] = self._command_parser.add_parser(command)
            commands_registry[command]().configure_parser(self._commands[command])

    def run(self, args=None):
        """
        Odoons main method.

        :param args: command line arguments. Default arguments are loaded if not supplied
        :return: None
        """
        printing.info("====== Odoons ======")

        if args:
            self._args = self._parser.parse_args(args)
        else:
            self._args = self._parser.parse_args()

        commands_registry[self._args.command]().run(self._args)


def main():
    Odoons().run()


if __name__ == "__main__":
    main()
