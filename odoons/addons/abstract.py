from abc import ABC, abstractmethod

import os
import subprocess


class OdoonsAddons(ABC):
    """
    This class represents an Odoo Addons collections to load on the current odoo instance
    It is made abstract since the addons collection may have different format such as:
        - local directory
        - git/svn repository
        - ...

    A typical OdooAddons instance is defined by the following attributes:
        - name(str):    name of the OdoonsAddons collection
        - path(str):    path to the collection

    The following behaviours are expected from an OdoonsAddons instance:
        - init()
        - update()
        - reset()

    Moreover static method `from_yaml` allows object instantiation according to the given YAML
    data structure.
    """
    def __init__(self, name, path):
        assert name, 'name attribute should have a value'
        assert path, 'path attribute should have a value'
        self._name = name
        self._path = path
        self._type = 'abstract'

    @property
    def name(self):
        return self._name

    @property
    def abspath(self):
        return os.path.abspath(self._path)

    @property
    def type(self):
        return self._type

    def is_initialized(self):
        """
        Check if the repositories is initialized.
        An instance is considered initialized when all the following conditions are correct:
            - self._target_path exists
            - self._target_path is a directory
            - self._target_path is not empty

        :return: True if self is initialized, False otherwise
        """
        abs_path = self.abspath
        return os.path.exists(abs_path) and os.path.isdir(abs_path) and os.listdir(abs_path)

    def install_pip_requirements(self):
        assert self.is_initialized(), 'Instance should be initialized to install pip requirements'
        req_file_path = os.path.join(self.abspath, 'requirements.txt')
        if os.path.exists(req_file_path) and os.path.isfile(req_file_path):
            subprocess.run(['pip', 'install', '-r', req_file_path], check=True)
        else:
            print('WARNING: could not find requirements for repository {}'.format(self._name))

    @abstractmethod
    def init(self, install_requirement=True):
        pass

    @abstractmethod
    def update(self, update_requirement=True):
        pass

    @abstractmethod
    def reset(self):
        pass

    @staticmethod
    @abstractmethod
    def from_yaml(name, data):
        pass

