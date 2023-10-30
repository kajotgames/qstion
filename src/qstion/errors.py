# Parser errors

class Unparsable(Exception):
    pass


class ArrayLimitReached(Exception):
    pass


class UnbalancedBrackets(Exception):
    pass


class EmptyKey(Exception):
    pass
