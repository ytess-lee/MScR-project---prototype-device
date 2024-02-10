# jog delta - how much the carriage will move (0.1mm/ 1mm), but i don't think it's neccessary



# Microstepping, the stepper motor is Nema 17 Bipolar 45Ncm
# 1 step = 1.8 degree
# 200 steps = 360 degree/ a full revolution
# the original poseidon team got 1/32 microstepping for 1 motor (3 jumpers)
	# 200 steps per rev
	# one rev is 0.8mm dist

 
# Populate the microstepping amounts for the dropdown menu
# I don't think we need this    
	from wsgiref.types import StartResponse	
 
 # Populate the list of possible syringes to the dropdown menus
 # syringe_size = ___ instead of writing a function
	def populate_syringe_sizes(self): 
		self.syringe_options = ["BD 1 mL", "BD 3 mL", "BD 5 mL", "BD 10 mL", "BD 20 mL", "BD 30 mL", "BD 60 mL"]
		self.syringe_volumes = [1, 3, 5, 10, 20, 30, 60]
		self.syringe_areas = [17.34206347, 57.88559215, 112.9089185, 163.539454, 285.022957, 366.0961536, 554.0462538]

		self.ui.p1_syringe_DROPDOWN.addItems(self.syringe_options)
		self.ui.p2_syringe_DROPDOWN.addItems(self.syringe_options)
		self.ui.p3_syringe_DROPDOWN.addItems(self.syringe_options)

# allow changes on the gui
def populate_microstepping(self):
		self.microstepping_values = ['1', '2', '4', '8', '16', '32']
		self.ui.microstepping_DROPDOWN.addItems(self.microstepping_values)
		self.microstepping = 1
``# self.populate_microstepping()

	# Px amount
  # prob don't need this
def connect_all_gui_componets(self):
	self.ui.p1_amount_INPUT.valueChanged.connect(self.set_p1_amount)
	self.ui.p2_amount_INPUT.valueChanged.connect(self.set_p2_amount)
    self.ui.p3_amount_INPUT.valueChanged.connect(self.set_p3_amount)
    
    self.ui.microstepping_DROPDOWN.currentIndexChanged.connect(self.set_microstepping) # Set the microstepping value, default is 1
  
	# Set Px distance to move
	# amount in mm but with the maths it can be translated into ul/ml

	def set_p1_amount(self):
		self.p1_amount = self.ui.p1_amount_INPUT.value() # sets the value of self.p1_amount to the current value of the input widget self.ui.p1_amount_INPUT."""
	def set_p2_amount(self):
		self.p2_amount = self.ui.p2_amount_INPUT.value()
	def set_p3_amount(self):
		self.p3_amount = self.ui.p3_amount_INPUT.value()
  
  # ==================
  # DISPLACEMENT
  # "
  	def run(self):
		self.statusBar().showMessage("You clicked RUN")
		testData = []

		active_pumps = self.get_active_pumps()
		if len(active_pumps) > 0: # change this part to if p1_active == true
			# def convert_displacement(self, displacement, units, syringe_area, microsteps):
			# can take away unit as it's set with our prototype
			# syringe_area = __
			p1_input_displacement = str(self.convert_displacement(self.p1_amount, self.p1_units, self.p1_syringe_area, self.microstepping))

			pumps_2_run = ''.join(map(str,active_pumps)) # then won't need this part 

			cmd = "<RUN,DIST,"+pumps_2_run+",0.0,F," + p1_input_displacement + ">" # can take away the pumps_2_run

			testData.append(cmd) # testData = [<RUN, DIST, 0.0, F, (p1_amount, p1_units, p1_syringe_area, p1_microstepping) >], an array
   # also import thread (read everything once it recieved all data while subprocesses won't wait one by one hence the timeout() added to the script)

			print("Sending RUN command..")
			thread = Thread(self.runTest, testData) # send cmd to run
			thread.finished.connect(lambda:self.thread_finished(thread)) # like f"{} but for function
			thread.start()
			print("RUN command sent.")
		else:
			self.statusBar().showMessage("No pumps enabled.")
   
   #=================
   #    # check if p1 is already active and activates p1 through send_command method
   
   """
   def start_pump(self):
        if self.p1_is_active == False:
            self.send_command('START')
            if self.p1_is_active == True:
				p1_input_displacement = str(self.convert_displacement(self.p1_amount))
            
            
            print('Pump started.')
    .........
    if __name__ == '__main__':
    try:
        port = 'COM3' # change depends on the system
        p1_speed = int(input("Enter the speed (ul/ min): "))
        p1_duration = int(input("Enter the duration (min): ")) # convert number into integer
        pump_controller = SyringePumpController(port) # create an instance to the class and assign to variable pump_controller
        
        # add keybindings
        keyboard.add_hotkey("F1", pump_controller.start_pump)
        keyboard.add_hotkey("F2", pump_controller.stop_pump)
        keyboard.add_hotkey("F3", pump_controller.pause_pump)
        keyboard.add_hotkey("F4", pump_controller.resume_pump)
        
        pump_controller.run_exp(p1_speed, p1_duration)
    except Exception as e:
        print(f"An error has occurred: {e}")
    finally:
        if 'pump_controller' in locals(): # check the variable of pump_controller exist, and avoid 'NameError' 
            pump_controller.close_connection()
    """"
        
  
def convert_displacement(self, displacement, units, syringe_area, microsteps):
		length = units.split("/")[0]
		time = units.split("/")[1]
		inp_displacement = displacement
		# convert length first
		if length == "mm":
			displacement = self.mm2steps(displacement, microsteps)
		elif length == "mL":
			displacement = self.mL2steps(displacement, syringe_area, microsteps)
		elif length == "µL":
			displacement = self.uL2steps(displacement, syringe_area, microsteps)

		print('______________________________')
		print("INPUT  DISPLACEMENT: " + str(inp_displacement) + ' ' + length)
		print("OUTPUT DISPLACEMENT: " + str(displacement) + ' steps')
		print('\n############################################################\n')
		return displacement



# =========
# SPEED TO STEP CONVERSION
# but it doesn't seem like it's doing anything to arduino/ pump though, more like a happy maths situation
# Don't need to add this part, the dev wrote this so that they could use convert_speed function in other functions (ie settings)
# =========
"""def convert_speed(self, inp_speed, units, syringe_area, microsteps):
		length = units.split("/")[0]
		time = units.split("/")[1]


		# convert length first
		if length == "mm":
			speed = self.mm2steps(inp_speed, microsteps)
		elif length == "mL":
			speed = self.mL2steps(inp_speed, syringe_area, microsteps)
		elif length == "µL":
			speed = self.uL2steps(inp_speed, syringe_area, microsteps)


		# convert time next
		if time == "s":
			pass
		elif time == "min":
			speed = self.permin2persec(speed)
		elif time == "hr":
			speed = self.perhour2persec(speed)



		print("INPUT  SPEED: " + str(inp_speed) + ' ' + units)
		print("OUTPUT SPEED: " + str(speed) + ' steps/s')
		return speed"""


# ===============
# MATHS
# ===============

def steps2mm(self, steps, microsteps):
    # 200 step = 1 rev
    # 1 rev = 0.8mm dist
    # steps/ 200 = # of rev
    # # of rev/ (microsteps * 0.8) = dist traveled
    
    mm = (steps/ 2000)/ (microsteps * 0.8)
    return mm

# convert to dist based on syringe area
def steps2uL(self, steps, syringe_area):
    ul = self.mm32ul(self.steps2mm(steps) * syringe_area)
    return ul

def mm2steps(self, mm, microsteps):
    steps = (mm/ 0.8) * 200 * microsteps
    return steps

def ul2steps(self, ul, syringe_area, microsteps):
    steps = self.mm2steps(self.ul2mm3(ul)/ syringe_area, microsteps)
    return steps

def ul2mm3(self, ul):
    return ul

# have alr coded for operating time in min

	# Connect to the Arduino board
	def connect(self):
		#self.port_nano = '/dev/cu.usbserial-A9M11B77'
		#self.port_uno = "/dev/cu.usbmodem1411"
		#self.baudrate = baudrate
		self.statusBar().showMessage("You clicked CONNECT TO CONTROLLER")
		try:
			port_declared = self.port in vars()
			try:
				self.serial = serial.Serial()
				self.serial.port = self.port
				self.serial.baudrate = 230400
				self.serial.parity = serial.PARITY_NONE
				self.serial.stopbits = serial.STOPBITS_ONE
				self.serial.bytesize = serial.EIGHTBITS
				self.serial.timeout = 1
				self.serial.open()
				#self.serial.flushInput()

				# This is a thread that always runs and listens to commands from the Arduino
				#self.global_listener_thread = Thread(self.listening)
				#self.global_listener_thread.finished.connect(lambda:self.self.thread_finished(self.global_listener_thread))
				#self.global_listener_thread.start()