import serial
import time
import keyboard


class SyringePumpController:
    def __init__(self, port, baudrate=9600): # need to set baudrate to 9600 on arduino as well
        # creates an instance variable self.ser that represents the serial connection
        # initialises and opens the seria connection using specified port, baudrate and timeout values
        self.ser = serial.Serial(port, baudrate, timeout=1) # timeout duration = 1s for read operations
        self.is_p1_active = False
        self.p1_is_paused = False
        self.coordinate = "absolute"
        self.p1_amount = 0
        self.p1_speed = 0

    def send_command(self, command):
        # encode -> converts resulting strings (START/ STOP/ PAUSE) into bytes
        # self.ser.write -> writes the encoded bytes to the serial port
        self.ser.write((command + '\n').encode())

    def start_pump(self):
        if not self.is_p1_active:
            self.send_command('START')
            self.is_p1_active = True
            print('Pump started.')

    def stop_pump(self):
        if self.is_p1_active:
            self.send_command('STOP')
            self.is_p1_active = False
            print('Pump stopped.')
            
    def pause_pump(self):
        if self.is_p1_active and not self.p1_is_paused:
            self.send_command('PAUSE')
            self.p1_is_paused = True
    
    def resume_pump(self):
        if self.is_p1_active and self.p1_is_paused:
            self.send_command('RESUME')
            self.p1_is_paused = False

    def set_speed(self, speed_ul_per_min):
        self.send_command(f'SPEED {speed_ul_per_min}')
        self.p1_speed = speed_ul_per_min
        print(f'Speed set to {speed_ul_per_min} ul/min.')

    def run_experiment(self, speed_ul_per_min, duration_sec):
        self.set_speed(speed_ul_per_min)
        self.start_pump()
        time.sleep(duration_sec)
        self.stop_pump()

    def close_connection(self):
        self.ser.close()
        print('Serial connection closed')

if __name__ == '__main__':
    try:
        port = 'COM3'  # for Windows system
        pump_controller = SyringePumpController(port)
        
        # add keybindings
        keyboard.add_hotkey("F1", pump_controller.start_pump)
        keyboard.add_hotkey("F2", pump_controller.stop_pump)
        keyboard.add_hotkey("F3", pump_controller.pause_pump)
        keyboard.add_hotkey("F4", pump_controller.resume_pump)
        
        pump_controller.run_experiment(30, 60)  # Set speed to 30 ul/min and run for 60 seconds
    # catches any exceptions that might occur during the try block and store in variable e
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # check if the variable pump_controller is defined in the local scope
        # and only call close_connection() method when the variable exists in the local scope
        if 'pump_controller' in locals():
            pump_controller.close_connection()
