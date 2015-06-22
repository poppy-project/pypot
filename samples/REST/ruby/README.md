## Poppy Ruby


### Example use. 

```ruby

$poppy = Poppy.new
$poppy.set_default_motor_positions

$poppy.set_compliant "true"
$poppy.set_compliant "false"

$motor = $poppy.motors["head_z"]

#show the list of registers
$motor.registers

# You can access the registers directly
puts $motor.compliant
# false
$motor.compliant = "true"

## goal_position and goal_speed registers can handle numeric values
$motor.goal_position = 30
$motor.goal_position = -30
```

