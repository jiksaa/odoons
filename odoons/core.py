import os
import yaml
import shutil
import argparse
import subprocess
from configparser import ConfigParser


ACTION_INIT = 'init'
ACTION_INSTALL = 'install'
ACTION_UPDATE = 'update'
ACTION_RESET = 'reset'
ACTION_ADDONS = 'addons'
ACTION_CONFIG = 'config'

DEFAULT_YAML_FILE = 'odoons.yml'
DEFAULT_ODOO_URL = 'https://github.com/odoo/odoo'


class Odoons:
    def __init__(self):
        self.__setup_parsers()
        self.odoons_file = None

    def __setup_parsers(self):
        # Top level argument
        self._parser = argparse.ArgumentParser(prog='Odoons')
        self._parser.add_argument(
            '-f',
            '--file',
            default=DEFAULT_YAML_FILE,
            help='Path to odoons YAML file',
        )

        self._command_parser = self._parser.add_subparsers(title='command', help='command to perform')

        # Init command arguments
        self._init_parser = self._command_parser.add_parser(ACTION_INIT)
        self._init_parser.add_argument(
            '--no-requirements',
            action='store_true',
            help='Ignore PIP requirements.txt installation from cloned repositories',
        )
        self._init_parser.set_defaults(execute=self.init)

        # Install command arguments
        self._install_parser = self._command_parser.add_parser(ACTION_INSTALL)
        self._install_parser.set_defaults(execute=self.install)

        # Update command arguments
        self._update_parser = self._command_parser.add_parser(ACTION_UPDATE)
        self._update_parser.set_defaults(execute=self.update)

        # Addons command arguments
        self._addons_parser = self._command_parser.add_parser(ACTION_ADDONS)
        self._addons_parser.set_defaults(execute=self.addons)

        # Config command arguments
        self._config_parser = self._command_parser.add_parser(ACTION_CONFIG)
        self._config_parser.set_defaults(execute=self.config)

        # Reset command arguments
        self._reset_parser = self._command_parser.add_parser(ACTION_RESET)
        self._reset_parser.set_defaults(execute=self.reset)

    def _load_file(self):
        self.file_path = self._args.file
        with open(self.file_path, 'r') as file:
            self.odoons_file = yaml.load(file, Loader=yaml.FullLoader)
        if 'odoons' not in self.odoons_file:
            raise Exception('missing odoons section')
        self._odoo = self.odoons_file['odoons']['odoo']
        self._options = self.odoons_file['odoons'].get('options', [])
        self._addons = self.odoons_file['odoons'].get('addons', [])

    def init(self):
        """
        Action method responsible of the ACTION_INIT sub command

        :return: None
        """

        def git_init(path, url, branch=None):
            command = ['git', 'clone', '--depth', '1']
            if branch:
                branch = branch if isinstance(branch, str) else str(branch)
                command += ['-b', branch]
            command += [url, path]
            print('Running command:', command)
            subprocess.Popen(command).wait()

        apply_requirements = 'apply-requirements' in self._options and self._options['apply-requirements']
        print('Initializing Odoo...')
        abspath = os.path.abspath(self._odoo['path'])
        url = self._odoo.get('url', DEFAULT_ODOO_URL)
        branch = self._odoo['version']
        git_init(abspath, url, branch)
        if self._options.get('install-odoo-command', False):
            subprocess.run(['pip', 'install', '-e', abspath, '--no-deps'], check=True)
        print('Odoo {} initialized in {}'.format(branch, abspath))

        for name, conf in self._addons.items():
            print('Initializing {}...'.format(name))
            conf_type = conf['type']
            abspath = os.path.abspath(conf['path'])
            if conf_type == 'git':
                git_init(abspath, conf['url'], conf.get('branch', None))
            print('Initialized')

        if apply_requirements:
            self.install()

    def config(self):
        template_file = self._options.get('config-template', 'odoo.cfg.template')
        template_path = os.path.abspath(template_file)
        config_path = os.path.abspath('odoo.cfg')

        shutil.copyfile(template_path, config_path)

        new_options = {}
        options = self._odoo.get('options', {})

        data_dir = options.get('data_dir', False)
        if data_dir:
            options.pop('data_dir')
            new_options.update({'data_dir': os.path.abspath(data_dir)})

        options.update({'addons_path': self._addons_path()})

        new_options.update({k: v for k, v in options.items()})

        parser = ConfigParser()
        parser.read(config_path)
        for k, v in new_options.items():
            parser.set('options', k, v)
        with open(config_path, 'w+') as configfile:
            parser.write(configfile)


    def install(self):
        """
        Action method responsible of the ACTION_INSTALL sub command

        :return: None
        """

        def pip_install(path):
            req_file_path = os.path.join(path, 'requirements.txt')
            if os.path.exists(req_file_path) and os.path.isfile(req_file_path):
                subprocess.run(['pip', 'install', '-r', req_file_path], check=True)
            else:
                print('Could not find requirements for {}'.format(name))

        pip_install(self._odoo['path'])
        for name, conf in self._addons.items():
            pip_install(conf['path'])

    def update(self):
        """
        Action method responsible of the ACTION_UPDATE sub command

        :return: None
        """

        def git_update(path, branch=None):
            path = os.path.abspath(path)
            git_command = ['git', '-C', path]
            subprocess.run(git_command + ['fetch', 'origin'])
            if branch:
                branch = branch if isinstance(branch, str) else str(branch)
                subprocess.run(git_command + ['reset', '--hard', 'origin/' + branch])

        apply_requirements = 'apply-requirements' in self._options and self._options['apply-requirements']

        git_update(self._odoo['path'], self._odoo['version'])
        for name, conf in self._addons.items():
            if conf['type'] == 'git':
                git_update(conf['path'], conf.get('branch', 'master'))

        if apply_requirements:
            self.install()

    def _addons_path(self):
        """
        Action method responsible of the ACTION_LS sub command

        :return: None
        """
        odoo_path = os.path.abspath(self._odoo['path'])
        paths = [
            os.path.join(odoo_path, 'odoo/addons'),
            os.path.join(odoo_path, 'addons'),
        ]
        for name, conf in self._addons.items():
            abspath = os.path.abspath(conf['path'])
            paths.append(abspath)
        return ','.join(paths)

    def addons(self):
        print(self._addons_path())

    def reset(self):
        """
        Action method responsible of the ACTION_RESET sub command

        :return: None
        """

        def reset_path(path):
            shutil.rmtree(path)

        odoo_path = os.path.abspath(self._odoo['path'])
        reset_path(odoo_path)
        for name, conf in self._addons.items():
            if conf['type'] == 'git':
                reset_path(os.path.abspath(conf['path']))

    def exec(self, args=None):
        """
        Odoons main method.

        :param args: command line arguments. Default arguments are loaded if not supplied
        :return: None
        """
        if args:
            self._args = self._parser.parse_args(args)
        else:
            self._args = self._parser.parse_args()

        self._load_file()
        self._args.execute()


def main():
    Odoons().exec()


if __name__ == '__main__':
    main()
