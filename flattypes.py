from lattice import PowerSetLattice, YesNoLattice
from collections import defaultdict

"""'Simple' type system.

The type system keeps track of information about variables and their
attributes.  It does so using a mapping from keys to values, where
each key represents some information about some variable.  Each
variable corresponds to a set of keys, representing such things as
whether the variable is defined, whether it is callable, etc.  The
type system maps each key to the set of values that the type system
knows that the key can take.  For example, it might map the key
corresponding to the class of some variable "x" to the set {int,
float}, indicating that x is either an int or a float.

In addition, attributes of variables are also treated as variables,
each corresponding to their own sets of keys.  The variables and keys
form a tree, where the nodes are variables and their attributes (and
the attributes of the attributes and so on), and leaves are keys
corresponding to the variables/attributes.

"""

Defined = YesNoLattice()
OtherAttrs = YesNoLattice()
SameAs = YesNoLattice()
Callable = YesNoLattice()

class Key(object):
    """A leaf in the key tree, used as a key."""
    def __init__(self, name=u''):
        self.name = name

    def __repr__(self):
        return self.name

    def copy_to(self, other, state, depth=5):
        state[other] = state[self]

class Namespace(dict):
    """A map from names to variables.  This can either be for some
    scope or for the attributes of a variable."""
    def __init__(self, name=u''):
        super(Namespace, self).__init__()
        self.name = name

    def __repr__(self):
        return self.name

    def __missing__(self, key):
        ret = self[key] = Variable(u'%s[%r]' % (self.name, key))
        return ret

    def copy_to(self, other, state, depth=5):
        for name in self:
            self[name].copy_to(other[name], state, depth)

class Variable(object):
    """A node in the key tree, representing a variable or attribute."""
    def __init__(self, name=u''):
        self.name = name

        # Whether this name is defined.
        self.defined = Key(name + u'.defined')

        # The attributes of the object.  This only includes the
        # attributes of the object itself, not the attributes of its
        # class.
        self.attrs = Namespace(name + u'.attrs')
        # Whether this variable might have other attributes.
        self.other_attrs = Key(name + u'.other_attrs')

        # Map from variables to whether this variable is the same
        # object as that variable.
        self.same_as = defaultdict(lambda: Key(name + u'.same_as[TODO]'))

        self.callable = Key(name + u'.callable')
        self.args = Namespace(name + u'.args')
        self._return_type = None

    @property
    def cls(self):
        return self.attrs['__class__']

    @property
    def return_type(self):
        if self._return_type is None:
            self._return_type = Variable(self.name + u'.return_type')
        return self._return_type

    def __repr__(self):
        return self.name

    def initialize(self, state):
        state[self.defined] = Defined.YES
        state[self.other_attrs] = OtherAttrs.MAYBE
        state[self.callable] = Callable.MAYBE

    def copy_to(self, other, state, depth=5):
        other.initialize(state)
        if depth <= 0:
            return

        self.defined.copy_to(other.defined, state, depth - 1)

        #self.attrs.copy_to(other.attrs, state, depth - 1)
        self.other_attrs.copy_to(other.other_attrs, state, depth - 1)

        for third_variable in self.same_as:
            is_same = state[self.same_as[third_variable]]
            state[other.same_as[third_variable]] = is_same
            assert state[third_variable.same_as[self]] == is_same
            state[third_variable.same_as[other]] = is_same
        state[self.same_as[other]] = SameAs.YES
        state[other.same_as[self]] = SameAs.YES

        self.callable.copy_to(other.callable, state, depth - 1)
        self.args.copy_to(other.args, state, depth - 1)

        if state[self.callable] >= Callable.YES and self.return_type in state:
            self.return_type.copy_to(other.return_type, state, depth - 1)

        self.attrs.copy_to(other.attrs, state, depth - 1)


class State(dict):
    pass


initial_state = State()

builtins = Namespace('builtins')
builtins['type'].initialize(initial_state)
initial_state[builtins['type'].other_attrs] = OtherAttrs.YES
#builtins['type'].copy_to(builtins['type'].cls, initial_state)

builtins['object'].initialize(initial_state)
builtins['type'].copy_to(builtins['object'].cls, initial_state)

builtins['int'].initialize(initial_state)
builtins['type'].copy_to(builtins['int'].cls, initial_state)

builtins['int'].attrs['__add__'].initialize(initial_state)
initial_state[builtins['int'].attrs['__add__'].callable] = Callable.YES
builtins['int'].copy_to(builtins['int'].attrs['__add__'].args[0], initial_state)
initial_state[builtins['int'].attrs['__add__'].args[1].defined] = Defined.NO
