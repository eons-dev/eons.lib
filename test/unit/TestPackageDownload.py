import pytest
import logging
import sys, os
import eons as e
import shutil

sys.path.append(os.path.join((os.path.dirname(os.path.abspath(__file__))), "util"))
sys.path.append(os.path.join((os.path.dirname(os.path.abspath(__file__))), "class"))

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
    executor.extraArgs = {
        'repo_store': executor.defaultRepoDirectory,
        'repo_url': 'https://api.infrastructure.tech/v1/package',
    }

    logging.debug(f"Executor args: {executor.args}")
    executor()

    #Make sure test package doesn't exist.
    #package_test is avaliable from infrastructure.tech.
    with pytest.raises(Exception):
        executor.GetRegistered("test")
        assert(False) # just in case something was missed.

    with pytest.raises(Exception):
        executor.GetRegistered("test", "package")
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
    executor.extraArgs = {
        'repo_store': executor.defaultRepoDirectory,
        'repo_url': 'https://api.infrastructure.tech/v1/package',
    }

    logging.debug(f"Executor args: {executor.args}")
    executor()

    logging.info(f"Deleting: {executor.repo['store']}")
    if (os.path.exists(executor.repo['store'])):
        shutil.rmtree(executor.repo['store'])

    test = executor.GetRegistered("test", "package")
    assert(test is not None)
    test(executor=executor)
    assert(test.result == 1)
