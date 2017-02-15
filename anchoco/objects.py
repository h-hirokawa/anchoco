from ansible.utils import module_docs


class Module(object):
    _docstring = None

    def __init__(self, name, path):
        self.name = name
        self.path = path

    @property
    def doc(self):
        if not self._docstring:
            self._get_docstring()
        return self._docstring[0]

    def _get_docstring(self):
        self._docstring = module_docs.get_docstring(self.path)

    def __repr__(self):
        return '<module: {}>'.format(self.name)


class Directive(object):
    def __init__(self, name, targets, default=None):
        self.name = name
        self.targets = targets

    @property
    def targets_string(self):
        return ', '.join([t.__name__ for t in self.targets])

    def __repr__(self):
        return '<directive for {}: {}>'.format(self.targets_string, self.name)
