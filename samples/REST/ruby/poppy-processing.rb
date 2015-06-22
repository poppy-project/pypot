# -*- coding: utf-8 -*-
require 'ruby-processing' 
require './poppy'

Processing::Runner
Dir["#{Processing::RP_CONFIG['PROCESSING_ROOT']}/core/library/\*.jar"].each{ |jar| require jar }
Processing::App::SKETCH_PATH = __FILE__


class Sketch < Processing::App

  attr_reader :poppy

  def setup 
    size(800, 600, OPENGL)

    $poppy = Poppy.new "schtroumpf.local"
    @poppy = $poppy
    $motor = @poppy.motors["head_z"]

    
    
  end

  def draw
    background 200
    rect 0, 0, 100, 20

    if mouse_y < 20 and mouse_x < 100
      ellipse mouse_x, mouse_y, 10, 10
    end

    
  end 

  def mouse_dragged
    if mouse_y < 20
      $motor.goal_position = mouse_x - 50   if mouse_x < 100    
    end 
  end

end


Sketch.new unless defined? $app
