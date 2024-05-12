#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
example class to use the controller with asyncio
python>=3.6 is necessary
script is tested on a raspberry pi 3
hayden tested working on pi 2b
requires xpadneo installed with DKMS (go to xpadneo website)
"""
import asyncio, time, sys
from evdev import InputDevice, ff, ecodes, list_devices
import gertbot as gb

devices = [InputDevice(path) for path in list_devices()]
for device in devices:
    print(device.path, device.name, device.phys)

board = 0
for channel in range(0,3): # 3 inclusive
    gb.set_mode(board,channel,gb.MODE_BRUSH)
    gb.set_endstop(board,channel,gb.ENDSTOP_OFF,gb.ENDSTOP_OFF)
    gb.set_brush_ramps(board,channel,gb.RAMP_100,gb.RAMP_100,gb.RAMP_OFF)

class gamepad():
    def __init__(self, file = '/dev/input/event5'):
        #self.event_value = 0
        self.power_on = True
        try:
            self.device_file = InputDevice(file)
        except FileNotFoundError:
            print("Controller not found on /dev/input/event5 ; quitting")
            self.power_on = False
            self.erase_rumble()
            sys.exit()
        self.joystick_left_y = 0 # values are mapped to [-1 ... 1]
        self.joystick_left_x = 0 # values are mapped to [-1 ... 1]
        self.joystick_right_x = 0 # values are mapped to [-1 ... 1]
        self.joystick_right_y = 0
        self.joystick_click_l = False
        self.joystick_click_r = False
        self.trigger_right = 0 # values are mapped to [0 ... 1]
        self.trigger_left = 0 # values are mapped to [0 ... 1]
        self.button_x = False
        self.button_y = False
        self.button_b = False
        self.button_a = False
        self.button_xbox = False
        self.pad_x = 0 # values are -1 for left, 0 for none, 1 for right
        self.pad_y = 0 # values are -1 for down, 0 for none, 1 for up
        self.bumper_l = False
        self.bumper_r = False
        self.select = False
        self.start = False
        # xbox one S controller only supports sine rumble (id 0)
        self.rumble_effect = 0
        self.effect1_id = 0 # light rumble, played continuously
        self.effect2_id = 0 # strong rumble, played once
        self.load_effects()

    def load_effects(self):
        #effect 1, light rumble
        rumble = ff.Rumble(strong_magnitude=0x0000, weak_magnitude=0x500)
        duration_ms = 300
        effect = ff.Effect(ecodes.FF_RUMBLE, -1, 0, ff.Trigger(0, 0), ff.Replay(duration_ms, 0), ff.EffectType(ff_rumble_effect=rumble))
        self.effect1_id = self.device_file.upload_effect(effect)
        # effect 2, strong rumble
        rumble = ff.Rumble(strong_magnitude=0xc000, weak_magnitude=0x0000)
        duration_ms = 200
        effect = ff.Effect(ecodes.FF_RUMBLE, -1, 0, ff.Trigger(0, 0), ff.Replay(duration_ms, 0), ff.EffectType(ff_rumble_effect=rumble))
        self.effect2_id = self.device_file.upload_effect(effect)

    async def read_gamepad_input(self): # asyncronus read-out of events
        max_abs_joystick_left_x = 0xFFFF/2 #32767
        uncertainty_joystick_left_x = 2500 #some sort of idle unregistered threshold in the centre
        max_abs_joystick_left_y = 0xFFFF/2
        uncertainty_joystick_left_y = 2500
        max_abs_joystick_right_x = 0xFFFF/2
        uncertainty_joystick_right_x = 2000
        max_abs_joystick_right_y = 0xFFFF/2
        uncertainty_joystick_right_y = 2000
        max_trigger = 1023

        async for event in self.device_file.async_read_loop():
                if not(self.power_on): #stop reading device when power_on = false
                    break
                if event.type == 3 == ecodes.EV_ABS: # type is analog trigger or joystick or dpad
                    if event.code == ABS_HAT0X: # dpad-x axis event active
                        self.pad_x = event.value
                    if event.code == ABS_HAT0Y: # dpad-y axis event active
                        self.pad_y = -event.value # sensor for y axis is inverted. hardware design.
                        
                    if event.code == ecodes.ABS_Y: # left joystick y-axis
                        if -event.value > uncertainty_joystick_left_y:
                            self.joystick_left_y = (-event.value - uncertainty_joystick_left_y) / (max_abs_joystick_left_y - uncertainty_joystick_left_y + 1)
                        elif -event.value < -uncertainty_joystick_left_y:
                            self.joystick_left_y = (-event.value + uncertainty_joystick_left_y) / (max_abs_joystick_left_y - uncertainty_joystick_left_y + 1)
                        else:
                            self.joystick_left_y = 0
                    elif event.code == ecodes.ABS_X: # left joystick x-axis
                        if event.value > uncertainty_joystick_left_x:
                            self.joystick_left_x = (event.value - uncertainty_joystick_left_x) / (max_abs_joystick_left_x - uncertainty_joystick_left_x + 1)
                        elif event.value < -uncertainty_joystick_left_x:
                            self.joystick_left_x = (event.value + uncertainty_joystick_left_x) / (max_abs_joystick_left_x - uncertainty_joystick_left_x + 1)
                        else:
                            self.joystick_left_x = 0
                    elif event.code == ecodes.ABS_RY: # right joystick y-axis
                        if -event.value > uncertainty_joystick_right_y:
                            self.joystick_right_y = (-event.value - uncertainty_joystick_right_y) / (max_abs_joystick_right_y - uncertainty_joystick_right_y + 1)
                        elif -event.value < -uncertainty_joystick_right_y:
                            self.joystick_right_y = (-event.value + uncertainty_joystick_right_y) / (max_abs_joystick_right_y - uncertainty_joystick_right_y + 1)
                        else:
                            self.joystick_right_y = 0
                    elif event.code == ecodes.ABS_RX: # right joystick x-axis
                        if event.value > uncertainty_joystick_right_x:
                            self.joystick_right_x = (event.value - uncertainty_joystick_right_x) / (max_abs_joystick_right_x - uncertainty_joystick_right_x + 1)
                        elif event.value < -uncertainty_joystick_right_x:
                            self.joystick_right_x = (event.value + uncertainty_joystick_right_x) / (max_abs_joystick_right_x - uncertainty_joystick_right_x + 1)
                        else:
                            self.joystick_right_x = 0
                    elif event.code == ecodes.ABS_RZ: # right trigger
                        self.trigger_right = event.value / max_trigger
                    elif event.code == ecodes.ABS_Z: # left trigger
                        self.trigger_left = event.value / max_trigger
                if (event.type == ecodes.EV_KEY): # type is button
                    if event.code == BTN_X: # button "X" pressed/released
                        self.button_x = bool(event.value)
                    if event.code == BTN_Y: # button "Y" pressed/released
                        self.button_y = bool(event.value)
                    if event.code == BTN_B: # button "B" pressed/released
                        self.button_b = bool(event.value)
                    if event.code == BTN_A: # button "A" pressed/released
                        self.button_a = bool(event.value)
                    if event.code == BTN_TL: # button left trigger pressed/released
                        self.bumper_l = bool(event.value)
                    if event.code == BTN_TR: # button right trigger pressed/released
                        self.bumper_r = bool(event.value)
                    if event.code == BTN_SELECT: # select ?
                        self.select = bool(event.value)
                    if event.code == BTN_START: # start ?
                        self.start = bool(event.value)
                    if event.code == BTN_THUMBR: # right joy click ?
                        self.joystick_click_r = bool(event.value)
                    if event.code == BTN_THUMBL: # left joy click
                        self.joystick_click_l = bool(event.value)
                    if event.code == BTN_MODE:
                        self.button_xbox = bool(event.value)

    async def rumble(self): # asyncronus control of force feed back effects
        repeat_count = 1
        while self.power_on:
            if self.rumble_effect == 1:
                self.device_file.write(ecodes.EV_FF, self.effect1_id, repeat_count)
            elif self.rumble_effect == 2:
                self.device_file.write(ecodes.EV_FF, self.effect2_id, repeat_count)
                self.rumble_effect = 0 # turn of effect in order to play effect2 only once
            await asyncio.sleep(0.2)

    def erase_rumble(self):
        self.device_file.erase_effect(self.effect1_id)

if __name__ == "__main__":

    async def main():
        print("press X to exit script, B stop motors, trigger and joystick right to see analog value")
        while True:
##            if remote_control.joystick_left_y > 0: # move forward!
##                for channel in range(0,1):
##                    gb.set_mode(board, channel, gb.MODE_BRUSH)
##                    gb.pwm_brushed(board, channel, 10000, 100*round(remote_control.joystick_left_y,2))
##                    print(round(remote_control.joystick_left_y,2))
                
            print(" trigger_right = ", round(remote_control.trigger_right,2), "  joystick_right_x = ", round(remote_control.joystick_right_x,2),end="\r")
            if remote_control.button_a:
                remote_control.button_a = False
                print("A BTN")
                gb.move_brushed(board,channel,1)
                gb.move_brushed(board,channel,1)
##            if remote_control.button_y: # turn on light rumble effect
##                remote_control.button_y = False
##                remote_control.rumble_effect = 1
            if remote_control.button_b: # play once strong rumble effect
                remote_control.button_b = False
                gb.stop_all()
            if remote_control.button_x: # stop the script
                print("X BTN")
                remote_control.button_x = False
                remote_control.power_on = False
                remote_control.erase_rumble()
                gb.emergency_stop()
                break
            await asyncio.sleep(0)

    remote_control = gamepad(file = '/dev/input/event5')
    futures = [remote_control.read_gamepad_input(), remote_control.rumble(), main()]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(futures))
    loop.close()
    print(" ")
