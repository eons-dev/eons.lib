import pytest
import logging
import sys, os
import eons
from pathlib import Path

thisPath = Path(__file__).parent.resolve()
utilPath = str(thisPath.joinpath("util"))
classPath = str(thisPath.joinpath("class"))
registerPath = str(thisPath.joinpath("register"))

sys.path.append(utilPath)
sys.path.append(classPath)

from dotdict import dotdict
from DummyExecutor import DummyExecutor

# Try to get a non-existant SelfRegistering without downloading a package from the infrastructure repository.
# Should fail.
def test_inheritance():

    executor = DummyExecutor("Test Package Download")

    # Spoof CLI args.
    executor.args = dotdict({
        'no_repo': True,
        'verbose': 1,
        'config': None
    })
    # executor.extraArgs = {
    #     'repo_store': executor.defaultRepoDirectory,
    #     'repo_url': 'https://api.infrastructure.tech/v1/package',
    # }

    logging.debug(f"Executor args: {executor.args}")
    executor()
    executor.RegisterAllClassesInDirectory(registerPath)

    testCases = [
        'inheritance_positive_control',
        'inheriting_error_resolution',
        'inheriting_endpoint'
    ]

    for test in testCases:
        registered = executor.GetRegistered(test)
        assert (registered is not None)
