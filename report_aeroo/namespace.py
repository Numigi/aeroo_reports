
from types import SimpleNamespace


class AerooNamespace(SimpleNamespace):

    def update(self, values):
        self.__dict__.update(values)
