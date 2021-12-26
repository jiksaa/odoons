import os
import shutil
from configparser import ConfigParser

from .command import Command, commands_registry

from odoons.utils import printing
from odoons.utils.config import OPT_CONF_DIR, OPT_CONF_TEMPLATE, DEFAULT_OPTIONS


class Config(Command):
    def _get_config_path(self, options=None):
        options = self._options or options
        conf_dir = options.get(OPT_CONF_DIR, DEFAULT_OPTIONS[OPT_CONF_DIR])
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir, exist_ok=True)
        return os.path.join(os.path.abspath(conf_dir), "odoo.cfg")

    def _get_template_path(self):
        template_file = self._options.get(OPT_CONF_TEMPLATE, DEFAULT_OPTIONS[OPT_CONF_TEMPLATE])
        return os.path.abspath(template_file)

    def run(self, args):
        printing.info("Generating Odoo configuration file...")
        self.load_config(args.file)

        template_path = self._get_template_path()
        config_path = self._get_config_path()

        shutil.copyfile(template_path, config_path)

        new_options = {}
        options = self._odoo.get("options", {})

        data_dir = options.get("data_dir", False)
        if data_dir:
            options.pop("data_dir")
            new_options.update({"data_dir": os.path.abspath(data_dir)})

        addons_path = commands_registry["addons"]()._addons_path(args)
        options.update({"addons_path": addons_path})

        new_options.update({k: v for k, v in options.items()})

        parser = ConfigParser()
        parser.read(config_path)
        for k, v in new_options.items():
            parser.set("options", k, v)
        with open(config_path, "w+") as configfile:
            parser.write(configfile)

