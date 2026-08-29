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

Generative AI / LLM Policy
==========================
Please minimize the use of generative AI in patches submitted to this project. The
authors have found changes made by generative AI models to be unnecessarily complex
and require significant additional burden to review. While we will not outright
reject changes authored by a generative AI model they will be treated skeptically
and are more likely to be rejected than changes made by humans.

Patches made by generative AI models will be held to the same standard of quality
as those changes submitted by humans. Review the guidelines above and ensure that
your model follows them.

Building a Release
==================
Official releases are built and uploaded to PyPi using the GitHub |release workflow|_.
To prepare a release, first, bump the ``__version__`` string in
|pandora/__init__.py|_ and push a new release branch with the name
``release-${version}`` where ``${version}`` is the version number from
|pandora/__init__.py|_. The GitHub workflow will do the rest.

The workflow does the same thing that is documented above with the addition of
an upload to PyPi.

.. |pandora/__init__.py| replace:: ``pandora/__init__.py``
.. _pandora/__init__.py: https://github.com/mcrute/pydora/tree/master/pandora/__init__.py

.. |release workflow| replace:: ``release`` workflow
.. _release workflow: https://github.com/mcrute/pydora/blob/master/.github/workflows/release.yml
