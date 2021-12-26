import os
import subprocess

from .command import Command

from odoons.utils import printing
from odoons.utils.git import Git
from odoons.utils.config import OPT_INSTALL_ODOO, OPT_APPLY_REQS, get_git_addons_path


DEFAULT_ODOO_URL = "https://github.com/odoo/odoo"


class Pull(Command):

    def _init_odoo(self):
        printing.info("Cloning Odoo core...")
        abspath = os.path.abspath(self._odoo["path"])
        url = self._odoo.get("url", DEFAULT_ODOO_URL)
        branch = self._odoo["version"]
        commit = self._odoo.get("commit", None)

        Git(abspath, url, branch, commit).clone()

        if self._options.get(OPT_INSTALL_ODOO, False):
            printing.info("Installing odoo command...")
            subprocess.run(["pip", "install", "-e", abspath, "--no-deps"], check=True)

    def _init_addons(self):
        printing.info("Cloning addons...")
        potential_errors = []
        for name, conf in self._addons.items():
            printing.info("Initializing {}...".format(name))
            conf_type = conf["type"]
            if conf_type == "git":
                abspath = get_git_addons_path(conf)
                git = Git(
                    abspath,
                    conf["url"],
                    conf.get("branch", None),
                    conf.get("commit", None),
                )
                returncode = git.clone()
                if returncode != 0:
                    potential_errors.append((name, conf))

        if potential_errors:
            printing.warning("Some addons repository cloning seems to have issues")
            printing.warning("Check execution logs for the following:")
            for name, conf in potential_errors:
                printing.warning(name)

    def run(self, args):
        """
        Action method responsible of the ACTION_INIT sub command

        :return: None
        """
        printing.info("Initializing project...")
        self.load_config(args.file)
        self._init_odoo()
        self._init_addons()
