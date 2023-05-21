from setuptools import setup
from Cython.Build import cythonize
import numpy

setup(
    name='frame_to_string_cy',
    ext_modules=cythonize("frame_to_string_cy.pyx"),
    include_dirs=[numpy.get_include()]
)