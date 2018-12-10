# Development Practices
As this project/library will hopefully grow further in the future, a few general practices are outlined in this document. If you consider extending *pydtnsim* in a way that should finally end up in the core code, please adhere to these practices:

## GitHub Flow
This project follows the [GitHub Flow](https://guides.github.com/introduction/flow/) (rather than the Git Flow or Gitlab Flow). This is due to the simplicity of the GitHub Flow and the limited complexity of this project.

## Semantic Versioning
*pydtnsim* is released using [Semantic Versioning 2.0](https://semver.org/spec/v2.0.0.html).

## License
The project is published under the MIT license. If you want to contribute to this project and your code should become part of the main repository, you are
required to provide your contribution under the MIT license as well. Given the characteristics of the MIT license, you are always able to fork the project and publish it with your extensions under another (less permissive) license.

## Code of Conduct
Please adhere to the [PSF Code of Conduct](https://www.python.org/psf/codeofconduct/).

## Deterministic Behaviour
The implementations of all components in the core library should behave deterministic. This means that when some operation is performed twice on the same structures/information base, it should always result in the same outcome/output.

Please consider this when e.g. using `Dictionaries` (which depend on `HASHSEED`) in a way that affects the outcome of an operation (i.e. by iterating over it). In that case `OrderedDict` might be a helpful option.

If something is supposed to be indeterministic or random, please implement it in a way that the behaviour is based on a seed value that can be provided to the object. This allows users to create reproducible results when using the same seed value.

## Docstrings
Please document your functions and objects! This project uses [Google style docstrings](http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).

## Pylint
In order to keep the code quality level at tha highest possible level, the linting tool `pylint` should be used to validate the code. [Pylint](https://www.pylint.org/) not only checks for programming errors and ambiguities, but also for documentation errors (docstrings, inconsistencies of parameter description) and code complexity.

## Pydocstring
While overlapping in some parts with `pylint`, [`pydocstyle`](http://www.pydocstyle.org/en/2.1.1/) should be used to evaluate the written *docstrings*. In particular, the imperative mood of the summaries and correct formating is enforced when using this tool.

## Continuous ~~Integration~~ (Testing)
As so often in the Gitlab context[^1], the erroneously called **Continuous Integration** functionality is actually used for **Continuous Testing/Building** in the scope of this project.

The CI instance performs the following tests:
- Run `pylint` and `pydocstyle` and check for issues
- Execute all implemented test cases with `pytest` and check for failing assertions.
- Run checks on the implemented CGR flavours/algorithms:
  * Determinism check: Runs the algorithm twice with a given scenario and compare the routing decisions and results afterwards. Fails, if these two runs are not equal.
  * Equivalence check: Runs all algorithms for the same scenario and compares the routing decisions and results. Only succeeds when `SCGR` and `CGR_basic` return the same results. `CGR_anchor` will produce different results due to the anchoring mechanism returning slightly different routes.
- Run all examples in the `examples/` folder. Fail if one of them fails.
- Check if both the legacy JSON format (DTN-TVG-Tools) and the new format (DTN-TVG-Util) are processed without error.

There might be even more checks in the future. Particularly, the comparison of routing decisions to an external routing instance (*ION* or *TVG-Util*) would be very helpful.

[^1]: https://martinfowler.com/bliki/FeatureBranch.html
