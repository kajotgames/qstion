import unittest

from . import test_parser

def suite() -> unittest.TestSuite:
    loader = unittest.TestLoader()
    return loader.loadTestsFromModule(test_parser)


def main():
    runner = unittest.TextTestRunner()
    runner.run(suite())


if __name__ == "__main__":
    main()