from functools import total_ordering

class Lattice(object):
    def __init__(self):
        class ElementType(object):
            def __and__(self, other):
                if isinstance(other, ElementType):
                    if self == other:
                        return self
                    if other is not TOP:
                        return BOT
                return NotImplemented

            def __or__(self, other):
                if isinstance(other, ElementType):
                    if self == other:
                        return self
                    if other is not BOT:
                        return TOP
                return NotImplemented                    
        self.ElementType = ElementType

        class TopType(ElementType):
            def __and__(self, other):
                if isinstance(other, ElementType):
                    return other
                return NotImplemented
            __rand__ = __and__

            def __or__(self, other):
                if isinstance(other, ElementType):
                    return self
                return NotImplemented
            __ror__ = __or__

            def __repr__(self):
                return 'TOP'
        TOP = TopType()
        self.TOP = TOP

        class BotType(ElementType):
            def __and__(self, other):
                if isinstance(other, ElementType):
                    return self
                return NotImplemented
            __rand__ = __and__

            def __or__(self, other):
                if isinstance(other, ElementType):
                    return other
                return NotImplemented
            __ror__ = __or__

            def __repr__(self):
                return 'BOT'
        BOT = BotType()
        self.BOT = BOT


class PowerSetLattice(object):
    def make_subset(self, elements):
        self._check_valid(elements)
        if len(elements) == 0 and self.BOT is not None:
            return self.BOT
        elif len(elements) >= self.max_elements and self.TOP is not None:
            return self.TOP
        else:
            return self._Subset(elements)

    def make_inverted_subset(self, elements):
        self._check_valid(elements)
        if len(elements) == 0 and self.TOP is not None:
            return self.TOP
        elif len(elements) >= self.max_elements and self.BOT is not None:
            return self.BOT
        else:
            return self._Subset(elements, inverted=True)

    def only(self, element):
        return self.make_subset([element])

    def never(self, element):
        return self.make_inverted_subset([element])

    def is_valid_element(self, element):
        return True

    def _check_valid(self, elements):
        for element in elements:
            if not self.is_valid_element(element):
                raise TypeError('invalid element: %r' % element)

    def __init__(self, max_elements):
        self.max_elements = max_elements
        lat = self

        class Subset(object):
            def __init__(self, elements, inverted=False):
                self.elements = frozenset(elements)
                self.inverted = inverted

            def __and__(self, other):
                if isinstance(other, Subset):
                    if not self.inverted and not other.inverted:
                        return lat.make_subset(
                            self.elements.intersection(other.elements))
                    elif not self.inverted and other.inverted:
                        return lat.make_subset(self.elements - other.elements)
                    elif self.inverted and not other.inverted:
                        return lat.make_subset(other.elements - self.elements)
                    else:
                        return lat.make_inverted_subset(
                            self.elements.union(other.elements))
                return NotImplemented

            def __or__(self, other):
                if isinstance(other, Subset):
                    if not self.inverted and not other.inverted:
                        return lat.make_subset(
                            self.elements.union(other.elements))
                    elif not self.inverted and other.inverted:
                        return lat.make_inverted_subset(
                            other.elements - self.elements)
                    elif self.inverted and not other.inverted:
                        return lat.make_inverted_subset(
                            self.elements - other.elements)
                    else:
                        return lat.make_inverted_subset(
                            self.elements.intersection(other.elements))
                return NotImplemented

            def __invert__(self):
                if self.inverted:
                    return lat.make_subset(self.elements)
                else:
                    return lat.make_inverted_subset(self.elements)

            def __eq__(self, other):
                return isinstance(other, Subset) and \
                    self.inverted == other.inverted and \
                    self.elements == other.elements

            def __le__(self, other):
                return self & other == self

            def __ge__(self, other):
                return self & other == other

            def __ne__(self, other):
                return not self == other

            def __lt__(self, other):
                return self <= other and self != other

            def __gt__(self, other):
                return self >= other and self != other

            def __hash__(self):
                return hash((self.inverted, self.elements))

            def __repr__(self):
                if self == lat.BOT:
                    return u'BOT'
                elif self == lat.TOP:
                    return u'TOP'
                elements = u' | '.join(map(repr, self.elements))
                if self.inverted:
                    return u'~ (%s)' % elements
                else:
                    return elements

        self._Subset = Subset

        self.BOT = None
        self.TOP = None
        self.BOT = self.make_subset([])
        self.TOP = self.make_inverted_subset([])


class FinitePowerSetLattice(PowerSetLattice):
    def __init__(self, *element_names):
        class Element(object):
            def __init__(self, name):
                self.name = name
            def __repr__(self):
                return unicode(self.name)
        self.elements = frozenset(Element(name) for name in element_names)

        super(FinitePowerSetLattice, self).__init__(len(self.elements))

        for element in self.elements:
            self.__dict__[element.name] = self.only(element)

    def make_inverted_subset(self, elements):
        return self.make_subset(self.elements - set(elements))

    def is_valid_element(self, element):
        return element in self.elements


class YesNoLattice(FinitePowerSetLattice):
    def __init__(self):
        super(YesNoLattice, self).__init__('YES', 'NO')
        self.MAYBE = self.TOP
