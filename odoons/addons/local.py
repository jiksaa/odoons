from odoons.addons.abstract import OdoonsAddons


class LocalAddons(OdoonsAddons):

    def __init__(self, name, path):
        super().__init__(name, path)
        self._type = 'local'

    def init(self, install_requirement=True):
        if install_requirement:
            self.install_pip_requirements()

    def update(self, update_requirement=True):
        if update_requirement:
            self.install_pip_requirements()

    def reset(self):
        pass

    @staticmethod
    def from_yaml(name, data):
        # TODO: implements
        return LocalAddons('dummy', '.')
