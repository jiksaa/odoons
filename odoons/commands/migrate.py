import os
import re
from ruamel.yaml import YAML

from .command import Command

from odoons.utils import printing
from odoons.utils.config import get_config_parser, DEFAULT_OPTIONS


def is_sha1_string(value):
    pattern = re.compile(r"\b[0-9a-f]{40}\b")
    return bool(re.match(pattern, value))


class Migrate(Command):

    def configure_parser(self, parser):
        parser.add_argument("buildout_file", help="Odoo buildout file to migrate")

    def _get_buildout_file_hierarchy(self, buildout_file, data):
        """
        Build the buildout file hiearchy for top to bottom

        :param buildout_file: starting buildout file path
        :param data: list of buildout file hierarchy (recusion accumulator)
        :return: list(str)
        """
        data = [buildout_file] + data
        buildout_parser = get_config_parser()
        buildout_parser.read(buildout_file)
        if not buildout_parser.has_section("buildout"):
            raise RuntimeError("Invalid buildout file: missing buildout section")
        buildout_section = dict(buildout_parser.items("buildout"))
        if "extends" in buildout_section:
            extend_file = os.path.join(os.path.dirname(buildout_file), buildout_section["extends"])
            return self._get_buildout_file_hierarchy(extend_file, data)

        return data

    def run(self, args):
        """
        Migrate the given buildout file to an YAML Odoons compatible file

        :return: None
        """
        printing.info("Migrating buildout file to Odoons...")
        extends_list = self._get_buildout_file_hierarchy(args.buildout_file, [])
        odoo_config = dict()
        # Read buildout file hierarchy from top to bottom
        for file in extends_list:
            file_parser = get_config_parser()
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
        odoons_data["odoons"]["options"] = dict(DEFAULT_OPTIONS)

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
            addons_type, *addons_config = items
            if addons_type == "git":
                # [ 'git', URL, PATH, REVISION, [OPTIONS] ]
                git_url, path, revision, *addons_options = addons_config
                d = dict({"type": "git", "path": path, "url": git_url})
                addons_name = os.path.basename(os.path.normpath(path))

                if is_sha1_string(revision):
                    d.update(commit=revision)
                else:
                    d.update(branch=revision)

                # Revision has been set apply it
                if path in revisions_dict:
                    d["commit"] = revisions_dict[path]

                try:
                    for option in addons_options:
                        prefix = "group="
                        if option.startswith(prefix):
                            group_value = option[len(prefix) :]
                            base_path = os.path.dirname(path)
                            d["path"] = os.path.join(base_path, group_value)
                            d["standalone"] = addons_name
                        else:
                            printing.warning("Unknown addons options: " + option)
                except IndexError:
                    pass
                addons[addons_name] = d
                continue
            elif addons_type == "local" and len(addons_config) == 1:
                # [ 'local', PATH ]
                addons_path = addons_config[0]
                d = {"type": "local", "path": addons_path}
                name = os.path.basename(os.path.normpath(d["path"]))
                addons[name] = d
                continue
            else:
                printing.warning("Unprocessable addons config: {}".format(items))
        odoons_data["odoons"]["addons"] = addons

        yaml = YAML(typ="safe")
        yaml.default_flow_style = False
        yaml.indent(mapping=2, sequence=4, offset=2)
        with open(args.file, "w") as outfile:
            yaml.dump(odoons_data, outfile)
