from odoons.addons.git import GitAddons
from odoons.config.yaml import AddonsFile
from odoons.config.yaml import REPOSITORIES_ENTRY

import argparse
import shutil
import logging


ACTION_INIT = 'init'
ACTION_INSTALL = 'install'
ACTION_UPDATE = 'update'
ACTION_RESET = 'reset'
ACTION_PATH = 'list'
MODE_CHOICES = [ACTION_INIT, ACTION_UPDATE, ACTION_INSTALL, ACTION_RESET]

DEFAULT_YAML_FILE = 'addons.yml'


class Odoons:
    def __init__(self):
        # Initialize attributes
        self._args = None
        self._file = None
        self._file_content = None
        self._repositories = []

        # Initialize argument parser
        self._parser = argparse.ArgumentParser(prog='Odoons')
        self._command_parser = self._parser.add_subparsers(title='command', help='command to perform')
        self._init_parser = self._command_parser.add_parser('init')
        self._install_parser = self._command_parser.add_parser('install')
        self._update_parser = self._command_parser.add_parser('update')
        self._list_parser = self._command_parser.add_parser('list')
        self._reset_parser = self._command_parser.add_parser('reset')
        self.__configure_parsers()
        self.__set_command_routines()

    def __configure_parsers(self):
        # Top level argument
        self._parser.add_argument(
            '-f',
            '--file',
            default=DEFAULT_YAML_FILE,
            help='Path to odoons YAML file',
        )

        # Init command arguments
        self._init_parser.add_argument(
            '--no-requirements',
            action='store_true',
            help='Ignore PIP requirements.txt installation from cloned repositories',
        )

        # Install command arguments
        self._install_parser.add_argument(
            '-x',
            '--exclude',
            nargs='+',
            help='Addons to exclude from requirement installation',
        )

        # Update command arguments
        self._update_parser.add_argument(
            '--no-requirements',
            action='store_true',
            help='Ignore PIP requirements.txt installation from cloned repositories',
        )
        self._update_parser.add_argument(
            '-x',
            '--exclude',
            nargs='+',
            help='Addons to exclude from requirement installation',
        )

        # List command arguments
        self._list_parser.add_argument(
            '-f',
            '--filter',
            choices=['init', 'missing', 'all'],
            default='init',
            help='List filter',
        )

    def __set_command_routines(self):
        self._init_parser.set_defaults(execute=self.init)
        self._install_parser.set_defaults(execute=self.install)
        self._update_parser.set_defaults(execute=self.update)
        self._list_parser.set_defaults(execute=self.odoons_list)
        self._reset_parser.set_defaults(execute=self.reset)

    def _load_odoons(self):
        logging.info('Loading file {}'.format(self._args.file))
        self._file = self._args.file
        yaml_file = AddonsFile(self._file)
        yaml_file.load()
        self._file_content = yaml_file.content
        for name, data in self._file_content[REPOSITORIES_ENTRY].items():
            self._repositories.append(GitAddons.from_yaml(name, data))

    def _save_oddons(self):
        shutil.copyfile(self._file, '.odoons.yml')

    def init(self):
        logging.info('Odoons initializing...')
        for repository in self._repositories:
            repository.init(install_requirement=not self._args.no_requirements)
        self._save_oddons()

    def install(self):
        logging.info('Odoons installing requirements...')
        for repository in self._repositories:
            repository.install_pip_requirements()

    def update(self):
        logging.info('Oddons updating addons...')
        for repository in self._repositories:
            if self._args.exclude and repository.name in self._args.exclude:
                logging.info('Ignoring {}'.format(repository.name))
                continue
            logging.info('Updating {}'.format(repository.name))
            repository.update(update_requirement=not self._args.no_requirements)
        self._save_oddons()

    def odoons_list(self):
        logging.info('Odoons listing addons...')
        initialized_file = AddonsFile('.odoons.yml')
        initialized_file.load()
        existing = [
            GitAddons.from_yaml(name, data)
            for name, data in initialized_file.content[REPOSITORIES_ENTRY].items()
        ]
        for r in existing:
            print(r.name, '\t', r.url, '\t', r.abspath)

    def reset(self):
        logging.info('Odoons resetting addons...')
        for repository in self._repositories:
            print('Deleting repository', repository.name, 'located at', repository.abspath)
            repository.reset()

    def exec(self, args=None):
        if args:
            self._args = self._parser.parse_args(args)
        else:
            self._args = self._parser.parse_args()
        self._load_odoons()
        self._args.execute()
