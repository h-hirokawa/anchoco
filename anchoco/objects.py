class Module(object):
    def __init__(self, name):
        self.name = name
        self.type = 'module'

    def __repr__(self):
        return '<module: {}>'.format(self.name)


class Directive(object):
    def __init__(self, name, targets, default=None):
        self.name = name
        self.targets = targets

    def __repr__(self):
        return '<directive for {}: {}>'.format(
            ', '.join([t.__name__ for t in self.targets]), self.name)
