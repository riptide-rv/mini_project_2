import tkinter as tk
from PIL import Image, ImageTk
import cv2
import threading

from yolov9.test_gui import TrackerModel
from yolov9.get_video_details import get_video_details
import socket
import pickle
from yolov9.test_utils import Counter

class GUIApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GUI Application")
       
        self.tracker_model = None
        self.frame_updater_thread = None
        self.value = tk.StringVar()
        self.c = Counter()
        self.frame = None
        self.create_widgets()
        self.update_value_loop()

    def create_widgets(self):
        # Create the "Source" label and entry field
        source_label = tk.Label(self, text="Source:")
        source_label.pack()
        label = tk.Label(self, textvariable=self.value)
        label.pack()
        self.entry = tk.Entry(self)
        self.entry.pack()
        self.source_entry = tk.Entry(self)
        self.source_entry.pack()
        

        # Create the "Run" button
        run_button = tk.Button(self, text="Run", command=self.run_function)
        run_button.pack()

        button = tk.Button(self, text="Stop", command=self.stop)
        button.pack()

        # Create a canvas to display the video
        self.canvas = tk.Canvas(self, width=640, height=480)
        self.canvas.pack()

    def run_function(self):
        source = self.source_entry.get()
        fps, width, height = get_video_details(source)
        print(f"FPS: {fps}, Width: {width}, Height: {height}")

        object_creation_thread = threading.Thread(target=self.create_tracker_model, args=(source,self.c, self.frame))
        object_creation_thread.start()

    def stop(self):
        self.c.set_true()
    

    def create_tracker_model(self, source, c, frame):
        self.tracker_model = TrackerModel(source, counter = c, frame = frame)


    def update_value(self):
        new_value = str(self.c.count)
        self.value.set(new_value)


    def update_value_loop(self):
        self.update_value()
        if self.c.frame is not None:
            self.display_frame()
        self.after(15, self.update_value_loop)

    def display_frame(self):
        # cv2.imshow("Frame", self.c.frame)

        # b,g,r = cv2.split(self.c.frame)
        # img = cv2.merge((r,g,b))
        cv2_image = cv2.cvtColor(self.c.frame, cv2.COLOR_BGR2RGBA)
        pil_image = Image.fromarray(cv2_image)
        tk_image = ImageTk.PhotoImage(image=pil_image)

            # Update the canvas with the new frame
        self.canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
        self.canvas.image = tk_image 

  