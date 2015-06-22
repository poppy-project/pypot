require 'json'
require 'rest-client'
require 'parallel'

require './motor'

class Poppy 

  attr_reader :ip, :port, :url, :motors

  def initialize ip
    @host = ip
    @port = "8080"
    @url = "http://" + @host + ":" + @port  

    init_motors;
  end

  def init_motors
    @motors = Hash.new
    motor_list.each do |motor_name|
      @motors[motor_name] = Motor.new(self, motor_name)
    end 
  end


  def motor_list_text
    RestClient.get @url + '/motor/list.json'
  end

  def motor_list
    JSON.parse(motor_list_text).values[0]
  end

  def to_s
    "Poppy :]"
  end

  def update_motor_registers
    each_motor do |motor|
      motor.update_registers
    end
  end

  def each_motor
    @motors.each_value do |motor|
      yield motor
    end
  end
  
  def set_compliant (is_compliant)
    each_motor do |motor| 
      motor.compliant = is_compliant
    end
  end

  def set_default_motor_positions
    each_motor do |motor| 
      motor.compliant = "false"
      motor.goal_speed = 0
      motor.goal_position = 0
    end

  end

  def set_default_motor_positions_parallel
    Parallel.each(@motors.values) do |motor| 
      motor.compliant = "false"
      motor.goal_speed = 10
      motor.goal_position = 0
    end
  end

  ## Low level for motors ... 
  
  def motor_values (name) 
    RestClient.get @url + '/motor/' + name + '/register/list.json' , {:accept => :json}
  end

  def motor_register_get (motor, register)
    RestClient.get @url + '/motor/' + motor.name + '/register/' + register , {:accept => :json}
  end
  
  def motor_register_list (motor)
    RestClient.get @url + '/motor/' + motor.name + '/register/list.json' , {:accept => :json}
  end

  def send_motor_register (motor, register, value)
    RestClient.post @url + '/motor/' + motor.name + '/register/' + register + '/value.json', value, :content_type => :json 
  end
  
end
