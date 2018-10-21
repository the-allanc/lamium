#!/usr/bin/env python

# Project skeleton maintained at https://github.com/the-allanc/skeleton
# All the hard work done by jaraco at https://github.com/jaraco/skeleton

#
# Extract the project identity from the README.
#
import io
import setuptools

with io.open('README.rst', encoding='utf-8') as readme:
    readme = readme.read()


def get_definition(prefix):
    for line in readme.split('\n'):
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    err = 'no line in README.rst with prefix {!r}'.format(prefix)
    raise AssertionError(err)


def get_description():
    d_start = '|summary|\n'
    i_start = readme.index(d_start) + len(d_start)
    return readme[i_start:].strip()


name = get_definition('.. |name| replace:: ')

#
# End extraction code.
#

params = dict(
    name=name,
    use_scm_version=True,
    author="Allan Crooks",
    author_email="allan@increment.one",
    description=get_definition('.. |summary| replace:: '),
    long_description=get_description(),
    license='MIT',
    url=get_definition('.. _repository: '),
    keywords=[],
    py_modules=['lamium'],
    include_package_data=True,
    namespace_packages=name.split('.')[:-1],
    python_requires='>=2.7',
    install_requires=[
        'crookbook',
        'requests',
        'six',
    ],
    extras_require={
        'testing': [
            'mock',
            'requests_mock',
            'pytest>=3.5',
            'pytest-sugar>=0.9.1',
            'collective.checkdocs',
            'pytest-cov',
            'pylint',
        ],
        'docs': [
            'sphinx',
            'jaraco.packaging>=3.2',
            'rst.linker>=1.9',
            'allanc-sphinx[yeen]>=0.2',
        ],
        'lint': [
            'flake8',
            'radon',
            'pylint',
        ],
        'manage': [
            'bump2version>=0.5.6',
            'tox>=2.4',
            'pip-tools',
        ],
    },
    setup_requires=[
        'setuptools_scm>=1.15.0',
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        # "Development Status :: 4 - Beta",
        # "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    entry_points={
    },
)

if __name__ == '__main__':
    setuptools.setup(**params)
