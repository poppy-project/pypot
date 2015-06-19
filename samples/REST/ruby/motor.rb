
class Motor

  attr_reader :name, :registers
  
  def initialize (robot, motor_name)
    @name = motor_name
    @robot = robot
    load_registers
  end

  def set_name (name)
    @name = name
  end
  
  def load_registers

    @registers = Hash.new
    names = JSON.parse(@robot.motor_register_list self).values[0]
    
    names.each do |name|
      
      next if name == "registers"
      begin 
        value = @robot.motor_register_get(self, name)
        value = JSON.parse(value)
        value = value[name]
        @registers[name] = value

        ## create a function to access this
        instance_variable_set("@#{name}", value)
        self.class.send(:attr_reader, name)

        if is_float_register(name)
          self.class.send(:define_method, name+"=") do |argument|
            puts "Sending value..."
            @robot.send_motor_register(self, name, argument.to_s)
          end
        else
          self.class.send(:define_method, name+"=") do |argument|
            puts "Sending ..."
            @robot.send_motor_register(self, name, argument)
          end

        end
        
      rescue
#        puts "Register not read " + name
      end
    end

#    update_registers
  end

  def is_float_register (name)
    if name == "goal_position" or name == "goal_speed"
      return true
    end
    false
  end
  
  def update_registers
    
    @registers.each do |name, value|
      begin 
        value = @robot.motor_register_get(self, name)
        value = JSON.parse(value)
        value = value[name]
        @registers[name] = value

        instance_variable_set("@#{name}", value)
      rescue
#        puts "Register not read " + name
      end
    end
  end

  ## TODO: custom functions for key functions.
  ## not for the others. 
  
  # def set_compliant (value)
  #   compliant = value
  # end

  # def compliant= (value)
  #   text = "true" if value == true
  #   text = "false" if value == false
  #   @robot.send_motor_register(self, "compliant", text)
  # end

  # def moving_speed= (value)
  #   @robot.send_motor_register(self, "moving_speed", value)
  # end

  # def position= (value)
  #   @robot.send_motor_register(self, "goal_position", value.to_s)
  # end

  # def position
  #   present_position
  # end


  def to_s
    return "Motor: " + @name 
  end
  
#   RestClient.get @url + '/motor/' + name + '/register/list.json' , {:accept => :json}
  
  
  
end


# class Register
#   attr_reader :name 
# end
