import os
import subprocess

from .command import Command
from odoons.utils import printing
from odoons.utils.config import ADDONS_REQ_INSTALL_CONFIG, get_git_addons_path


class Install(Command):
    def run(self, args):
        """
        Action method responsible of the ACTION_INSTALL sub command

        :return: None
        """
        printing.info("Installing python dependencies...")
        self.load_config(args.file)

        def pip_install(path, addons_name):
            req_file_path = os.path.join(path, "requirements.txt")
            if os.path.exists(req_file_path) and os.path.isfile(req_file_path):
                subprocess.run(["pip", "install", "-r", req_file_path], check=True)
            else:
                printing.warning("No requirements file for {}".format(addons_name))

        for name, conf in self._addons.items():
            if conf.get(ADDONS_REQ_INSTALL_CONFIG, True):
                abspath = get_git_addons_path(conf)
                pip_install(abspath, name)

        pip_install(self._odoo["path"], "odoo")
        pip_install(".", "project root")
