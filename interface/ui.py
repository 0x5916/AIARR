import os
import tkinter as tk
from PIL import Image, ImageTk
import machine.mio as mio
from machine.controller import MachineController
import queue
import pygame
import tool.sound_tool as sound_tool
import cv2
import time

class Ui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.resizing = False  # Flag to prevent infinite loop

        self.ui_queue = queue.Queue()
        self.machine = None

        self.log_prefix = "Ui: "

        # Initialize pygame mixer
        pygame.mixer.init()

        # Start the message processing loop
        self.process_messages()

    def init_ui(self):
        self.font_size = 24
        self.title_font = ("Arial", self.font_size + 2, "bold")
        self.body_font = ("Arial", self.font_size)
        self.option_add("*Font", self.body_font)

        self.pack_propagate(False)
        self.geometry("400x200")

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)

        # Load and display the image
        image_path = "./resources/1.JPG"  # Replace with your image path
        self.image = Image.open(image_path)
        self.photo = ImageTk.PhotoImage(self.image)

        self.display = tk.Canvas(self)
        self.display.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=2, pady=2)
        self.change_image("./resources/1.JPG")

        self.start_btn = tk.Button(self, text="Start", command=self.start_btn_event)
        self.start_btn.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)

        self.stop_btn = tk.Button(self, text="Stop", command=self.stop_btn_event)
        self.stop_btn.grid(row=1, column=1, sticky="nsew", padx=2, pady=2)

        self.up_btn = tk.Button(self, text="Up")
        self.up_btn.grid(row=0, column=2, sticky="nsew", padx=2, pady=2)
        self.up_btn.bind("<ButtonPress-1>", self.up_btn_event)
        self.up_btn.bind("<ButtonRelease-1>", self.release_up_down_btn_event)

        self.down_btn = tk.Button(self, text="Down")
        self.down_btn.grid(row=1, column=2, sticky="nsew", padx=2, pady=2)
        self.down_btn.bind("<ButtonPress-1>", self.down_btn_event)
        self.down_btn.bind("<ButtonRelease-1>", self.release_up_down_btn_event)

        self.down_btn = tk.Button(self, text="Left")
        self.down_btn.grid(row=0, column=3, sticky="nsew", padx=2, pady=2)
        self.down_btn.bind("<ButtonPress-1>", self.left_btn_event)
        self.down_btn.bind("<ButtonRelease-1>", self.release_left_right_btn_event)

        self.down_btn = tk.Button(self, text="Right")
        self.down_btn.grid(row=1, column=3, sticky="nsew", padx=2, pady=2)
        self.down_btn.bind("<ButtonPress-1>", self.right_btn_event)
        self.down_btn.bind("<ButtonRelease-1>", self.release_left_right_btn_event)

        self.bind("<Configure>", self.resize_event)

        # Handle window close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def process_messages(self):
        try:
            while True:
                message = self.ui_queue.get_nowait()
                command = message[0]
                if command == 'update_image':
                    img_path = f"./resources/{message[1]}.JPG"
                    if os.path.isfile(img_path): self.change_image(img_path)
                elif command == 'play_sound':
                    sound_path = f"./resources/{message[1]}.wav"
                    if os.path.isfile(sound_path):
                        sound_tool.play_sound(sound_path)
                elif command == 'update_start_button_text':
                    text = message[1]
                    self.start_btn.config(text=text)
                elif command == 'update_cv_image':
                    img = message[1]
                    self.change_cv_image(img)
                else:
                    break
            self.after(50, self.process_messages)
        except queue.Empty:
            self.after(50, self.process_messages)

    def resize_event(self, event):
        if self.resizing:
            return

        self.resizing = True
        try:
            w = event.width
            h = event.height

            if event.widget == self:
                r = self.image.width / self.image.height
                new_height = int(w / r)

                if new_height > h:
                    new_width = int(h * r)
                    w, h = new_width, h
                else:
                    h = new_height

                if w <= 0 or h <= 0:
                    self.resizing = False
                    return

                resized_image = self.image.resize((w, h), Image.LANCZOS)
                self.photo = ImageTk.PhotoImage(resized_image)
                self.display.configure(width=w, height=h)

                # Clear the canvas and place the image in the center
                self.display.delete("all")
                canvas_width = self.display.winfo_width()
                canvas_height = self.display.winfo_height()
                x_center = (canvas_width - w) // 2
                y_center = (canvas_height - h) // 2
                self.display.create_image(x_center, y_center, anchor=tk.NW, image=self.photo)
        finally:
            self.resizing = False

    def change_image(self, file_path):
        if file_path:
            self.image = Image.open(file_path)
            self.photo = ImageTk.PhotoImage(self.image)

            # Resize the image to fit the canvas
            w, h = self.display.winfo_width(), self.display.winfo_height()
            r = self.image.width / self.image.height
            new_height = int(w / r)

            if new_height > h:
                new_width = int(h * r)
                w, h = new_width, h
            else:
                h = new_height

            if w <= 0 or h <= 0:
                self.resizing = False
                return

            resized_image = self.image.resize((w, h), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(resized_image)

            # Clear the canvas and place the new image in the center
            self.display.delete("all")
            canvas_width = self.display.winfo_width()
            canvas_height = self.display.winfo_height()
            x_center = (canvas_width - w) // 2
            y_center = (canvas_height - h) // 2
            self.display.create_image(x_center, y_center, anchor=tk.NW, image=self.photo)

    def change_cv_image(self, cv_image):
        """Convert OpenCV image to Tkinter compatible format and display it"""
        if cv_image is not None:
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            
            w, h = self.display.winfo_width(), self.display.winfo_height()
            if w <= 0 or h <= 0:
                return

            img_w, img_h = pil_image.size
            r = img_w / img_h

            new_height = int(w / r)
            if new_height > h:
                new_width = int(h * r)
                w, h = new_width, h
            else:
                h = new_height

            if w <= 0 or h <= 0:  # Skip if calculated dimensions are not valid
                return

            resized_image = pil_image.resize((w, h), Image.LANCZOS)
            
            self.photo = ImageTk.PhotoImage(resized_image)

            # Clear canvas and display new image
            self.display.delete("all")
            canvas_width = self.display.winfo_width()
            canvas_height = self.display.winfo_height()
            x_center = (canvas_width - w) // 2
            y_center = (canvas_height - h) // 2
            self.display.create_image(x_center, y_center, anchor=tk.NW, image=self.photo)

    def start_btn_event(self):
        print(self.log_prefix + "Machine started")
        if self.machine is not None:
            self.machine.set_shot(True)
            return
        self.ui_reset()
        self.machine = MachineController(self.ui_queue)
        self.machine.start()

    def stop_btn_event(self):
        if self.machine is not None:
            self.machine.stop()
            self.machine = None
        self.ui_reset()

    def up_btn_event(self, event):
        mio.cpr_move("up")

    def down_btn_event(self, event):
        mio.cpr_move("down")

    def release_up_down_btn_event(self, event):
        mio.cpr_move("stop")

    def left_btn_event(self, event):
        mio.cam_go("left")

    def right_btn_event(self, event):
        mio.cam_go("right")

    def release_left_right_btn_event(self, event):
        mio.cam_go("stop")

    def ui_reset(self):
        self.change_image("./resources/1.JPG")
        self.start_btn.config(text="Start")

    def on_closing(self):
        if self.machine is not None:
            self.machine.stop()
        self.destroy()
