import os
import shutil

from .command import Command
import odoons.utils.printing as printing


class Reset(Command):
    def run(self, args):
        self.load_config(args.file)

        printing.info("Deleting remote addons...")

        def reset_path(path):
            try:
                shutil.rmtree(path)
            except FileNotFoundError:
                printing.warning("Path {} seems already deleted".format(path))

        odoo_path = os.path.abspath(self._odoo["path"])
        reset_path(odoo_path)
        for name, conf in self._addons.items():
            if conf["type"] == "git":
                abspath = os.path.abspath(conf["path"])
                reset_path(abspath)
