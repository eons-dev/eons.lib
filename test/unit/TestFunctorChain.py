from StandardTestFixture import StandardTestFixture

class TestFunctorChainFixture(StandardTestFixture):

	def test_simple_hello(this):
		simpleHello = this.executor.Execute('HelloFunctor')
		assert (simpleHello == "HelloFunctor says hello to you")

	# Inheritance test: make sure Hello() is inherited normally.
	def test_friend_hello(this):
		friendlyHello = this.executor.Execute('FriendFunctor', 'Best')
		assert (friendlyHello == "FriendFunctor says hello to its Best Friend")

	# Only the last Functor to be Executed should be returned.
	# This chain should satisfy EnemyFunctor's requiredMethod 'Hello'
	def test_enemy_hello(this):
		enemyHello = this.executor.Execute('HelloFunctor', enemy='Worst', next=['EnemyFunctor'])
		assert (enemyHello == "EnemyFunctor says hello to its Worst Enemy")
