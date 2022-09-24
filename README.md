# eons python framework

Generalized framework for doing python things.

Design in short: Self-registering functors downloaded just-in-time for use with arbitrary data structures.

## Installation
`pip install eons`

## Usage

This library is intended for consumption by other executables.
To create your own executable, override `Executor` to add functionality to your program, then create children of `Datum` and `UserFunctor` for adding your own data structures and operations.

For example implementations, check out:
 * [apie](https://github.com/eons-dev/bin_apie)
 * [ebbs](https://github.com/eons-dev/bin_ebbs)
 * [emi](https://github.com/eons-dev/bin_emi)

## Design

### Configuration File and Fetch()

eons provides a simple means of retrieving variables from a wide array of places. When you `Fetch()` a variable, we look through:
1. The system environment (e.g. `export some_key="some value"`)
2. The json configuration file supplied with `--config` (or specified by `this.defualtConfigFile` per `Configure()`)
3. Arguments supplied at the command line (e.g. specifying `--some-key "some value"` makes `Fetch(some_key)` return `"some value"`)
4. Member variables of the Executor (e.g. `this.some_key = "some value"`)

The higher the number on the above list, the higher the precedence of the search location. For example, member variables will always be returned before values from the environment.

NOTE: The supplied configuration file must contain only valid json.

### GetRegistered()

In addition to dynamically Fetch()ing variables, eons provides a means of dynamically providing instances of classes by name. These classes can be stored on the filesystem or online.

Additionally, when provisioning SelfRegistering classes, both python package and other SelfRegistering class dependencies will be resolved. This means that, in the course of using this library, your system may be changed in order to provide the requested functionality.

Keep reading for more details.

### Functors

Functors are classes (objects) that have an invokable `()` operator, which allows you to treat them like functions.
eons uses functors to provide input, analysis, and output functionalities, which are made simple by classical inheritance.

For extensibility, all functors take a `**kwargs` argument when called. This allows you to provide arbitrary key word arguments (e.g. key="value") to your objects.

### Self Registration

Normally, one has to `import` the files they create into their "main" file in order to use them. That does not apply when using eons. Instead, you simply have to derive from an appropriate base class and then call `SelfRegistering.RegisterAllClassesInDirectory(...)` (which is usually done for you based on the `repo['store']` and `defaultRepoDirectory` members), providing the directory of the file as the only argument. This will essentially `import` all files in that directory and make them instantiable via `SelfRegistering("ClassName")`.

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

## Extension

When extending a program that derives from eons, defer to that program's means of extension. However, the following utilities may greatly aid in standardizing downstream code.

### User Functor

UserFunctors store all args passed to them in the `kgwargs` member. While you can check this member directly for arguments, `Fetch(...)` is preferred.

When extending `UserFunctor`, please be aware that the following utilities are available to you:
```python
#RETURNS: an opened file object for writing.
#Creates the path if it does not exist.
def CreateFile(this, file, mode="w+"):
    ...

#Copy a file or folder from source to destination.
#This really shouldn't be so hard...
def Copy(this, source, destination):
    ...

#Delete a file or folder
def Delete(this, target):
    ...

#Run whatever.
#DANGEROUS!!!!!
#RETURN: Return value and, optionally, the output as a list of lines.
#per https://stackoverflow.com/questions/803265/getting-realtime-output-using-subprocess
def RunCommand(this, command, saveout=False, raiseExceptions=True):
    ...
```
The source for these methods is available in UserFunctor.py.
