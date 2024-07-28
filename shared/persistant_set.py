import pickle
import os

class PersistentSet:
    def __init__(self, filename):
        self.filename = filename
        self._data = set()
        self._load()

    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'rb') as file:
                    self._data = pickle.load(file)
            except (pickle.UnpicklingError, EOFError, FileNotFoundError):
                print("Error reading pickle file. Initializing with an empty set.")

    def _save(self):
        with open(self.filename, 'wb') as file:
            pickle.dump(self._data, file)

    def add(self, element):
        self._data.add(element)
        self._save()

    def remove(self, element):
        self._data.remove(element)
        self._save()

    def discard(self, element):
        self._data.discard(element)
        self._save()

    def pop(self):
        element = self._data.pop()
        self._save()
        return element

    def clear(self):
        self._data.clear()
        self._save()

    def update(self, *others):
        self._data.update(*others)
        self._save()

    def union(self, *others):
        return self._data.union(*others)

    def intersection(self, *others):
        return self._data.intersection(*others)

    def difference(self, *others):
        return self._data.difference(*others)

    def symmetric_difference(self, other):
        return self._data.symmetric_difference(other)

    def issubset(self, other):
        return self._data.issubset(other)

    def issuperset(self, other):
        return self._data.issuperset(other)

    def isdisjoint(self, other):
        return self._data.isdisjoint(other)

    def copy(self):
        return self._data.copy()

    def __len__(self):
        return len(self._data)

    def __contains__(self, element):
        return element in self._data

    def __iter__(self):
        return iter(self._data)

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return repr(self._data)

# # Example usage
# pset = PersistentSet('persistent_set.pkl')
# pset.add('apple')
# pset.add('banana')
# pset.add('cherry')
# print(pset)

# pset.remove('banana')
# print(pset)
