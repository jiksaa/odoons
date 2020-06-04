import yaml

REPOSITORIES_ENTRY = 'repositories'
PATH_ENTRY = 'path'
URL_ENTRY = 'url'
BRANCH_ENTRY = 'branch'
COMMIT_ENTRY = 'commit'


class AddonsFile:

    def __init__(self, path):
        self._path = path
        self._read = False
        self._content = False

    @property
    def path(self):
        return self._path

    @property
    def content(self):
        if not self._read:
            raise Exception('File should be read first')
        return self._content

    def _validate_content(self):
        if not self._content:
            raise Exception('Empty repositories file')
        if REPOSITORIES_ENTRY not in self._content:
            raise Exception('Missing `{}` entry'.format(REPOSITORIES_ENTRY))
        if not isinstance(self._content[REPOSITORIES_ENTRY], dict):
            raise Exception('Invalid `{}` content'.format(REPOSITORIES_ENTRY))

        missing_msg = []

        def check(keys, entry, r_name):
            if entry not in keys:
                missing_msg.append('Entry {} missing for {}'.format(entry, r_name))

        for name, data in self._content[REPOSITORIES_ENTRY].items():
            data_keys = data.keys()
            check(data_keys, PATH_ENTRY, name)
            check(data_keys, URL_ENTRY, name)
            if BRANCH_ENTRY not in data_keys and COMMIT_ENTRY not in data_keys:
                missing_msg.append('Entry `{}` or `{}` is missing'.format(BRANCH_ENTRY, COMMIT_ENTRY))
        if missing_msg:
            raise Exception('\n'.join(missing_msg))

    def load(self):
        with open(self._path, 'r') as file:
            self._content = yaml.load(file, Loader=yaml.FullLoader)
            self._read = True
            self._validate_content()

