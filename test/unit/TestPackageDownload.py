import pytest
import logging
import sys, os
import eons
import shutil
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
def test_package_download_without_repo():

    executor = DummyExecutor("Test Package Download")

    # Spoof CLI args.
    executor.args = dotdict({
        'no_repo': True,
        'verbose': 1,
        'config': None
    })

    # These are no longer needed.
    # executor.extraArgs = {
    #     'repo_store': executor.defaultRepoDirectory,
    #     'repo_url': 'https://api.infrastructure.tech/v1/package',
    # }

    logging.debug(f"Executor args: {executor.args}")
    executor()

    #Make sure test package doesn't exist.
    #package_test is avaliable from infrastructure.tech.
    with pytest.raises(Exception):
        executor.GetRegistered("eonstestpackage")
        assert(False) # just in case something was missed.

    with pytest.raises(Exception):
        executor.GetRegistered("eonstestpackage", "package")
        assert(False) # just in case something was missed.


# Try downloading a package from the infrastructure repository.
# Should try to download https://infrastructure.tech/package/package_test and succeed.
def test_package_download_with_repo():

    executor = DummyExecutor("Test Package Download")

    # Spoof CLI args.
    executor.args = dotdict({
        'no_repo': False,
        'verbose': 1,
        'config': None
    })

    logging.debug(f"Executor args: {executor.args}")
    executor()

    # For some reason, the name 'test' is unusable if this line is included.
    # This line comes from TestInheritance and will be run before *this under normal circumstances (i.e. when running all tests).
    # 'test' has thus been renamed to 'eonstestpackage'
    # executor.RegisterAllClassesInDirectory(registerPath)

    logging.info(f"Deleting: {executor.repo['store']}")
    if (os.path.exists(executor.repo['store'])):
        shutil.rmtree(executor.repo['store'])

    test = executor.GetRegistered("eonstestpackage", "package")
    assert(test is not None)
    test(executor=executor)
    assert(test.result == 1)
