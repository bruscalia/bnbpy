import argparse
import os
import sys
from distutils.errors import CompileError

from setuptools import Extension, find_packages, setup
from setuptools.command.build_ext import build_ext

# -----------------------------------------------------------------------------
# BASE CONFIGURATION
# -----------------------------------------------------------------------------

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

BASE_PACKAGE = 'bnbpy'

base_kwargs = dict(  # noqa: C408
    name='bnbpy',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    version='0.1.0',
    license='Apache License 2.0',
    description='A Python general Branch & Bound framework.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Bruno Scalia C. F. Leite',
    author_email='bruscalia12@gmail.com',
    url='https://github.com/bruscalia/bnbpy',
    download_url='https://github.com/bruscalia/bnbpy',
    keywords=[
        'Branch & Bound',
        'Branch and Bound',
        'Mixed Integer Programming',
        'Mixed Integer Linear Programming',
        'MIP',
        'MILP',
        'Discrete Optimization',
        'Optimization',
        'Operations Research',
        'Combinatorial Optimization',

    ],
    install_requires=[
        'numpy>=1.21.0',
        'scipy>=1.9.0',
        'Cython==3.*'
    ],
)

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


# try to compile, if not possible throw exception
def construct_build_ext(build_ext):
    class WrappedBuildExt(build_ext):
        def run(self):
            try:
                build_ext.run(self)
            except BaseException as e:
                raise CompilingFailed() from e

        def build_extension(self, ext):
            try:
                build_ext.build_extension(self, ext)
            except BaseException as e:
                raise CompilingFailed() from e

    return WrappedBuildExt


# -----------------------------------------------------------------------------
# HANDLING CYTHON FILES
# -----------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.realpath(__file__))
CY_PATH = os.path.join(ROOT, 'src', 'bnbpy', 'cython')
CY_PATH_PFSSP = os.path.join(ROOT, 'src', 'bnbprob', 'pfssp', 'cython')
CPP_PATH_PFSSP = os.path.join(ROOT, 'src', 'bnbprob', 'pfssp', 'cpp')
CPP_FILES_PFSSP = [
    os.path.join(CPP_PATH_PFSSP, f)
    for f in os.listdir(CPP_PATH_PFSSP) if f.endswith('.cpp')
]
HPP_PATH_PFSSP = os.path.join(ROOT, 'include')


def get_ext_pfssp(f: str):
    return [os.path.join(CY_PATH_PFSSP, f)] + CPP_FILES_PFSSP


if params.nopyx:
    ext_modules = []

else:
    try:
        ext_modules_base = [
            Extension(
                f'bnbpy.cython.{f[:-4]}',
                [os.path.join(CY_PATH, f)],
                # extra_compile_args=["/O2"],
            )
            for f in os.listdir(CY_PATH) if f.endswith('.pyx')
        ]
        ext_modules_pfssp = [
            Extension(
                f'bnbprob.pfssp.cpp.{f[:-4]}',
                # CPP_FILES_PFSSP,
                [os.path.join(CPP_PATH_PFSSP, f)],
                include_dirs=[CPP_PATH_PFSSP],
                # extra_compile_args=["/O2"],
            )
            for f in os.listdir(CPP_PATH_PFSSP) if f.endswith('.cpp')
        ] + [
            Extension(
                f'bnbprob.pfssp.cython.{f[:-4]}',
                get_ext_pfssp(f),
                include_dirs=[CPP_PATH_PFSSP, CY_PATH_PFSSP],
                # extra_compile_args=["/O2"],
            )
            for f in os.listdir(CY_PATH_PFSSP) if f.endswith('.pyx')
        ]

        ext_modules_ = ext_modules_base + ext_modules_pfssp
        if params.nocython:
            ext_modules = ext_modules_
        else:
            try:
                from Cython.Build import cythonize

                ext_modules = cythonize(
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

if not params.nolibs:
    if len(ext_modules) > 0:
        base_kwargs['ext_modules'] = ext_modules

        try:
            import numpy as np

            base_kwargs['include_dirs'] = [np.get_include()]

        except BaseException as e:
            raise CompileError(
                'NumPy libraries must be installed for compiled extensions!'
                ' Speedups are not enabled.'
            ) from e

        base_kwargs['cmdclass'] = dict(  # noqa: C408
            build_ext=construct_build_ext(build_ext)
        )

    else:
        print('*' * 75)
        print('External cython modules found.')
        print('To verify compilation success run:')
        print(
            'from bnbpy import is_compiled'
        )
        print('This function will be True to mark compilation success;')
        print(
            'If no compilation occurs, .py files will be used instead,'
            ' which provide the same results but'
            ' with worse computational time.'
        )
        print('*' * 75)

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
