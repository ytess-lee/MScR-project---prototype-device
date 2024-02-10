#####
# This script is adapted from 20231112 Syringe Pump Controller.py to run a 
# simulated pump controller to debug or test newly added function
######

import time
import keyboard

class MockSyringePumpController:
    def __init__(self, port, baudrate = 9600):
        self.port = port
        self.is_p1_active = False
        self.p1_is_paused = False
       # self.coordinate = "absolute"
        # self.p1_amount = 0
        self.p1_speed = 0
        self.p1_new_speed = 0
    
    # don't need this function for the mock since it doesn't require serial connection to the actual pump, just here to mimic the syringe pump controller send_command function
    #def send_command(self, command):
        #self.ser.write((command + '\n').encode())
    
    def set_p1_speed(self):
        self.p1_speed = self.p1_speed_INPUT.value()
        try:
            p1_speed = float(input("Enter speed for pump: "))
            print(f"Pump speed is set to {p1_speed} ul/ min.")
        except ValueError:
            print("Invalid input. Press F4 to exit.)")

    
    def start_pump(self):
        if not self.is_p1_active:
            print("Simulated pump started.")
            self.is_p1_active = True
            
    def stop_pump(self):
        if self.is_p1_active:
            print("Simulated pump stopped.")
            self.is_p1_active = False
            print("Simulated serial connection closed.")
    
    def pause_pump(self, new_p1_speed=0):
        if self.is_p1_active and not self.p1_is_paused:
            print("Simulated pump paused.")
            self.p1_is_paused = True
            # allow change of speed after pause
            change_speed = int(input("Do you want to change the speed? \n (1) Yes \n (2) No\n"))
            if change_speed == 1:
                new_p1_speed = float(input(f"Change speed to: {new_p1_speed}"))
                self.set_speed(new_p1_speed)
                print(f"The new speed is {new_p1_speed} ul/ min, press F4 to resume.")
            elif change_speed == 2:
                print(f"The current speed is {self.p1_speed}, press F4 to resume.")
            else:
                print("Invalid input, press F4 to resume.")
                            
    def resume_pump(self):
        if self.is_p1_active and self.p1_is_paused:
            print("Simulated pump resumed.")
            self.p1_is_paused = False

            # add scripts that ask if you want to change the speed, if yes then set the new speed, if no then pop up current speed and duration profile
            #new_speed = int(input("Do you want to change the speed: (1) Yes\n (2) No"))
            #if new_speed == 2:
                #print(f"The current speed is {self.p1_speed}, for a total duration of {duration_min} min.")

# can't use self.p1_speed as arg, different self object
    #def set_speed(self, p1_speed):
        #print(f"Simulated speed set to {p1_speed} ul/ min.")
        #self.p1_speed = p1_speed
        
    
    
    
    def set_p1_speed(self):
        try:
            self.p1_speed = float(input("Enter the speed (ul/min): "))
            print(f"Pump speed is set to {self.p1_speed}")
        except ValueError:
            print("Invalid input. Do better next time.")

    def set_speed(self, p1_speed):
        print(f"Simulated speed set to {p1_speed} ul/min.")
        self.p1_speed = p1_speed

        
    def run_experiment(self, p1_speed, duration_min):
        self.set_speed(p1_speed)
        self.start_pump()
        print(" Pump function hotkeys: \n F1: Start\n F2: Stop \n F3: Pause \n F4: Resume")
        time.sleep(duration_min * 60)
        self.stop_pump()
        
    def close_connection(self):
        print("Simulated serial connection closed.")
        

if __name__ == '__main__':
    try:
        port = 'COM3' # change depends on the system
        # p1_speed = float(input("Enter the speed (ul/ min): "))
        duration_min = int(input("Enter the duration (min): "))
        pump_controller = MockSyringePumpController(port) # create an instance to the class and assign to variable pump_controller
        
        # add keybindings
        keyboard.add_hotkey("F1", pump_controller.start_pump)
        keyboard.add_hotkey("F2", pump_controller.stop_pump)
        keyboard.add_hotkey("F3", pump_controller.pause_pump)
        keyboard.add_hotkey("F4", pump_controller.resume_pump)
        pump_controller.set_p1_speed()
        pump_controller.run_experiment(pump_controller.p1_speed, duration_min)
    except Exception as e:
        print(f"An error has occurred: {e}")
    finally:
        if 'pump_controller' in locals(): # check the variable of pump_controller exist, and avoid 'NameError' 
            pump_controller.close_connection()