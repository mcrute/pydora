import os
from unittest import TestLoader

def discover_suite():
    return TestLoader().discover(os.path.dirname(__file__))
