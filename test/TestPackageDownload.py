import pytest
import logging
import sys, os
import eons as e
import shutil

sys.path.append(os.path.join((os.path.dirname(os.path.abspath(__file__))), "util"))
sys.path.append(os.path.join((os.path.dirname(os.path.abspath(__file__))), "class"))

from dotdict import dotdict
from TestExecutor import TestExecutor

#Try downloading a package from the infrastructure repository.
def test_package_download():

    executor = TestExecutor("Test Package Download")

    #Spoof CLI args.
    executor.args = dotdict({
        'no_repo': True,
        'repo_store': executor.defaultRepoDirectory,
        'repo_url': 'https://api.infrastructure.tech/v1/package'
    })

    logging.debug(f'Executor args: {executor.args}')

    logging.info(f'Deleting: {executor.args.repo_store}')
    shutil.rmtree(executor.args.repo_store)
    
    #Make sure test package doesn't exist.
    #package_test is avaliable from infrastructure.tech.
    with pytest.raises(Exception):
        executor.GetRegistered("test")
        assert(False) # just in case something was missed.

    with pytest.raises(Exception):
        executor.GetRegistered("test", "package")
        assert(False) # just in case something was missed.

    executor.args.no_repo = False
    logging.debug(f'Executor args: {executor.args}')

    #Should try to download https://infrastructure.tech/package/package_test and succeed.
    test = executor.GetRegistered("test", "package")
    assert(test is not None)
    assert(test())
