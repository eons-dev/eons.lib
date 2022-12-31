import logging
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT
from .Functor import Functor
from .Method import method

# The standard Functor extends Functor to add a set of standard members and methods.
# This is similar to the standard library in C and C++
# You must inherit from *this if you would like to use the functionality *this provides. The methods defined will not be propagated.
class StandardFunctor(Functor):
	def __init__(this, name="Standard Functor"):
		super().__init__(name)

	# Override this and do whatever!
	# This is purposefully vague.
	def Function(this):
		pass


	# Undo any changes made by UserFunction.
	# Please override this too!
	def Rollback(this):
		pass


	# Override this to check results of operation and report on status.
	# Override this to perform whatever success checks are necessary.
	def DidFunctionSucceed(this):
		return this.functionSucceeded


	# RETURN whether or not the Rollback was successful.
	# Override this to perform whatever success checks are necessary.
	def DidRollbackSucceed(this):
		return this.rollbackSucceeded


	######## START: UTILITIES ########

	# RETURNS: an opened file object for writing.
	# Creates the path if it does not exist.
	@method()
	def CreateFile(this, file, mode="w+"):
		Path(os.path.dirname(os.path.abspath(file))).mkdir(parents=True, exist_ok=True)
		return open(file, mode)

	# Copy a file or folder from source to destination.
	# This really shouldn't be so hard...
	# root allows us to interpret '/' as something other than the top of the filesystem.
	@method()
	def Copy(this, source, destination, root='/'):
		if (source.startswith('/')):
			source = str(Path(root).joinpath(source[1:]).resolve())
		else:
			source = str(Path(source).resolve())
		
		destination = str(Path(destination).resolve())
		
		Path(destination).parent.mkdir(parents=True, exist_ok=True)

		if (os.path.isfile(source)):
			logging.debug(f"Copying file {source} to {destination}")
			try:
				shutil.copy(source, destination)
			except shutil.Error as exc:
				errors = exc.args[0]
				for error in errors:
					src, dst, msg = error
					logging.debug(f"{msg}")
		elif (os.path.isdir(source)):
			logging.debug(f"Copying directory {source} to {destination}")
			try:
				shutil.copytree(source, destination)
			except shutil.Error as exc:
				errors = exc.args[0]
				for error in errors:
					src, dst, msg = error
					logging.debug(f"{msg}")
		else:
			logging.error(f"Could not find source to copy: {source}")

	# Delete a file or folder
	@method()
	def Delete(this, target):
		if (not os.path.exists(target)):
			logging.debug(f"Unable to delete nonexistent target: {target}")
			return
		if (os.path.isfile(target)):
			logging.debug(f"Deleting file {target}")
			os.remove(target)
		elif (os.path.isdir(target)):
			logging.debug(f"Deleting directory {target}")
			try:
				shutil.rmtree(target)
			except shutil.Error as exc:
				errors = exc.args[0]
				for error in errors:
					src, dst, msg = error
					logging.debug(f"{msg}")

	# Run whatever.
	# DANGEROUS!!!!!
	# RETURN: Return value and, optionally, the output as a list of lines.
	@method()
	def RunCommand(this, command, saveout=False, raiseExceptions=True):
		logging.debug(f"================ Running command: {command} ================")
		p = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
		output = []
		while p.poll() is None:
			line = p.stdout.readline().decode('utf8')[:-1]
			if (saveout):
				output.append(line)
			if (line):
				logging.debug(f"| {line}")  # [:-1] to strip excessive new lines.

		if (p.returncode is not None and p.returncode):
			raise CommandUnsuccessful(f"Command returned {p.returncode}: {command}")
		
		logging.debug(f"================ Completed command: {command} ================")
		if (saveout):
			return p.returncode, output
		
		return p.returncode
	######## END: UTILITIES ########
