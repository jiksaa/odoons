import os
import re
import shutil
import argparse
import subprocess
from configparser import ConfigParser, ExtendedInterpolation

from ruamel.yaml import YAML

from . import printing
from .git import Git


ACTION_INIT = "init"
ACTION_INSTALL = "install"
ACTION_MIGRATE = "migrate"
ACTION_UPDATE = "update"
ACTION_RESET = "reset"
ACTION_ADDONS = "addons"
ACTION_CONFIG = "config"

DEFAULT_YAML_FILE = "odoons.yml"
DEFAULT_ODOO_URL = "https://github.com/odoo/odoo"


def is_sha1_string(value):
    pattern = re.compile(r"\b[0-9a-f]{40}\b")
    return bool(re.match(pattern, value))


class Odoons:
    def __init__(self):
        self.__setup_parsers()
        self.odoons_file = None
        self._args = None

    def __setup_parsers(self):
        # Top level argument
        self._parser = argparse.ArgumentParser(prog="Odoons")
        self._parser.add_argument(
            "-f",
            "--file",
            default=DEFAULT_YAML_FILE,
            help="Path to odoons YAML file",
        )

        self._command_parser = self._parser.add_subparsers(title="command", help="command to perform")

        # Init command arguments
        self._init_parser = self._command_parser.add_parser(ACTION_INIT)
        self._init_parser.add_argument(
            "--no-requirements",
            action="store_true",
            help="Ignore PIP requirements.txt installation from cloned repositories",
        )
        self._init_parser.add_argument(
            "--skip-config",
            action="store_true",
            help="Skip Odoo configuration file generation",
        )
        self._init_parser.set_defaults(execute=self.init)

        # Install command arguments
        self._install_parser = self._command_parser.add_parser(ACTION_INSTALL)
        self._install_parser.set_defaults(execute=self.install)

        # Migrate command arguments
        self._migrate_parser = self._command_parser.add_parser(ACTION_MIGRATE)
        self._migrate_parser.add_argument(
            "-b",
            "--buildout-file",
            help="Odoo buildout file to migrate",
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
        yaml = YAML(typ="safe")
        with open(self.file_path, "r") as file:
            self.odoons_file = yaml.load(file)
        if "odoons" not in self.odoons_file:
            raise Exception("missing odoons section")
        self._odoo = self.odoons_file["odoons"]["odoo"]
        self._options = self.odoons_file["odoons"].get("options", [])
        self._addons = self.odoons_file["odoons"].get("addons", [])

    def _init_odoo(self):
        printing.info("Cloning Odoo core...")
        abspath = os.path.abspath(self._odoo["path"])
        url = self._odoo.get("url", DEFAULT_ODOO_URL)
        branch = self._odoo["version"]
        freeze = self._odoo.get("commit", None)

        Git(abspath, url, branch, freeze).clone()

        if self._options.get("install-odoo-command", False):
            printing.info("Installing odoo command...")
            subprocess.run(["pip", "install", "-e", abspath, "--no-deps"], check=True)

    def _init_addons(self):
        printing.info("Cloning addons...")
        potential_errors = []
        for name, conf in self._addons.items():
            printing.info("Initializing {}...".format(name))
            conf_type = conf["type"]
            abspath = os.path.abspath(conf["path"])
            if conf_type == "git":
                git = Git(
                    abspath,
                    conf["url"],
                    conf.get("branch", None),
                    conf.get("freeze", None),
                )
                returncode = git.clone()
                if returncode != 0:
                    potential_errors.append((name, conf))

        if potential_errors:
            printing.warning("Some addons repository cloning seems to have issues")
            printing.warning("Check execution logs for the following:")
            for name, conf in potential_errors:
                printing.warning(name)

    def init(self):
        """
        Action method responsible of the ACTION_INIT sub command

        :return: None
        """
        printing.info("Initializing project...")

        apply_requirements = (
            "apply-requirements" in self._options
            and self._options["apply-requirements"]
            and not self._args.no_requirements
        )
        skip_config_generation = self._args.skip_config

        self._init_odoo()
        self._init_addons()

        if apply_requirements:
            self.install()

        if not skip_config_generation:
            self.config()

    def config(self):
        printing.info("Generating Odoo configuration file...")
        template_file = self._options.get("config-template", "odoo.cfg.template")
        template_path = os.path.abspath(template_file)
        config_path = os.path.abspath("odoo.cfg")

        shutil.copyfile(template_path, config_path)

        new_options = {}
        options = self._odoo.get("options", {})

        data_dir = options.get("data_dir", False)
        if data_dir:
            options.pop("data_dir")
            new_options.update({"data_dir": os.path.abspath(data_dir)})

        options.update({"addons_path": self._addons_path()})

        new_options.update({k: v for k, v in options.items()})

        parser = ConfigParser()
        parser.read(config_path)
        for k, v in new_options.items():
            parser.set("options", k, v)
        with open(config_path, "w+") as configfile:
            parser.write(configfile)

    def install(self):
        """
        Action method responsible of the ACTION_INSTALL sub command

        :return: None
        """
        printing.info("Installing python dependencies...")

        def pip_install(path, addons_name):
            req_file_path = os.path.join(path, "requirements.txt")
            if os.path.exists(req_file_path) and os.path.isfile(req_file_path):
                subprocess.run(["pip", "install", "-r", req_file_path], check=True)
            else:
                printing.warning("No requirements file for {}".format(addons_name))

        pip_install(self._odoo["path"], "odoo")
        for name, conf in self._addons.items():
            pip_install(conf["path"], name)

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
        if not buildout_parser.has_section("buildout"):
            raise RuntimeError("Invalid buildout file: missing buildout section")
        buildout_section = dict(buildout_parser.items("buildout"))
        if "extends" in buildout_section:
            extend_file = os.path.join(os.path.dirname(buildout_file), buildout_section["extends"])
            return self._get_buildout_file_hierarchy(extend_file, data)

        return data

    def migrate(self):
        """
        Migrate the given buildout file to an YAML Odoons compatible file

        :return: None
        """
        printing.info("Migrating buildout file to Odoons...")
        extends_list = self._get_buildout_file_hierarchy(self._args.buildout_file, [])
        odoo_config = dict()
        # Read buildout file hierarchy from top to bottom
        for file in extends_list:
            file_parser = self._get_config_parser()
            file_parser.read(file)
            if file_parser.has_section("odoo"):
                odoo_config.update(file_parser.items("odoo"))

        odoons_data = {"odoons": dict()}

        # Odoo YAML section
        version = odoo_config.get("version", None)
        if not version:
            raise RuntimeError("Unidentified Odoo version: check version key on buildout file")
        splited_value = version.split(" ")
        odoons_data["odoons"]["odoo"] = dict(
            {
                "version": splited_value[3],
                "url": splited_value[1],
                "path": "parts/"
                + splited_value[2],  # Hardcoding parts: ts not obvious where it is defined on buildout file
            }
        )

        # Odoo - options YAML section
        options = {}
        options_prefix = "options."
        for key, value in odoo_config.items():
            if key.startswith(options_prefix):
                options[key[len(options_prefix) :]] = value
        if options:
            odoons_data["odoons"]["odoo"]["options"] = options

        # Options YAML section
        odoons_data["odoons"]["options"] = {
            "install-odoo-command": True,
            "apply-requirements": True,
            # TODO: maybe add config template generation ?
        }

        # Addons YAML section
        addons = odoo_config.get("addons", None)
        revisions = odoo_config.get("revisions", "")
        if not addons:
            raise RuntimeError("No addons defined on buildout file. Does migrate the file still useful ?")
        revisions_dict = {}
        if revisions:
            for value in revisions.split("\n"):
                items = value.split(" ")
                # Commit hash only applies to Odoo repository
                if len(items) == 1:
                    odoons_data["odoons"]["odoo"]["commit"] = items[0]
                if len(items) == 2:
                    revisions_dict[items[0]] = items[1]

        buildout_addons_list = addons.split("\n")
        addons = {}
        for buildout_addons in buildout_addons_list:
            items = buildout_addons.split(" ")
            if items[0] == "git" and len(items) >= 4:
                # [ 'git', URL, PATH, REVISION, [OPTIONS] ]
                revision = items[3]
                path = items[2]
                git_url = items[1]
                d = dict({"type": "git", "path": path, "url": git_url})

                if is_sha1_string(revision):
                    d.update(freeze=revision)
                else:
                    d.update(branch=revision)

                # Revision has been set apply it
                if path in revisions_dict:
                    d["freeze"] = revisions_dict[path]

                try:
                    prefix = "group="
                    if items[4].startswith(prefix):
                        d["path"] = os.path.join(d["path"], items[4][len(prefix) :])
                    print("Unknown addons definition: ", items[4])
                except IndexError:
                    pass
                name = os.path.basename(os.path.normpath(d["path"]))
                addons[name] = d
                continue
            if items[0] == "local" and len(items) == 2:
                # [ 'local', PATH ]
                d = {"type": "local", "path": items[1]}
                name = os.path.basename(os.path.normpath(d["path"]))
                addons[name] = d
                continue
        odoons_data["odoons"]["addons"] = addons

        yaml = YAML(typ="safe")
        yaml.default_flow_style = False
        yaml.indent(mapping=2, sequence=4, offset=2)
        with open(self._args.file, "w") as outfile:
            yaml.dump(odoons_data, outfile)

    def update(self):
        """
        Action method responsible of the ACTION_UPDATE sub command

        :return: None
        """
        printing.info("Updating project addons...")
        apply_requirements = "apply-requirements" in self._options and self._options["apply-requirements"]

        Git(
            self._odoo["path"],
            self._odoo.get("url", DEFAULT_ODOO_URL),
            self._odoo["version"],
            self._odoo.get("commit", None),
        ).update()
        for name, conf in self._addons.items():
            if conf["type"] == "git":
                git = Git(
                    conf["path"],
                    conf["url"],
                    conf.get("branch", None),
                    conf.get("freeze", None),
                )
                git.update()

        if apply_requirements:
            self.install()

    def _addons_path(self):
        """
        Action method responsible of the ACTION_LS sub command

        :return: None
        """
        odoo_path = os.path.abspath(self._odoo["path"])
        paths = [
            os.path.join(odoo_path, "odoo/addons"),
            os.path.join(odoo_path, "addons"),
        ]
        for name, conf in self._addons.items():
            abspath = os.path.abspath(conf["path"])
            paths.append(abspath)
        return ",".join(paths)

    def addons(self):
        print(self._addons_path())

    def reset(self):
        """
        Action method responsible of the ACTION_RESET sub command

        :return: None
        """
        printing.info("Deleting remote addons...")

        def reset_path(path):
            try:
                shutil.rmtree(path)
            except FileNotFoundError:
                printing.warning("Path {} already deleted".format(path))

        odoo_path = os.path.abspath(self._odoo["path"])
        reset_path(odoo_path)
        for name, conf in self._addons.items():
            if conf["type"] == "git":
                reset_path(os.path.abspath(conf["path"]))

    def exec(self, args=None):
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

        if self._args.execute != self.migrate:
            self._load_file()
        self._args.execute()


def main():
    Odoons().exec()


if __name__ == "__main__":
    main()
