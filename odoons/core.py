import os
import yaml
import shutil
import argparse
import subprocess
from configparser import ConfigParser, ExtendedInterpolation


ACTION_INIT = 'init'
ACTION_INSTALL = 'install'
ACTION_MIGRATE = 'migrate'
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

        # Migrate command arguments
        self._migrate_parser = self._command_parser.add_parser(ACTION_MIGRATE)
        self._migrate_parser.add_argument(
            '-b',
            '--buildout-file',
            help='Odoo buildout file to migrate',
        )
        self._migrate_parser.set_defaults(execute=self.migrate)

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

    @staticmethod
    def _get_config_parser():
        return ConfigParser(interpolation=ExtendedInterpolation(), strict=False)

    def _get_buildout_file_hierarchy(self, buildout_file, data):
        """
        Build the buildout file hiearchy for top to bottom

        :param buildout_file: starting buildout file path
        :param data: list of buildout file hierarchy (recusion accumulator)
        :return: list(str)
        """
        data = [buildout_file] + data
        buildout_parser = self._get_config_parser()
        buildout_parser.read(buildout_file)
        if not buildout_parser.has_section('buildout'):
            raise RuntimeError('Invalid buildout file: missing buildout section')
        buildout_section = dict(buildout_parser.items('buildout'))
        if 'extends' in buildout_section:
            extend_file = os.path.join(os.path.dirname(buildout_file), buildout_section['extends'])
            return self._get_buildout_file_hierarchy(extend_file, data)

        return data

    def migrate(self):
        """
        Migrate the given buildout file to an YAML Odoons compatible file

        :return: None
        """
        extends_list = self._get_buildout_file_hierarchy(self._args.buildout_file, [])
        odoo_config = {}
        # Read buildout file hierarchy from top to bottom
        for file in extends_list:
            file_parser = self._get_config_parser()
            file_parser.read(file)
            if file_parser.has_section('odoo'):
                odoo_config.update(file_parser.items('odoo'))

        odoons_data = {'odoons': {}}

        # Odoo YAML section
        version = odoo_config.get('version', None)
        if not version:
            raise RuntimeError('Unidentified Odoo version: check version key on buildout file')
        splited_value = version.split(' ')
        odoons_data['odoons']['odoo'] = {
            'version': splited_value[3],
            'url': splited_value[1],
            'path': 'parts/' + splited_value[2] # Hardcoding parts: ts not obvious where it is defined on buildout file
        }

        # Odoo - options YAML section
        options = {}
        options_prefix = 'options.'
        for key, value in odoo_config.items():
            if key.startswith(options_prefix):
                options[key[len(options_prefix):]] = value
        if options:
            odoons_data['odoons']['odoo']['options'] = options

        # Options YAML section
        odoons_data['odoons']['options'] = {
            'install-odoo-command': True,
            'apply-requirements': True,
            # TODO: maybe add config template generation ?
        }

        # Addons YAML section
        addons = odoo_config.get('addons', None)
        if not addons:
            raise RuntimeError('No addons defined on buildout file. Does migrate the file still useful ?')
        buildout_addons_list = addons.split('\n')
        addons = {}
        for buildout_addons in buildout_addons_list:
            items = buildout_addons.split(' ')
            if items[0] == 'git' and len(items) >= 4:
                # [ 'git', URL, PATH, BRANCH, [STANDALONE] ]
                d = {'type': 'git', 'path': items[2], 'url': items[1], 'branch': items[3]}
                try:
                    prefix = 'group='
                    if items[4].startswith(prefix):
                        d['path'] = os.path.join(d['path'], items[4][len(prefix):])
                    print('Unknown addons definition: ', items[4])
                except IndexError:
                    pass
                name = os.path.basename(os.path.normpath(d['path']))
                addons[name] = d
                continue
            if items[0] == 'local' and len(items) == 2:
                # [ 'local', PATH ]
                d = {'type': 'local', 'path': items[1]}
                name = os.path.basename(os.path.normpath(d['path']))
                addons[name] = d
                continue
        odoons_data['odoons']['addons'] = addons

        with open(self._args.file, 'w') as outfile:
            yaml.dump(odoons_data, outfile, default_flow_style=False)

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

        if self._args.execute != self.migrate:
            self._load_file()
        self._args.execute()


def main():
    Odoons().exec()


if __name__ == '__main__':
    main()
