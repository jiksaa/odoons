import os
import subprocess

from . import printing


class Git:
    def __init__(self, path, url, branch=None, commit=None):
        self._path = path
        self._url = url
        self._branch = str(branch) if branch else None
        self._commit = str(commit) if commit else None

    def is_git_directory(self):
        command = ["git", "-C", self._path, "status"]
        process = subprocess.call(command, stderr=subprocess.STDOUT, stdout=open(os.devnull, "w"))
        return process == 0

    def is_frozen(self):
        return bool(self._commit)

    def clone(self):
        if self.is_git_directory():
            return self.update()

        command = ["git", "clone", "--depth", "1"]

        if not self.is_frozen():
            command += ["-b", self._branch]

        command += [self._url, self._path]
        printing.debug("Running command:" + str(command))
        printing.next_muted()
        sp = subprocess.Popen(command)
        sp.wait()
        printing.reset()

        if not self.is_frozen() or sp.returncode != 0:
            return sp.returncode

        printing.info("Repository is frozen to: {}".format(self._commit))
        return self.checkout()

    def update(self):
        if not self.is_git_directory():
            return self.clone()

        path = os.path.abspath(self._path)
        git_command = ["git", "-C", path]
        printing.next_muted()
        subprocess.run(git_command + ["fetch", "origin"])
        if not self.is_frozen():
            process = subprocess.run(git_command + ["reset", "--hard", "origin/" + self._branch])
            printing.reset()
            return process.returncode

        return self.checkout()

    def checkout(self):
        if not self.is_git_directory():
            return self.clone()
        fetch_return = self.fetch_commit()
        if fetch_return != 0:
            printing.error("Error fetching commit")
            return fetch_return
        checkout_return = self.checkout_commit()
        return checkout_return

    def checkout_commit(self):
        checkout_command = ["git", "-C", self._path, "reset", "--hard", self._commit]
        printing.debug("Running command:" + str(checkout_command))
        printing.next_muted()
        sp = subprocess.Popen(checkout_command)
        sp.wait()
        printing.reset()
        return sp.returncode

    def fetch_commit(self):
        checkout_command = ["git", "-C", self._path, "fetch", "--depth", "1", "origin", self._commit]
        printing.debug("Running command:" + str(checkout_command))
        printing.next_muted()
        sp = subprocess.Popen(checkout_command)
        sp.wait()
        printing.reset()
        return sp.returncode
