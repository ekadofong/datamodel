import sys
import unittest
import inspect

import lsst.utils.tests

from pfs.datamodel.drp import PfsArm, PfsMerged, PfsReference, PfsSingle, PfsObject


class DocstringsTestCase(unittest.TestCase):
    def testDocstrings(self):
        for cls in (PfsArm, PfsMerged, PfsReference, PfsSingle, PfsObject):
            for name, attr in inspect.getmembers(cls):
                if not hasattr(attr, "__doc__") or not attr.__doc__:
                    continue
                docstring = attr.__doc__
                for base in cls.__mro__[1:-1]:
                    self.assertNotIn(base.__name__, docstring,
                                     f"{cls.__name__}.{name}.__doc__ contains {base.__name__}: {docstring}")


class TestMemory(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    setup_module(sys.modules["__main__"])
    unittest.main(failfast=True)
