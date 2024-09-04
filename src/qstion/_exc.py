class Unparsable(Exception):
    """Exception raised when query string cannot be parsed with QsParser"""

    pass


class ArrayLimitReached(Exception):
    """Exception raised when array limit is reached while parsing query string"""

    pass


class UnbalancedBrackets(Exception):
    """Exception raised when query string contains unbalanced brackets"""

    pass


class EmptyKey(Exception):
    """Exception raised when query string contains empty key and is not allowed"""

    pass


class ConfigurationError(Exception):
    """Exception raised when configuration is invalid"""

    pass


class UnknownInputType(Exception):
    """Exception raised when input type is unknown"""

    pass
