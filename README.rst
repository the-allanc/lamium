.. |name| replace:: lamium
.. |summary| replace:: Lamium is a library which provides some syntactic sugar around the requests library to make it nicer to construct URLs, similar to projects like Hammock and Tortilla.

|name|
======

|summary|

.. _repository: https://github.com/the-allanc/lamium/
.. _documentation: https://lamium.readthedocs.io/en/stable/
.. _pypi: https://pypi.python.org/pypi/lamium
.. _coveralls: https://coveralls.io/github/the-allanc/lamium
.. _license: https://github.com/the-allanc/lamium/master/LICENSE.txt
.. _travis: https://travis-ci.org/the-allanc/lamium
.. _codeclimate: https://codeclimate.com/github/the-allanc/lamium

.. |Build Status| image:: https://img.shields.io/travis/the-allanc/lamium.svg
    :target: travis_
    :alt: Build Status
.. |Coverage| image:: https://img.shields.io/coveralls/the-allanc/lamium.svg
    :target: coveralls_
    :alt: Coverage
.. |Docs| image:: https://readthedocs.org/projects/lamium/badge/?version=stable&style=flat
    :target: documentation_
    :alt: Docs
.. |Release Version| image:: https://img.shields.io/pypi/pyversions/lamium.svg
    :target: pypi_
    :alt: Release Version
.. |Python Version| image:: https://img.shields.io/pypi/v/lamium.svg
    :target: pypi_
    :alt: Python Version
.. |License| image:: https://img.shields.io/pypi/l/lamium.svg
    :target: license_
    :alt: License
.. |Code Climate| image:: https://img.shields.io/codeclimate/issues/github/the-allanc/lamium.svg
    :target: codeclimate_
    :alt: Code Climate

|Docs| |Release Version| |Python Version| |License| |Build Status| |Coverage| |Code Climate|

.. all-content-above-will-be-included-in-sphinx-docs

Lamium contains three main types of object:

- Location
- Resource
- Session

Here's what the current example from Hammock looks like in Lamium:

    >>> from lamium import Session
    >>> github = Session().at('https://api.github.com').URL
    >>> resp = github.repos('kadirpekel', 'hammock').matchers.GET()
    >>> for watcher in resp.json: print watcher.get('login')

You can browse the source code and file bug reports at the project repository_. Full documentation can be found `here`__.

__ documentation_
