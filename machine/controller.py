import datetime
import time
from threading import Thread, Lock
import website.web as web

from tool.face_detection import FaceDetector
from machine.mio import *
import tool.sound_tool as sound_tool

class MachineController:
    def __init__(self, ui_queue):
        # Initialize hardware
        reset()
        self._stop = False
        self._shot = False
        self._lock = Lock()

        self.list_init()

        if not len(self.action_dict) == len(self.process_lst):
            raise ValueError("len(self.action_dict) != len(self.process_lst)")

        self.thread = None
        self.ui_queue = ui_queue

        setup_gpio()

        self.face_detection_timeout = 60
        
        self.camera_enabled = True

        self.log_prefix = "  MC: "

    def list_init(self):
        self.action_dict = {
            1: lambda: self.sleep(1),
            2: lambda: self.sleep(1),
            3: lambda: self.sleep(1),
            4: lambda: self.sleep(1),
            5: lambda: self.sleep(1),
            6: lambda: self.sleep(1),
            7: lambda: self.sleep(1),
            # 8: self.position,
            8: lambda: self.sleep(1),
            9: self.wait_for_shot,
            10: self.electric_shocks,
            11: self.down_until_triggered,
            12: self.cpr,
            13: self.breaf,
            14: lambda: self.sleep(1),
        }
        self.process_lst = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

    def get_stop(self) -> bool:
        with self._lock:
            return self._stop

    def set_stop(self, value: bool):
        with self._lock:
            self._stop = value

    def get_shot(self) -> bool:
        with self._lock:
            return self._shot

    def set_shot(self, value: bool):
        with self._lock:
            self._shot = value

    def get_sound_length(self, i):
        sound_path = f"./resources/{i}.wav"
        sound_length = sound_tool.get_sound_length(sound_path)
        return sound_length * 0

    def loop(self, start=1, end=None):
        len_action_dict = len(self.action_dict)

        if end is None:
            end=len_action_dict

        for i in self.process_lst[start-1:end-1]:
            if self.get_stop():
                break
            print(self.log_prefix + "RUNNING IMAGE", i)

            self.ui_queue.put(('update_image', i))
            self.ui_queue.put(('play_sound', i))
            self.sleep(self.get_sound_length(i) + 1)
            
            action = self.action_dict.get(i)
            if action:
                action()

    def wait_for_shot(self):
        self.ui_queue.put(('update_start_button_text', 'Shot!'))
        while not self.get_shot() and not self.get_stop():
            self.sleep(0.05)
        self.ui_queue.put(('update_start_button_text', 'Start'))

    def background_task(self):
        self.set_shot(False)
        web.machine_status.set_start(datetime.datetime.now())

        self.loop(start=8)
        for i in range(100):
            if self.get_stop():
                break
            if i == 2:
                self.loop(start=8)
            self.loop(start=11)

        web.machine_status.set_start(None)
        self.ui_queue.put(('update_image', 1))

    def position(self):
        if not self.camera_enabled:
            print(self.log_prefix + "camera was disabled")
            return
        
        print(self.log_prefix + "camera detection enabled!")
        # Set display=True to enable frame capturing for UI display
        face_detector = FaceDetector(display=True, camera_index=0)

        start_t = time.time()

        while not self.get_stop() and face_detector.get_running():
            # Get vector from queue
            align_vector = face_detector.get_vector()

            print(self.log_prefix + "getting vector")
            
            current_time = time.time()

            frame = face_detector.get_frame()
            if frame is not None:
                # Send the frame to the main UI for display
                self.ui_queue.put(('update_cv_image', frame))

            if align_vector is None:
                self.sleep(0.01)
                continue

            x, y, v_t = align_vector

            # Add timeout
            if current_time - v_t > 2:
                cam_go("stop")
                continue

            if current_time - start_t > self.face_detection_timeout:
                print(self.log_prefix + "Face detection timeout")
                break

            x = -x
                
            if abs(x) < 10:
                cam_go("stop")
                break
            elif x < 0:
                cam_go("left")
            elif x > 0:
                cam_go("right")
            else:
                print(self.log_prefix + "Unexpected happened in MachineController function position()")
            
            self.sleep(0.05)  # Small delay to prevent busy waiting

        print(self.log_prefix + "Stopping face detector")
        face_detector.stop()
        
        # Clear the display by showing the default image after face detection is done
        self.ui_queue.put(('update_image', 1))
        print(self.log_prefix + "Face detector stopped")

    def sleep(self, n):
        t = time.time()
        while time.time() - t < n and not self.get_stop():
            time.sleep(0.01)

    def electric_shocks(self):
        web.machine_status.update_status(shocks=1)
        self.sleep(1)

    def down_until_triggered(self):
        cpr_move("down")
        while not self.get_stop():
            if presure_sensor_triggered():
                break
            self.sleep(0.05)
        cpr_move("stop")

    def cpr(self):
        print(self.log_prefix + "cpr Running")
        web.machine_status.update_status(cpr_cycles=1)
        cpr_press_on(True)
        self.sleep(23.5)
        cpr_press_on(False)
        cpr_move("up")
        self.sleep(2)
        cpr_move("stop")

    def breaf(self):
        print(self.log_prefix + "breaf Running")
        web.machine_status.update_status(ventilations=1)
        air_pump_on(True)
        self.sleep(1.5)
        air_pump_on(False)
        self.set_shot(False)

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.set_stop(False)
        self.set_shot(False)
        self.thread = Thread(target=self.background_task)
        self.thread.start()

    def stop(self):
        if self.get_stop():
            print(self.log_prefix + "repeat stopping is not allowed.")
            return
        
        print(self.log_prefix + "Stop called, setting stop flag")
        self.set_stop(True)

        if self.thread and self.thread.is_alive():
            print(self.log_prefix + "Waiting for thread to join")
            self.thread.join(timeout=5)
            print(self.log_prefix + "Thread joined or timeout")

        reset()
        print(self.log_prefix + "Moving cpr up")
        cpr_move("up")
        cam_go("stop")
        time.sleep(2)

        print(self.log_prefix + "Resetting flags")
        self.set_shot(False)
        self.thread = None

        print(self.log_prefix + "Calling reset")
        reset()
        print(self.log_prefix + "Reset complete")

    def __del__(self):
        print(self.log_prefix + "MachineController destoried!")