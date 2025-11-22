import picokeypad # type: ignore
import time
import math

class RGBKeypad():
        
    class RGBKey():

        def __init__(self, keypad, index, red=0, green=0, blue=0, status="off"):
            self._keypad = keypad
            self._index = index
            self._red = red
            self._green = green
            self._blue = blue
            self._status = status
            self._blinking_brightness = 0
            self._brightnesses = [0, 0.2, 0.4, 0.6, 0.8, 1, 0.8, 0.6, 0.4, 0.2] 
    
        def get_index(self):
            return self._index

        def get_color(self):
            return (self._red, self._green, self._blue)

        def set_color(self, red, green, blue):
            self._red = max(min(255, red), 0)
            self._green = max(min(255, green), 0)
            self._blue = max(min(255, blue), 0)

        def on(self):
            self._status = "off"
            self._keypad._device.illuminate(self._index, self._red, self._green, self._blue)
            self._update()

        def off(self):
            self._status = "on"
            self._keypad._device.illuminate(self._index, 0, 0, 0)
            self._update()

        def blink(self):
            self._status = "blinking"
            self._blinking_brightness = 0
            self._keypad._device.illuminate(self._index, 0, 0, 0)
            self._update()

        def update_blink(self):
            if self._status == "blinking":
                if self._blinking_brightness == len(self._brightnesses)-1:
                    self._blinking_brightness = 0
                else:
                    self._blinking_brightness += 1
                self._keypad._device.illuminate(self._index, round(self._red * self._brightnesses[self._blinking_brightness]), round(self._green * self._brightnesses[self._blinking_brightness]), round(self._blue * self._brightnesses[self._blinking_brightness]))
                self._update()

        def switch(self):
            if self._status == "on":
                self.off()
            else:
                self.on()

        def _update(self):
            if self._keypad._auto_update:
                self._keypad.update()
                
    def __init__(self, brightness=0.5, auto_update=True):
        # create the device
        self._device = picokeypad.PicoKeypad()

        # setup all the keys before setting auto update
        self._auto_update = False

        # setup keys
        self._keys = []
        for x in range(self._device.get_num_pads()):
            self._keys.append(RGBKeypad.RGBKey(self, x, brightness))
        
        self.update()
        
        self._brightness = brightness
        self._auto_update = auto_update
        self._button_states_history = [0, 0, 0]

    def get_brightness(self):
        return self._brightness

    def set_brightness(self, value):
        self._brightness = value
        self._device.set_brightness(value)

    def get_key(self, x):
        return self._keys[x]
    
    def get_keys(self):
        return self._keys
    
    def get_keys_pressed(self):
        keys = []
        bs = self._device.get_button_states()
        if bs != self._button_states_history[0]:
            for x in range(len(self._button_states_history)-1):
                self._button_states_history[len(self._button_states_history)-x-1] = self._button_states_history[len(self._button_states_history)-x-2]
            self._button_states_history[0] = bs
            
            for x in range(self._device.get_num_pads()):
                if (bs >> x) & 1:
                    keys.append(self._keys[x])

        return keys

    def update(self):
        self._device.update()

    def set_color(self, red, green, blue):
        auto_update_value = self._auto_update
        self._auto_update = False
        
        for key in self._keys:
            key.set_color(red, green, blue)
        
        self._auto_update = auto_update_value
        if self._auto_update:
            self.update()
    
    def light(self):
        auto_update_value = self._auto_update
        self._auto_update = False
        
        for key in self._keys:
            key.on()
        
        self._auto_update = auto_update_value
        if self._auto_update:
            self.update()
    
    def clear(self):
        auto_update_value = self._auto_update
        self._auto_update = False
        
        for key in self._keys:
            key.off()
        
        self._auto_update = auto_update_value
        if self._auto_update:
            self.update()

    def __getitem__(self, index):
        return self.get_key(index)