# Eons python framework

Generalized framework for doing python things.

Design in short: Self-registering functors downloaded just-in-time for use with arbitrary data structures.

## Installation
`pip install eons`

## Usage

This library is intended for consumption by other libraries and executables.
To create your own executable, override `Executor` to add functionality to your program, then create children of `Datum` and `UserFunctor` for adding your own data structures and operations.

For example implementations, check out:
 * [apie](https://github.com/eons-dev/bin_apie)
 * [ebbs](https://github.com/eons-dev/bin_ebbs)
 * [emi](https://github.com/eons-dev/bin_emi)

## Features

Eons supports 3 major features:
* Get inputs to functors by drilling down through multiple layers
* Provide functionality by downloading functors on the fly
* Resolve errors through dynamic resolution by functors

### Inputs Through Configuration File and `Fetch()`

Eons provides a simple means of retrieving variables from a wide array of places. When you `Fetch()` a variable, we look through:
1. The system environment (e.g. `export some_key="some value"`)
2. The json configuration file supplied with `--config` (or specified by `this.defualtConfigFile` per `Configure()`)
3. Arguments supplied at the command line (e.g. specifying `--some-key "some value"` makes `Fetch(some_key)` return `"some value"`)
4. Member variables of the Executor (e.g. `this.some_key = "some value"`)

The higher the number on the above list, the higher the precedence of the search location. For example, member variables will always be returned before values from the environment.

Downstream implementors of the Eons library may optionally extend the `Fetch()` method to look through whatever layers are appropriate for their inputs.

NOTE: The supplied configuration file must contain only valid json.

### Dynamic Functionality via `GetRegistered()`

In addition to dynamically Fetching variables, Eons provides a means of dynamically providing instances of classes by name. These classes can be stored on the filesystem or online through [Eons Infrastructure Technologies](https://infrastructure.tech).

When provisioning SelfRegistering classes (below), both python package and other SelfRegistering class dependencies will be resolved. This means that, in the course of using this library, your system may be changed in order to provide the requested functionality.

When using an Eons Executor, SelfRegistering classes are retrieved with `Executor.GetRegistered(...)`. If the class you are trying to retrieve is not found in the Registered classes, the `ErrorResolution`, `install_from_repo` will try to download a package for the class.

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

### Error Resolution for `@recoverable` Methods

Any method (i.e. member function) of Executor or UserFunctor may be decorated with `@recoverable`. If a `@recoverable` method raises an Exception, the Eons error resolution system will engage and attempt to fix the problem.

Because there are a lot of ways an error might arise and be resolved, we don't give you the same freedom of execution as we do with generic `GetRegistered()` calls. While we use `GetRegistered()` under-the-hood, all possible `ErrorResolutions` have to be specified ahead of time in your Executor's `resolveErrorsWith` list member.

If you want to handle errors with your own `ErrorResolution`, simply call `my_executor.resolveErrorsWith('my_fix_everything_functor')` (paraphrasing).

Creating `ErrorResolutions` is the same as any other functor. The only difference is that when you derive from `ErrorResolution` most of the logic you need has been taken care of for you. You'll just have to implement a `Resolve(this)` method and call `this.ApplyTo(...)` in your constructor.  
NOTE: all ErrorResolution packages should have the `resolve_` prefix so that they may be readily identified online.

Check out [install_from_repo](inc/resolve/resolve_install_from_repo.py) for an example.

## Performance

At Eons, we always prefer functionality over performance. This is the same as the whole "don't prematurely optimize" argument. With that said, optimizing is always good and we try to do it as much as possible.

Please let us know if you are hitting any bottlenecks in this or any of our other libraries! 

## Design

Functors. Functors...

### Functors

Functors are classes (objects) that have an invokable `()` operator. This allows you to treat them like functions.
Eons uses functors to provide input, analysis, and output functionalities, which are made simple by classical inheritance.

Imagine you write 2 functions that take inputs `a` and `b`. You can choose to duplicate these inputs, as is the classic means of writing functions: `firstFunction(a, b)` and `secondFunction(a, b)`. However, with functors, you can make `baseFunctor{inputs=[a,b]}` and then simply `firstFunctor(baseFunctor)` and `secondFunctor(baseFunctor)`, thus creating 2 functors with identical inputs. The result of `firstFunctor(a, b) == firstFunction(a, b)` and likewise for the seconds; only, by using functors we've saved ourselves from duplicating code.

### Inputs

For extensibility, all functors take a `**kwargs` argument when called. This allows you to provide arbitrary key word arguments (e.g. key="value") to your objects.

Each functor supports:
* `requiredKWArgs` - the arguments which the functor cannot be called without.
* `staticKWArgs` - also required arguments but which are only `Fetch()`ed once.
* `optionalKWArgs` - arguments which have a default and do not have to be supplied.

All values provided in these members will be populated by calls to `Fetch()`, as described above. This means that if the user calling your functor does not provide, say their password, it can be automatically looked up in the environment variables.

For other supported features, check out [UserFunctor.py](src/UserFunctor.py)


### Self Registration

Normally, one has to `import` the files they create into their "main" file in order to use them. That does not apply when using Eons. Instead, you simply have to derive from an appropriate base class and then call `SelfRegistering.RegisterAllClassesInDirectory(...)` (which is usually done for you based on the `repo['store']` and `defaultRepoDirectory` members), providing the directory of the file as the only argument. This will essentially `import` all files in that directory and make them instantiable via `SelfRegistering("ClassName")`.

Dynamic error resolutions enables this self registration system to work with inheritance as well. This means that, within downloaded functor, you can `from some_module_to_download import my_desired_class` to download another.

#### Example

In some `MyDatum.py` in a `MyData` directory, you might have:
```
import logging
from Eons import Datum
class MyDatum(Datum): #Datum is a useful child of SelfRegistering
    def __init__(this, name="only relevant during direct instantiation"):
        logging.info(f"init MyDatum")
        super().__init__()
```
From our main.py, we can then call:
```
import sys, os
from Eons import SelfRegistering
SelfRegistering.RegisterAllClassesInDirectory(os.path.join(os.path.dirname(os.path.abspath(__file__)), "MyData"))
```
Here, we use `os.path` to make the file path relevant to the project folder and not the current working directory.
Then, from main, etc. we can call:
```
myDatum = SelfRegistering("MyDatum")
```
and we will get a `MyDatum` object, fully instantiated.

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
