from .Utils import util

# BackwardsCompatible classes simply map old names to new names.
# The more compatible an object, the slower it is to access.
# Compatibility can be adjusted by changing the compatibility member variable.
# Compatibility values are versions in accordance with the eons versioning convention: https://eons.llc/convention/versioning
class BackwardsCompatible:

	def __init__(this, compatibility = 2.0):
		# How much backwards compatibility should be maintained.
		# compatibility value is the lowest version of eons that this Functor is compatible with.
		# Compatibility is usually handled in the SupportBackwardsCompatibility method.
		this.compatibility = float(compatibility)

		this.compatibilities = {}

		# Anything that needs to be cached.
		this.cache = util.DotDict()

		# Accelerate backwards compatible lookups.
		# NOTE: this is inverted from this.compatibilities for faster lookup of the new name given the old name.
		this.cache.compatibilities = {}


	# Store a mapping of old names to new names for a particular version.
	def MaintainCompatibilityFor(this, version, compatibilities):
		version = str(version)
		if (version not in this.compatibilities):
			this.compatibilities[version] = {}
		this.compatibilities[version].update(compatibilities)

		this.cache.compatibilities = {}
		for comp in [
			comp
			for ver, comp in this.compatibilities.items()
			if float(ver) <= this.compatibility
		]:
			for new, old in comp.items():
				this.cache.compatibilities[old] = new


	# Support backwards compatibility, to an extent.
	# NOTE: This may cause unwanted type conversions.
	def Get(this, var):
		return eval(f"this.{this.cache.compatibilities[var]}")