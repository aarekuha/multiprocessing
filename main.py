from decorators import Decorators
import another


decorators_initializator = Decorators()
print(decorators_initializator.send_command(route="first_route"))
decorators_initializator.stop()
