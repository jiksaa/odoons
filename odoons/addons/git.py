from odoons.addons.abstract import OdoonsAddons
from odoons.config.yaml import URL_ENTRY
from odoons.config.yaml import PATH_ENTRY
from odoons.config.yaml import BRANCH_ENTRY
from odoons.config.yaml import COMMIT_ENTRY


import subprocess
import shutil


class GitAddons(OdoonsAddons):

    def __init__(self, name, path, url, branch=None, commit=None):
        assert url, 'url attribute should have a value'
        assert not branch or isinstance(branch, str), 'branch attribute should a string'
        assert not commit or isinstance(commit, str), 'commit attribute should a string'
        super().__init__(name, path)
        self._type = 'git'
        self._url = url
        self._branch = branch
        self._commit = commit

    @property
    def url(self):
        return self._url

    def init(self, install_requirement=True):
        if self.is_initialized():
            print('Repository {} seems already initialized. Try updating it...'.format(self._name))
            self.update()
            return

        command = ['git', 'clone', '--depth', '1']
        if self._branch:
            branch = self._branch if isinstance(self._branch, str) else str(self._branch)
            command += ['-b', branch]
        command += [self._url, self._path]
        print('Running command:', command)
        subprocess.Popen(command).wait()

        if not self.is_initialized():
            raise Exception('Could not detect initialization has been processed for {}'.format(self._name))

        if install_requirement:
            self.install_pip_requirements()

    def update(self, update_requirement=True):
        if not self.is_initialized():
            self.init(install_requirement=update_requirement)

        git_command = ['git', '-C', self.abspath]
        subprocess.run(git_command + ['fetch', 'origin'])
        if self._branch:
            subprocess.run(git_command + ['reset', '--hard', 'origin/' + self._branch])
        if self._commit:
            subprocess.run(git_command + ['checkout', self._commit])

        if update_requirement:
            self.install_pip_requirements()

    def reset(self):
        if self.is_initialized():
            shutil.rmtree(self.abspath)

    @staticmethod
    def from_yaml(name, data):
        print('Reading {} repository from yaml'.format(name))
        print(data)
        url = data.get(URL_ENTRY, False)
        path = data.get(PATH_ENTRY, False)
        branch = data.get(BRANCH_ENTRY, False)
        branch = branch if isinstance(branch, str) else str(branch)
        commit = data.get(COMMIT_ENTRY, False)
        return GitAddons(name, path, url, branch, commit)
