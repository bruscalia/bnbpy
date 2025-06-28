import argparse
import os
import sys

from setuptools import Extension, setup

# -----------------------------------------------------------------------------
# BASE CONFIGURATION
# -----------------------------------------------------------------------------

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

BASE_PACKAGE = 'bnbpy'

base_kwargs: dict[str, str | list[str]] = {}

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
    '--nolibs',
    dest='nolibs',
    action='store_true',
    help='Whether the libraries should be compiled.',
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
# CLASS TO BUILD EXTENSIONS
# -----------------------------------------------------------------------------


# exception that is thrown when the build fails
class CompilingFailed(Exception):
    pass


# -----------------------------------------------------------------------------
# HANDLING CYTHON FILES
# -----------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.realpath(__file__))
CY_PATH = os.path.join(ROOT, 'src', 'bnbpy', 'cython')
CY_PATH_PFSSP = os.path.join(ROOT, 'src', 'bnbprob', 'pfssp', 'cython')
CPP_PATH_PFSSP = os.path.join(ROOT, 'src', 'bnbprob', 'pfssp', 'cpp')
CPP_FILES_PFSSP = [
    os.path.join(CPP_PATH_PFSSP, f)
    for f in os.listdir(CPP_PATH_PFSSP)
    if f.endswith('.cpp') and 'environ' not in f
]
CY_PATH_SLPFSSP = os.path.join(ROOT, 'src', 'bnbprob', 'slpfssp', 'cython')
CPP_PATH_SLPFSSP = os.path.join(ROOT, 'src', 'bnbprob', 'slpfssp', 'cpp')
CPP_FILES_SLPFSSP = [
    os.path.join(CPP_PATH_SLPFSSP, f)
    for f in os.listdir(CPP_PATH_SLPFSSP)
    if f.endswith('.cpp') and 'environ' not in f
]
HPP_PATH_PFSSP = os.path.join(ROOT, 'include')


def get_ext_pfssp(f: str) -> list[str]:
    return [os.path.join(CY_PATH_PFSSP, f)] + CPP_FILES_PFSSP


def get_ext_slpfssp(f: str) -> list[str]:
    return [os.path.join(CY_PATH_SLPFSSP, f)] + CPP_FILES_SLPFSSP


if params.nopyx:
    ext_modules = []

else:
    try:
        ext_modules_base = [
            Extension(
                f'bnbpy.cython.{f[:-4]}',
                [os.path.join(CY_PATH, f)],
            )
            for f in os.listdir(CY_PATH) if f.endswith('.pyx')
        ]
        ext_modules_pfssp = [
            Extension(
                'bnbprob.pfssp.cpp.environ',
                [os.path.join(CPP_PATH_PFSSP, 'environ.pyx')]
                    + CPP_FILES_PFSSP,
                include_dirs=[CPP_PATH_PFSSP],
                language="c++",
            )
        ] + [
            Extension(
                f'bnbprob.pfssp.cython.{f[:-4]}',
                get_ext_pfssp(f),  # Mandatory to include all cpp files used
                include_dirs=[CPP_PATH_PFSSP],
            )
            for f in os.listdir(CY_PATH_PFSSP) if f.endswith('.pyx')
        ]
        ext_modules_slpfssp = [
            Extension(
                'bnbprob.slpfssp.cpp.environ',
                [os.path.join(CPP_PATH_SLPFSSP, 'environ.pyx')]
                    + CPP_FILES_SLPFSSP,
                include_dirs=[CPP_PATH_SLPFSSP],
                language="c++",
            )
        ]
        # + [
        #     Extension(
        #         f'bnbprob.slpfssp.cython.{f[:-4]}',
        #         get_ext_slpfssp(f),  # Mandatory to include all cpp files used
        #         include_dirs=[CPP_PATH_SLPFSSP],
        #     )
        #     for f in os.listdir(CY_PATH_SLPFSSP) if f.endswith('.pyx')
        # ]

        ext_modules_ = (
            ext_modules_base + ext_modules_pfssp + ext_modules_slpfssp
        )
        if params.nocython:
            ext_modules = ext_modules_
        else:
            try:
                from Cython.Build import cythonize

                ext_modules = cythonize(  # type: ignore
                    ext_modules_
                )
            except ImportError:
                print('*' * 75)
                print('No Cython package found to convert .pyx files.')
                print(
                    'If no compilation occurs, .py files will be used instead,'
                    ' which provide the same results but with'
                    ' worse computational time.'
                )
                print('*' * 75)
                ext_modules = []

    except Exception as e:
        print('*' * 75)
        print('Problems compiling .pyx files.')
        print(f'Exception: {type(e)} - {e}')
        print(
            'If no compilation occurs, .py files will be used instead,'
            ' which provide the same results but '
            'with worse computational time.'
        )
        print('*' * 75)
        ext_modules = []

# -----------------------------------------------------------------------------
# RUN SETUP
# -----------------------------------------------------------------------------

compiled_kwargs = base_kwargs.copy()
compiled_kwargs['ext_modules'] = ext_modules

try:
    setup(**compiled_kwargs)
    print('*' * 75)
    print('Installation successful at the first attempt.')
    print('To verify compilation success run:')
    print('from bnbpy import is_compiled')
    print('*' * 75)
except Exception as e:
    print('*' * 75)
    print(f'Exception: {type(e)} - {e}')
    print('Running setup with cython compilation failed.')
    print('Attempt to a pure Python setup.')
    print(
        'If no compilation occurs, .py files will be used instead,'
        ' which provide the same results but with worse computational time.'
    )
    print('*' * 75)
    setup(**base_kwargs)
