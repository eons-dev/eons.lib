import os
import logging
from pathlib import Path
from ebbs import Builder

# Class name is what is used at cli, so we defy convention here in favor of ease-of-use.
class test(Builder):
    def __init__(this, name="Test"):
        super().__init__(name)

        this.clearBuildPath = False

        this.requiredKWArgs.append("test_path") #new build path
        this.requiredKWArgs.append("test_fixture") #ebbs json

        this.optionalKWArgs["test_args"] = [] #any extra args

        this.supportedProjectTypes = []

    # Required Builder method. See that class for details.
    def DidBuildSucceed(this):
        return True  # TODO: how would we even know?

    # Required Builder method. See that class for details.
    def Build(this):
        tempRepoStore = str(Path(this.test_path).joinpath('eons/'))
        this.Copy(this.executor.repo['store'], tempRepoStore)
        os.chdir(this.test_path)
        this.RunCommand(f"ebbs . -v -c {this.test_fixture} {' '.join(this.test_args)} --repo_store {tempRepoStore}")
        this.Delete(tempRepoStore)