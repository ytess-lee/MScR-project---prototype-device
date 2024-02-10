import sys
import time
import glob
from threading import Thread, Lock
import threading
import serial 
from icecream import ic
import inquirer
import os, signal

# change the #define XYZ_SPEED in arduino IDE
# this program will:
# establish serial communication with arduino, initiate the stepper motor at speed set in arduino
# use python to control pump operation modes, stop, pause, resume
# with a countdown timer to stop the pump operation
# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
# HAPPY CLASS
# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
class SyringePumpController:
    # declaring start, mid, and end marker as class attributes for sending code to Arduino
    startMarker = 60# <
    endMarker = 62  # ,F,0.0>
    midMarker = 44 # ,
    syringe_area = 163.539454 # surprisingly change this does nothing to the speed either
    unit = "µl/s" # speed would be constant if changed the unit to ul/min
    microsteps = 1
    
    def __init__(self, port=None, baudrate = 230400):  
        try: 
            self.serial = serial.Serial(port, baudrate) # opens serial connection and connects to arduino
        except serial.SerialException as se:
            raise RuntimeError(f"Failed to open serial port. Error: {se}")
        
        self.p1_is_active = False
        self.p1_is_paused = False
        self.p1_speed = 0
        self.new_speed = 0

        self.waiting_for_reply = False # making it an instance variable instead of a local variable in the 'send_single_command' function so that it won't lead to unexpected behaviour when called multiple times
        self.run = True
  
        self.p1_amount = 0
        self.p1_accel = 0
        self.p1_speed_to_send = 0
        self.p1_accel_to_send = 0
        
        self.countdown_stop_event = threading.Event() 
        # create an instance of event class, acts as a signal to stop the countdown
        # when the countdown needs to be stopped, self.countdown_stop_event.set() is called, set the internal flag of the Event to true
        # signal the countdown thread that it should stop counting down and perform any cleanup or termination tasks
        # where self.countdown_stop_event.is_set() is used to CHECK the internal flag == T/False
        # often used with loops to check whether the event has been set
  
# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
# SETUP
# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
    def populate_ports(self):
        print("Populating ports...")
        
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)] 
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')
        
        result = []
        for port in ports:
            try: 
                s = serial.Serial(port) 
                s.close() 
                result.append(port)
            except (OSError, serial.SerialException):
                pass 
        return result

    def thread_finished(self):
        print("Your thread has completed. Now terminating..")
        self.run = False
        print("Thread has been terminated.")
        print("=============================\n\n")
        # here is where you need to end the thread

    def countdown_timer(self, duration_in_min):
        p1_duration = duration_in_min * 60
        end_time = time.time() + p1_duration
        self.remaining_time = p1_duration # store teh remaining time as an instance
        
        while time.time() < end_time and not self.countdown_stop_event.is_set(): # if set==false, timer still running 
            if self.p1_is_paused == True: # this block is somehow not run,  prob something up with threading
                print("Countdown paused.")
                while self.p1_is_paused == True and not self.countdown_stop_event.is_set(): # wait in the loop as long as the pump is paused and stop event is not set
                    time.sleep(1)
                print("Resuming countdown.")
                
            remaining_time = int(end_time - time.time())
            minutes, seconds = divmod(remaining_time, 60)
            print(f"Time remaining: {minutes:02d}:{seconds:02d}", end="\r")
            
            time.sleep(1)
            self.remaining_time = remaining_time
            
        if not self.countdown_stop_event.is_set(): # if it's not been set then the countdown timer completes without being stopped
            print("Time's up!")
            self.stop_pump()
            
    def stop(self):
        self.run = False
        
    def send_ctrl_c(self):
        try:
            os.kill(os.getpid(), signal.SIGINT)
            sys.exit()
        except Exception as e:
            print(f"Error sending Ctrl+C: {e}")

# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
# PROMPTs
# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬   
    
    def mode_prompt(self, question):
        with threading.Lock(): # lock out the critical section to prevent race condition
            question = [inquirer.List('mode',
                                    
                        message="Mode of actions:",
                        choices=['STOP', 'PAUSE OR RESUME', 'CONTINUE'],
                        ),
            ]
            answers = inquirer.prompt(question)
            if answers['mode'] == 'STOP':
                executeSTOP = self.stop_pump()
                return executeSTOP #=None
            elif answers['mode'] == 'PAUSE OR RESUME':
                executePAUSE_RESUME = self.pause_resume_pump()
                return executePAUSE_RESUME # =None
            else:
                pass
    
    # to handle mode promopt in a separate thread
    def handle_mode_prompt(self):
        with threading.Lock(): # ensure thread safety when calling input
            print(self.mode_prompt('mode'))
# ¬¬¬¬¬¬¬¬¬¬¬¬
# (SEND) SETTINGS
# ¬¬¬¬¬¬¬¬¬¬¬¬
    def set_p1_amount(self): # distance travel/ displacement
        self.p1_amount = 50000000000
        print(f"The total volume per pump operation is set to {self.p1_amount} µl.")
        return self.p1_amount

    def set_p1_speed(self):
        while True:
            try:
                self.p1_speed = 50
                print(f"Pump speed is set to {self.p1_speed} µl/min.")
                self.p1_speed_to_send = self.convert_speed(self.p1_speed, self.unit, self.syringe_area, self.microsteps)
                break
            except ValueError:
                print("Invalid input. Try again.")
        return self.p1_speed_to_send
    
    def send_p1_speed_setting(self):
        self.p1_settings = f"<SETTING,SPEED,123," + str(self.p1_speed_to_send) + ",F,0.0,0.0,0.0>"

        print("Sending P1 SPEED SETTINGS...")
        thread = Thread(target=self.runTest, args=([self.p1_settings],))
        thread.start()
        thread.join()
        print("P1 SPEED SETTINGS sent.")
        
    def set_p1_accel(self):
        self.p1_accel = 50
        self.p1_accel_to_send = self.convert_accel(self.p1_accel, self.unit, self.syringe_area, self.microsteps)
        return self.p1_accel_to_send
    
    def send_p1_accel_setting(self):
        self.p1_settings = f"<SETTING,ACCEL,123," + str(self.p1_accel_to_send) + ",F,0.0,0.0,0.0>"

        print("Sending P1 ACCEL SETTINGS...")
        thread = Thread(target=self.runTest, args=([self.p1_settings],))
        thread.start()
        thread.join()
        print("P1 ACCEL SETTINGS sent.")
  
    def send_p1_jog_setting(self):
        self.p1_setup_jog_delta_to_send = 0
        self.p1_settings = f"<SETTING,DELTA,123," + str(self.p1_setup_jog_delta_to_send) + ",F,0.0,0.0,0.0>"
        print("Sending P1 JOG SETTINGS...")
        thread = Thread(target=self.runTest, args=([self.p1_settings],))
        thread.start()
        thread.join()
        print("P1 JOG SETTINGS sent.")
  
    def send_p1_settings(self):
        print("Sending P1 SETTINGS...")
        self.set_p1_speed()
        self.send_p1_speed_setting()
        self.set_p1_accel()
        self.send_p1_accel_setting()
        #self.send_p1_jog_setting()
        print("ALL P1 SETTINGS sent.")
  
# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
# CONVERSION & MATHS
# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
    def convert_displacement(self, displacement, unit, syringe_area, microsteps):
        unit = SyringePumpController.unit
        syringe_area = SyringePumpController.syringe_area    
        microsteps = SyringePumpController.microsteps
        length = unit.split("/")[0]
        time = unit.split("/")[1]
        input_displacement = displacement 
        # convert length
        if length == "mm":
            displacement = self.mm2steps(displacement, microsteps)
        elif length == "ml":
            displacement = self.ml2steps(displacement, syringe_area, microsteps)
        elif length == "µl":
            displacement = self.ul2steps(displacement, syringe_area, microsteps)

        
        print('______________________________')
        print("INPUT  DISPLACEMENT: " + str(input_displacement) + ' ' + length)
        print("OUTPUT DISPLACEMENT: " + str(displacement) + ' steps')
        print('\n############################################################\n')
        return displacement
    
    # not sure if this function is necessary, it's used as part of the setting strings that are sent to arduino
    def convert_speed(self, p1_speed, unit, syringe_area, microsteps):
        unit = SyringePumpController.unit
        syringe_area = SyringePumpController.syringe_area    
        microsteps = SyringePumpController.microsteps
        length = unit.split("/")[0]
        time = unit.split("/")[1]
        speed = 0
        
        if length == "mm":
            speed = self.mm2steps(p1_speed, microsteps)
        elif length == "ml":
            speed = self.ml2steps(p1_speed, syringe_area, microsteps)
        elif length == "µl":
            speed = self.ul2steps(p1_speed, syringe_area, microsteps)

        if time == "s":
            pass
        elif time == "min":
            speed = self.permin2persec(speed)
            
        print('______________________________')   
        print("INPUT  SPEED: " + str(p1_speed) + ' ' + unit)
        print("OUTPUT SPEED: " + str(speed) + ' steps/s')
        return speed   

    def convert_accel(self, accel, unit, syringe_area, microsteps):
        unit = SyringePumpController.unit
        syringe_area = SyringePumpController.syringe_area    
        microsteps = SyringePumpController.microsteps
        length = unit.split("/")[0]
        time = unit.split("/")[1]
        inp_accel = accel
        accel = accel

        # convert length first
        if length == "mm":
            accel = self.mm2steps(accel, microsteps)
        elif length == "mL":
            accel = self.ml2steps(accel, syringe_area, microsteps)
        elif length == "µl":
            accel = self.ul2steps(accel, syringe_area, microsteps)

        # convert time next
        if time == "s":
            pass
        elif time == "min":
            accel = self.permin2persec(self.permin2persec(accel))

        print('______________________________')
        print("INPUT  ACCEL: " + str(inp_accel) + ' ' + unit + '/' + time)
        print("OUTPUT ACCEL: " + str(accel) + ' steps/s/s')
        return accel
    
    def steps2mm(self, steps, microsteps):
    # 200 steps per rev
    # one rev is 0.8mm dist
        #mm = steps/200/32*0.8
        mm = steps/200/microsteps*0.8
        return mm

    def steps2ul(self, steps, syringe_area):
        ul = self.mm32ul(self.steps2mm(steps)*syringe_area)
        return ul
    
    def mm32ul(self, mm3): # mm3 = ul
        return mm3    
    
    def ul2steps(self, ul, syringe_area, microsteps):
        syringe_area = 163.539454
        microsteps = 1
        steps = ((ul/syringe_area)/0.8)*200*microsteps
        # ul == mm3, mm3/mm2 = mm, mm/0.8 = rev, #rev * 200 = total steps
        #self.mm2steps(self.ul2mm3(ul)/ syringe_area, microsteps)
        return steps
    
    def mm2steps(self, mm, microsteps):
        steps = (mm/ 0.8) * 200 * microsteps
        return steps   
     
    def ul2mm3(self, ul):
        return ul
    
    def ml2steps(self, ml, syringe_area, microsteps):
        # note syringe_area is in mm^2
        steps = self.mm2steps(self.ml2mm3(ml)/syringe_area, microsteps)
        return steps

    def ml2mm3(self, ml):
        return ml*1000.0

    def permin2persec(self, value_per_min):
        value_per_sec = value_per_min/60.0
        return value_per_sec
   
# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
#	'''
#		Syringe Volume (mL)	|		Syringe Area (mm^2)
#	-----------------------------------------------
#		1				|			17.34206347
#		3				|			57.88559215
#		5				|			112.9089185
#		10				|			163.539454
#		20				|			285.022957
#		30				|			366.0961536
#		60				|			554.0462538
#
# IMPORTANT: These are for BD Plastic syringes ONLY!! Others will vary.
#¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬

# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
# CONTROLLER
# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
    def start_pump(self): 
        if self.p1_is_active == False: 
            print("You clicked START")
            self.p1_is_active = True
            self.set_p1_amount()
            p1_input_displacement =  str(self.convert_displacement(self.p1_amount, self.unit, self.syringe_area, self.microsteps))
            run_cmd = f"<RUN,DIST,123,0.0,F,{p1_input_displacement},{p1_input_displacement},{p1_input_displacement}>" 
            #"<RUN,DIST,"+123+",0.0,F," + p1_input_displacement + "," + p1_input_displacement + "," + p1_input_displacement + ">"
            #
            print("Sending START command...")
            
            thread = Thread(target=self.runTest, args=([run_cmd], )) 
            thread.start() # starts thread
            thread.join()
            print("START command sent.\n")		
            

        else:
            print("No pump available.")
            
   
    def stop_pump(self): 
        if self.p1_is_active == True:
            if not self.p1_is_paused:
                stop_cmd = f"<STOP,BLAH,BLAH,BLAH,F,0.0,0.0,0.0>" 
                self.p1_is_active = False
                print('Sending STOP command...')
    
                thread = Thread(target=self.send_single_command, args=(stop_cmd, )) 
                thread.start()
                thread.join()
                print("STOP command sent.")
                time.sleep(1)
                self.close_connection()
                
            else:
                print("Pump is currently paused. You may want to resume before stopping or press Ctrl + c to exit.")
   
    def pause_resume_pump(self):
        if self.p1_is_active and (self.p1_is_paused == False):
            print("You clicked PAUSE.\n")
            self.p1_is_paused = True
            self.countdown_stop_event.set() # signal the countdown timer to stop, not sure why it doesnt trigger countdown timer
            
            pause_cmd = f"<PAUSE,BLAH,123,BLAH,F,0.0,0.0,0.0>" # "<PAUSE,BLAH," + pumps_2_run + ",BLAH,F,0.0,0.0,0.0>"
            print("Sending PAUSE command...\n")
   
            thread = Thread(target=self.runTest, args=([pause_cmd], )) 
            thread.start()
            thread.join()
            print("PAUSE command sent.\n\n")
            print("Countdown timer paused.")
    
            change_speed = 0
            while change_speed not in [1, 2]: # enter loop if user enter anything but 1 or 2
                try:
                    change_speed = int(input("Do you wish to change the speed? \n (1) Change speed \n (2) RESUME with current speed \n"))
                except ValueError:
                    print("Invalid input. Please enter 1 or 2.")
                                  
            if change_speed == 1:  
                self.change_speed_during_pause()
                
            elif change_speed ==2:
                self.resume_pump_current_speed()
                
    def change_speed_during_pause(self): 
        self.new_speed = float(input("Enter the new speed (µl/min): "))
        print(f"The updated speed is: {self.new_speed} µl/min.\n")
        self.p1_new_speed_to_send = self.convert_speed(self.new_speed, self.unit, self.syringe_area, self.microsteps)
        self.p1_new_speed_settings = f"<SETTING,SPEED,123," + str(self.p1_new_speed_to_send) + ",F,0.0,0.0,0.0>"

        print("Sending UPDATED P1 SPEED SETTINGS...")
        thread = Thread(target=self.runTest, args=([self.p1_new_speed_settings], ))
        thread.start()
        thread.join()
        print("UPDATED P1 SPEED SETTINGS sent.")
                
        resume_cmd = "<RESUME,BLAH,123,BLAH,F,0.0,0.0,0.0>"
        self.resume_after_pause(resume_cmd)

    def resume_pump_current_speed(self):
        
        print(f"The current speed is {self.p1_speed} µl/min.\n")
        resume_cmd = "<RESUME,BLAH,123,BLAH,F,0.0,0.0,0.0>"
        print(f"Sending RESUME command with {self.p1_speed} µl/min...\n") # same speed setting
        
        self.resume_after_pause(resume_cmd)
        
        
    def resume_after_pause(self, resume_cmd):
        thread = Thread(target=self.runTest, args=([resume_cmd], )) 
        thread.start() # starts thread
        thread.join()
        self.p1_is_paused = False
        print("RESUME command sent.\n\n")
        self.mode_prompt('mode') # will keep asking until the timer's up
        

# ¬¬¬¬¬¬¬¬¬¬¬¬¬
# RUN
# ¬¬¬¬¬¬¬¬¬¬¬¬¬
    def run_exp(self, p1_input_duration):
        self.send_p1_settings()
        self.start_pump() # and start counting down
        
        # countdown timer thread
        countdown_thread = threading.Thread(target=self.countdown_timer, args=(p1_input_duration, ))
        countdown_thread.start()
        
        # mode_prompt thread
        mode_thread = threading.Thread(target=self.handle_mode_prompt)
        mode_thread.start()

        countdown_thread.join()
        mode_thread.join()
    
    # close serial connection
    def close_connection(self):
        self.thread_finished()
        print("Disconnecting from board...")
        self.serial.close()
        print('Serial connection closed.')
        self.send_ctrl_c()

# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
# COM WITH ARDUINO BOARD 
# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬ 
    def sendToArduino(self, sendStr):
        try:
            self.serial.write((sendStr + '\n').encode())
            self.serial.flushInput() # to clear the input after sending the command

        except Exception as e:
            print(f"Error sending data to Arduino: {e}")

# it is responsible for reading and processing data from the arduino board, and it's designed to work in conjuction
# with the overall communication flow in the script
# particularly tailored to handle data transmission that involves start, middle and end markers

    def recvPositionArduino(self): # use with runTest to wait for replies
        ck = "" # retain the data between function calls, could be used to accumulate data across multiple sets or used for other purposes outside the loop
        x = "z" # any value that is not an end- or startMarker

        try:
            while  ord(x) != self.startMarker:
                x = self.serial.read()

            # enters a loop that save data until the end marker is found
            while ord(x) != self.endMarker:
                if ord(x) == self.midMarker: # print the current data (ck) to the console if x is equal to midMarker
                    print(ck)
                    ck = "" # initialise here just to store the strings generated in the loop, it's cleared and reused for each set of data

                if ord(x) != self.startMarker: # ensure that the start marker itself is not included in the collected data
                    #print(x)
                    ck = ck + x.decode() # if the data is indeed not the start marker, it appends te character to the 'ck' variable after decoding it

                x = self.serial.read() # after processing the current character, it reads the net character from the serial port
            print(ck)
            return(ck)
        
        except Exception as e:
            print(f"Error receiving data from Arduino: {e}")

    #============================
# send a sequence of commands to the arduino board, wait for the board to reponse
# and handle the received data

    def runTest(self, testdata): # test data, take the args = run_cmd, pause_cmd, resume_cmd
        numLoops = len(testdata) # calculates the number of loops needed based on the length of the test data
        waitingForReply = False # whether the script is currently waitinf for a reply from the arduino
        n = 0 # initialises a counter variable n to zero

        while n < numLoops: # enters a loop that iterates as long as n is less than numloops
            teststr = testdata[n] # retrieves the 'n' -th element from the test data and assigns it to the variable  'teststr'

            if waitingForReply == False:
                self.sendToArduino(teststr) # if not waiting then send cmd to arduino
                print("Sent from PC -- " + teststr)
                waitingForReply = True

            if waitingForReply == True:
                try:
                    while self.serial.in_waiting == 0: 
                        pass

                    dataRecvd = self.recvPositionArduino() # once data is available, it calls recv() to receive and process the data from the arduino
                    print("Reply Received -- " + dataRecvd)
                    n += 1
                    waitingForReply = False
                except serial.SerialException as se:
                    print(F"Error reading data from Arduino: {se}")
                    self.serial.close()
                    self.serial = None
                    waitingForReply = False



            time.sleep(0.1)
        print("Send and receive complete\n\n")

# designed to send a cmd to arduino, wait for a reply, and then handle the received data
    def send_single_command(self, cmd):
        with threading.Lock(): # make sure race condition doesn't happen
            self.waiting_for_reply = False

            if self.serial and self.serial.is_open:
                try:
                    self.sendToArduino(cmd)
                    print("Sent from PC -- STR " + cmd)
                    self.waiting_for_reply = True
                except serial.SerialException as se:
                    print(f"Error sending data to Arduino: {se}")
                    self.serial.close()
                    self.serial = None
            else:
                print("Serial port is closed or not available. Cannot send command.")

            if self.waiting_for_reply:
                while self.serial and self.serial.in_waiting == 0:
                    pass

                data_received = self.recvPositionArduino()
                print("Reply Received -- " + data_received)
                self.waiting_for_reply = False
                print("=============================\n\n")
                print(f"Sent a single command: {cmd}.\n")


# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
# MAIN
# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
if __name__ == '__main__':
    try:
        # prompt user to choose a serial port dynamically
        available_ports = SyringePumpController().populate_ports() # first check what sys, then open and close diff ports and make it into a list for user to choose
        if not available_ports:
            raise RuntimeError("No serial ports found.")
        
        print(f"Available ports: {available_ports}")
        port = input(f"Enter the serial port (press Enter for default): ") or available_ports[0]
        print(f"The selected port is: {port}.\n")
                
        pump_controller = SyringePumpController(port='COM3') 
        p1_input_duration = int(input("Enter the duration (min): "))
        pump_controller.run_exp(p1_input_duration)
    
    except Exception as e:
        print(f"An error has occurred: {e}")
        
   # finally:
   #     if 'pump_controller' in locals(): # check the variable of pump_controller exist, and avoid 'NameError' 
   #         pump_controller.close_connection()