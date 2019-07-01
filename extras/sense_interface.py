from sense_hat import SenseHat

class sense_interface(object):
    def __init__(self):
        
        X = [255, 255, 255]  # White
        O = [0, 0, 0]        # Black
        self.green = [0, 255, 0]  # Green
        self.blue = [0, 0, 255]   # Blue
        self.sense_light = True
        
        self.tc_symbol = [
            O, O, O, O, O, O, O, O,
            X, X, X, O, O, X, O, O,
            O, X, O, O, X, O, X, O,
            O, X, O, O, X, O, O, O,
            O, X, O, O, X, O, O, O,
            O, X, O, O, X, O, X, O,
            O, X, O, O, O, X, O, O,
            O, O, O, O, O, O, O, O
            ]
        self.error_letter = "?"

        sense_3 = [
            X, X, X, X, X, X, X, X,
            X, O, O, O, O, O, O, X,
            X, O, O, O, O, O, O, X,
            X, O, O, O, O, O, O, X,
            X, O, O, O, O, O, O, X,
            X, O, O, O, O, O, O, X,
            X, O, O, O, O, O, O, X,
            X, X, X, X, X, X, X, X
            ]

        sense_2 = [
            O, O, O, O, O, O, O, O,
            O, X, X, X, X, X, X, O,
            O, X, O, O, O, O, X, O,
            O, X, O, O, O, O, X, O,
            O, X, O, O, O, O, X, O,
            O, X, O, O, O, O, X, O,
            O, X, X, X, X, X, X, O,
            O, O, O, O, O, O, O, O
            ]

        sense_1 = [
            O, O, O, O, O, O, O, O,
            O, O, O, O, O, O, O, O,
            O, O, X, X, X, X, O, O,
            O, O, X, O, O, X, O, O,
            O, O, X, O, O, X, O, O,
            O, O, X, X, X, X, O, O,
            O, O, O, O, O, O, O, O,
            O, O, O, O, O, O, O, O 
            ]

        sense_0 = [
            O, O, O, O, O, O, O, O,
            O, O, O, O, O, O, O, O,
            O, O, O, O, O, O, O, O,
            O, O, O, X, X, O, O, O,
            O, O, O, X, X, O, O, O,
            O, O, O, O, O, O, O, O,
            O, O, O, O, O, O, O, O,
            O, O, O, O, O, O, O, O
            ]

        self.sense_vector = (sense_0, sense_1, sense_2, sense_3)

        self.sense_count = len(self.sense_vector)
        self.count = 0

        self.sense = SenseHat()
	self.error()

    def error(self):
        self.sense.show_letter(self.error_letter)

    def sense_sensor_string(self):
        #this function reads the sense data and prepares a string
        temp     = self.sense.get_temperature()
        humidity = self.sense.get_humidity()
        pressure = self.sense.get_pressure()

        sensor_data = '{:.1f}'.format(humidity) + '\t' + '{:.1f}'.format(temp) + '\t' + '{:.1f}'.format(pressure)
        return sensor_data

    def increase(self):
        self.count = self.count + 1
        if self.count == len(self.sense_vector):
            self.count = 0
        self.sense.set_pixels(self.sense_vector[self.count])

    def decrease(self):
        self.count = self.count - 1
        if self.count < 0:
            self.count = len(self.sense_vector) - 1
        self.sense.set_pixels(self.sense_vector[self.count])
