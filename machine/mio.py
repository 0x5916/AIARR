from typing import Literal
import RPi.GPIO as GPIO

cpr_press = 26  # cpr 
cpr_press_low = 20
# air_pump = 3
# air_pump_low = 19
air_pump = 16
air_pump_low = 21
cpr_up = 23
cpr_down = 22
# cam_up = 22
# cam_down = 23
press_trigger = 2  # input

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(cpr_press, GPIO.OUT)
    GPIO.setup(cpr_press_low, GPIO.OUT)
    GPIO.setup(air_pump, GPIO.OUT)
    GPIO.setup(air_pump_low, GPIO.OUT)
    GPIO.setup(cpr_up, GPIO.OUT)
    GPIO.setup(cpr_down, GPIO.OUT)
    # GPIO.setup(cam_up, GPIO.OUT)
    # GPIO.setup(cam_down, GPIO.OUT)
    GPIO.setup(press_trigger, GPIO.IN)

def reset():
    GPIO.cleanup()
    setup()
    GPIO.output(air_pump, GPIO.LOW)
    GPIO.output(air_pump_low, GPIO.LOW)
    GPIO.output(cpr_press, GPIO.LOW)
    GPIO.output(cpr_press_low, GPIO.LOW)
    GPIO.output(cpr_up, GPIO.HIGH)
    GPIO.output(cpr_down, GPIO.LOW)
    # GPIO.output(cam_up, GPIO.LOW)
    # GPIO.output(cam_down, GPIO.HIGH)

def setup_gpio():
    setup()

def presure_sensor_triggered():
    return not GPIO.input(press_trigger)

cam_dict = {
    "left": (GPIO.LOW, GPIO.HIGH),
    "right": (GPIO.HIGH, GPIO.LOW),
    "stop": (GPIO.LOW, GPIO.LOW)
}

def cam_go(side: Literal["left", "right", "stop"]):
    return
    GPIO.output(cam_up, cam_dict[side][0])
    GPIO.output(cam_down, cam_dict[side][1])

cpr_dict = {
    "up": (GPIO.HIGH, GPIO.LOW),
    "down": (GPIO.LOW, GPIO.HIGH),
    "stop": (GPIO.LOW, GPIO.LOW)
}

def cpr_move(side: Literal["up", "down", "stop"]):
    GPIO.output(cpr_up, cpr_dict[side][0])
    GPIO.output(cpr_down, cpr_dict[side][1])

def air_pump_on(enable: bool):
    GPIO.output(air_pump, GPIO.HIGH if enable else GPIO.LOW)
    GPIO.output(air_pump_low, GPIO.LOW)

def cpr_press_on(enable: bool):
    GPIO.output(cpr_press, GPIO.HIGH if enable else GPIO.LOW)
    GPIO.output(cpr_press_low, GPIO.LOW)

setup()
reset()