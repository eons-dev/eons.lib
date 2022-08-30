import os
import logging
from ebbs import Builder

class TestError(Exception): pass

class AssertionFailed(TestError): pass

# Class name is what is used at cli, so we defy convention here in favor of ease-of-use.
class test_case(Builder):
    def __init__(this, name="Test"):
        super().__init__(name)

        this.clearBuildPath = False
        this.supportedProjectTypes = []
        
        this.requiredKWArgs.append("assertions")

    # Required Builder method. See that class for details.
    def DidBuildSucceed(this):
        return True  #errors raise exceptions.


    def Assert(this, real, comparator, expected):
        passed = False
        if (comparator == "eq" or comparator == "=="):
            passed = real == expected
        elif (comparator == "ne" or comparator == "!="):
            passed = real != expected
        else:
            raise TestError(f"Unknown or unsupported comparator: {comparator}")
        
        if (not passed):
            raise AssertionFailed(f"{real} not {comparator} to {expected}")

    # Required Builder method. See that class for details.
    def Build(this):
        for assertion in this.assertions:
            if (assertion["kind"] == "command"):
                if (assertion["check"] == "output"):
                    code, output = this.RunCommand(assertion["command"], True)
                    this.Assert(output, assertion["comparator"], assertion["expected"])

                elif (assertion["check"] == "return"):
                    code = this.RunCommand(assertion["command"], False)
                    this.Assert(code, assertion["comparator"], assertion["expected"])
                
                else:
                    raise TestError(f"Unknown or unsupported check: {assertion['check']}")

            else:
                raise TestError(f"Unknown or unsupported kind of assertion: {assertion['kind']}")            
