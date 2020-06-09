============
Contributing
============
If you would like to contribute to Pydora please visit the project's
`GitHub page <https://github.com/mcrute/pydora>`_ and open a pull request with
your changes. To have the best experience contributing, please:

* Don't break backwards compatibility of public interfaces
* Write tests for your new feature/bug fix
* Ensure that existing tests pass
* Update the readme/docstrings, if necessary
* Follow the coding style of the current code-base
* Ensure that your code is PEP8 compliant
* Validate that your changes work with Python 3.5+

All code is reviewed before acceptance and changes may be requested to better
follow the conventions of the existing API.

The build system runs ``tox -e tests,release`` on all supported Python
versions. You can, and should, run this on your pull request before submitting.
