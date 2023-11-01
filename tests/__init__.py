import unittest

from . import test_parse, test_stringify

TEST_MODULES = [
    test_parse,
    test_stringify
]



def suites():
    loader = unittest.TestLoader()
    for module in TEST_MODULES:
        yield loader.loadTestsFromModule(module)


def main():
    runner = unittest.TextTestRunner()
    for suite in suites():
        runner.run(suite)


if __name__ == "__main__":
    main()