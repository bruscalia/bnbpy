import argparse
import os
import sys

from setuptools import Extension, setup

# -----------------------------------------------------------------------------
# ARGPARSER
# -----------------------------------------------------------------------------

parser = argparse.ArgumentParser()

parser.add_argument(
    '--nopyx',
    dest='nopyx',
    action='store_true',
    help='Whether the pyx files shall be considered at all.',
)
parser.add_argument(
    '--nocython',
    dest='nocython',
    action='store_true',
    help='Whether pyx files shall be cythonized.',
)
parser.add_argument(
    '--markcython',
    dest='markcython',
    action='store_true',
    help='Whether to mark the html cython files.',
)

params, _ = parser.parse_known_args()
sys.argv = [arg for arg in sys.argv if arg.lstrip('-') not in params]

# -----------------------------------------------------------------------------
# ADD MARKED HTML FILES FOR CYTHON
# -----------------------------------------------------------------------------

if params.markcython:
    import Cython.Compiler.Options

    Cython.Compiler.Options.annotate = True

# -----------------------------------------------------------------------------
# HANDLING CYTHON FILES
# -----------------------------------------------------------------------------

# Paths must be relative to the directory of setup.py (setuptools rejects
# absolute paths in extension sources when building from an sdist)
ROOT = os.path.dirname(os.path.realpath(__file__))
CY_PATH = os.path.join('src', 'bnbpy', 'cython')
CY_PATH_PAFSSP = os.path.join('src', 'bnbprob', 'pafssp', 'cython')
CY_PATH_MAXCLIQUE = os.path.join('src', 'bnbprob', 'maxclique')
CPP_PATH_PAFSSP = os.path.join('src', 'bnbprob', 'pafssp', 'cpp')


def list_files(path: str, extension: str) -> list[str]:
    return sorted(
        f
        for f in os.listdir(os.path.join(ROOT, path))
        if f.endswith(extension)
    )


CPP_FILES_PAFSSP = [
    os.path.join(CPP_PATH_PAFSSP, f)
    for f in list_files(CPP_PATH_PAFSSP, '.cpp')
]


def get_ext_pafssp(f: str) -> list[str]:
    return [os.path.join(CY_PATH_PAFSSP, f)] + CPP_FILES_PAFSSP


def pyx_files(path: str) -> list[str]:
    return list_files(path, '.pyx')


ext_modules: list[Extension] = []

if not params.nopyx:
    ext_modules = (
        [
            Extension(f'bnbpy.cython.{f[:-4]}', [os.path.join(CY_PATH, f)])
            for f in pyx_files(CY_PATH)
        ]
        + [
            Extension(
                f'bnbprob.pafssp.cython.{f[:-4]}',
                get_ext_pafssp(f),  # Mandatory to include all cpp files used
                include_dirs=[CPP_PATH_PAFSSP],
            )
            for f in pyx_files(CY_PATH_PAFSSP)
        ]
        + [
            Extension(
                f'bnbprob.maxclique.{f[:-4]}',
                [os.path.join(CY_PATH_MAXCLIQUE, f)],
            )
            for f in pyx_files(CY_PATH_MAXCLIQUE)
        ]
    )
    if not params.nocython:
        # Compilation errors must not be hidden:
        # there is no pure Python fallback for the Cython modules
        from Cython.Build import cythonize

        ext_modules = cythonize(ext_modules)  # type: ignore

# -----------------------------------------------------------------------------
# RUN SETUP
# -----------------------------------------------------------------------------

setup(ext_modules=ext_modules)
