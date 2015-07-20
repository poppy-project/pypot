import pypot.dynamixel 
import threading 
import serial
import time


class RazorSensor(threading.Thread):

    def __init__(self,port="auto"):
        threading.Thread.__init__(self)

        # initialisation of all parameters (aeronautical convention with Z downward)
        # euler angles in degrees
        self._eul = [0.0,0.0,0.0]
        # acceleration not converted
        self._acc = [0.0,0.0,0.0]
        # magnetic field not converted
        self._mag = [0.0,0.0,0.0]
        # attitude rate not converted
        self._gyr = [0.0,0.0,0.0]
        
        # control flag of the main loop
        self._sync = True
        # sampling period of the sensor
        self._dt = 0.01

    
        if port == "auto":
            # get the list of ports
            portList = pypot.dynamixel .get_available_ports(only_free=True)
            #~ print portList
        else:
            portList = [port]

        portList.reverse() #razor USB port often found last, so get a quicker connection
        for port in portList:
            print('Razor trying to connect to '+port+'.')
            try:
                #test the port
                self.serial = serial.Serial(port, 57600,timeout = 0.1)
                time.sleep(3)
                # do not forget to strip the zeros values
                read = self.serial.readline().strip('\x00')
                
                if len(read)>0:
                    #~ print "received ", read
                    if read[0:5] == '#YPR=':
                        print('Razor connected to '+port+'.')
                        return
                self.serial.close()
                
            except serial.SerialException:
                pass

        # no port available or no razor connected
        print('no Razor connected.')
        self.serial = None


# property definition is independant to include conversion later
    @property
    def euler(self):
        return self._eul
  
    @property
    def accelerometer(self):
        return self._acc
    
    @property
    def magnetometer(self):
        return self._mag
  
    @property
    def gyroscope(self):
        return self._gyr
    
    # main loop of the Thread
    def run(self):
        # stop the streaming
        self.serial.write("#o0")
        # wash the streaming (flush does not work)
        line = self.serial.readlines()
        # start to read the euler angles (a=1) a=2 matches with raw data

        toRead = {"euler angles":"#ot#f", "raw data":"#osrt#f"}
        toReadIndex = 0
        while self._sync:
            t0 = time.time()
            #~ print toRead.values()[toReadIndex]
            self.serial.write(toRead.values()[toReadIndex])
            
            toReadIndex +=1
            if toReadIndex==len(toRead):
                toReadIndex = 0

            while time.time()-t0<self._dt:
                # get one line (do not forget to strip the 00 characters)
                line = self.serial.readline().strip('\x00')
                if len(line)>0:
                    #~ print "received ",line
        # if the line is not empty
                    line= line.replace('\r\n','')
        
                    # euler angles
                    if line[0:5]=='#YPR=':
                        line = line.replace('#YPR=','')
                        try:
                            self._eul = map(float,line.split(','))
                        except:
                            print "razor : YPR could not map ",line
                            pass
                    # accelerations
                    if line[0:5]=='#A-R=':
                        line = line.replace('#A-R=','')
                        try:
                            self._acc = map(float,line.split(','))
                        except:
                            print "razor : AR could not map ",line
                            pass
                    # magnetic field
                    if line[0:5]=='#M-R=':
                        line = line.replace('#M-R=','')
                        try:
                            self._mag = map(float,line.split(','))
                        except:
                            print "razor : MR could not map ",line
                            pass
                    # attitude rates
                    if line[0:5]=='#G-R=':
                        line = line.replace('#G-R=','')
                        try:
                            self._gyr = map(float,line.split(','))
                        except:
                            print "razor : GR could not map ",line
                            pass
                else:
                    print "razor: no data received"
       
    def start(self):
        threading.Thread.start(self)
        time.sleep(2) #razor board needs some time to initialize
        
    def stop(self):
        self._sync = False
        #    wait until the main loop is finished
        time.sleep(1)
        self.serial.close()
        print "razor sensor disconnected."
    
    
if __name__ == "__main__":

    rz = RazorSensor()#port="/dev/ttyUSB0")
    rz.start()
    
    print "euler angles ",rz.euler
    print "magnetic field ",rz.magnetometer
    print "acceleration ",rz.accelerometer
    print "gyroscope ",rz.gyroscope
    time.sleep(0.2)
    print "---"
    print "euler angles ",rz.euler
    print "magnetic field ",rz.magnetometer
    print "acceleration ",rz.accelerometer
    print "gyroscope ",rz.gyroscope
    rz.stop()
    
    
    