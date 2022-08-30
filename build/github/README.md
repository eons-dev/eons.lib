# eons python framework

![build](https://github.com/eons-dev/eons/actions/workflows/python-package.yml/badge.svg)

Generalized framework for doing python things.

Design in short: Self-registering functors for use with arbitrary data structures.

## Installation
`pip install eons`

## Usage

This library is intended for consumption by other executables.
To create your own executable, override `Executor` to add functionality to your program, then create children of `Datum` and `UserFunctor` for adding your own data structures and operations.

See [ebbs](https://github.com/eons-dev/ebbs) and [esam](https://github.com/eons-dev/esam) for examples of how to use this library.

## Design

### Configuration File and Fetch()

eons provides a simple means of retrieving variables from a wide array of places. When you `Fetch()` a variable, we look through:
1. The system environment (e.g. `export some_key="some value"`)
2. The json configuration file supplied with `--config` (or specified by `this.defualtConfigFile` per `Configure()`)
3. Arguments supplied at the command line (e.g. specifying `--some-key "some value"` makes `Fetch(some_key)` return `"some value"`)
4. Member variables of the Executor (e.g. `this.some_key = "some value"`)

The higher the number on the above list, the higher the precedence of the search location. For example, member variables will always be returned before values from the environment.

NOTE: The supplied configuration file must contain only valid json.

### Functors

Functors are classes (objects) that have an invokable `()` operator, which allows you to treat them like functions.
eons uses functors to provide input, analysis, and output functionalities, which are made simple by classical inheritance.

For extensibility, all functors take a `**kwargs` argument. This allows you to provide arbitrary key word arguments (e.g. key="value") to your objects.

### Self Registration

Normally, one has to `import` the files they create into their "main" file in order to use them. That does not apply when using eons. Instead, you simply have to derive from an appropriate base class and then call `SelfRegistering.RegisterAllClassesInDirectory(...)` (which is done for you on the folder paths detailed above), providing the directory of the file as the only argument. This will essentially `import` all files in that directory and make them instantiable via `SelfRegistering("ClassName")`.

#### Example

In some `MyDatum.py` in a `MyData` directory, you might have:
```
import logging
from eons import Datum
class MyDatum(Datum): #Datum is a useful child of SelfRegistering
    def __init__(this, name="only relevant during direct instantiation"):
        logging.info(f"init MyDatum")
        super().__init__()
```
From our main.py, we can then call:
```
import sys, os
from eons import SelfRegistering
SelfRegistering.RegisterAllClassesInDirectory(os.path.join(os.path.dirname(os.path.abspath(__file__)), "MyData"))
```
Here, we use `os.path` to make the file path relevant to the project folder and not the current working directory.
Then, from main, etc. we can call:
```
myDatum = SelfRegistering("MyDatum")
```
and we will get a `MyDatum` object, fully instantiated.

### Online Repository

When using an eons Executor, SelfRegistering classes are retrieved with `Executor.GetRegistered(...)`. If the class you are trying to retrieve is not found in the Registered classes, `GetRegistered` will try to download a package for the class.
You may add credentials and even provide your own repo url for searching. If credentials are supplied, private packages will be searched before public ones.
Online repository settings can be set through:
```
--repo-store
--repo-url
--repo-username
--repo-password
```

You may also publish to the online repository through [ebbs](https://github.com/eons-dev/bin_ebbs)

NOTE: per the above section on the Configuration File, you can set `repo_username` in the environment to avoid passing credentials on the command line, or worse, you can store them in plain text in the configuration file ;)
