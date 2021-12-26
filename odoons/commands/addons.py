import os

from .command import Command


class Addons(Command):
    def _addons_path(self, args):
        """
        Action method responsible of the ACTION_LS sub command

        :return: None
        """
        if not self._odoo or not self._addons:
            self.load_config(args.file)

        odoo_path = os.path.abspath(self._odoo["path"])
        paths = [
            os.path.join(odoo_path, "odoo/addons"),
            os.path.join(odoo_path, "addons"),
        ]
        for name, conf in self._addons.items():
            abspath = os.path.abspath(conf["path"])
            paths.append(abspath)
        return ",".join(paths)

    def run(self, args):
        print(self._addons_path(args))
