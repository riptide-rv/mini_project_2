import tkinter as ttk
from PIL import Image, ImageTk
import cv2
import threading

from yolov9.test_gui import TrackerModel
from yolov9.get_video_details import get_video_details
import socket
import pickle
from yolov9.test_utils import Counter

# class GUIApp(tk.Tk):
#     def __init__(self):
#         super().__init__()
#         self.title("GUI Application")
#         self.left_panel = None
#         self.right_panel = None
#         self.tracker_model = None
#         self.frame_updater_thread = None
#         self.value = tk.StringVar()
#         self.c = Counter()
#         self.create_widgets()
#         self.update_value_loop()

#     def create_widgets(self):

#         main_frame = tk.Frame(self)
#         main_frame.pack(fill=tk.BOTH, expand=True)
#         # Create the left panel frame
#         self.left_panel = tk.Frame(main_frame, bg="lightgray", width=200, relief=tk.RAISED)
#         self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH)

#         # Create the "Source" label and entry field
#         source_label = tk.Label(self.left_panel, text="Source:")
#         source_label.pack(pady=10)
#         source_label.pack()
#         label = tk.Label(self.left_panel, textvariable=self.value)
#         label.pack()

#         self.right_panel = tk.Frame(main_frame, bg="white")
#         self.right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

#         # Add widgets to the right panel
#         self.source_entry = tk.Entry(self.left_panel)
#         self.source_entry.pack()
        

#         # Create the "Run" button
#         run_button = tk.Button(self.left_panel, text="Run", command=self.run_function)
#         run_button.pack()

#         button = tk.Button(self.left_panel, text="Stop", command=self.stop)
#         button.pack()

#         # Create a canvas to display the video
        

#     def run_function(self):
#         source = self.source_entry.get()
#         fps, width, height = get_video_details(source)
#         print(f"FPS: {fps}, Width: {width}, Height: {height}")

#         self.canvas = tk.Canvas(self.right_panel, width=width, height=height)
#         self.canvas.pack()

#         object_creation_thread = threading.Thread(target=self.create_tracker_model, args=(source,self.c, self.frame))
#         object_creation_thread.start()

#     def stop(self):
#         self.c.set_true()
    

#     def create_tracker_model(self, source, c, frame):
#         self.tracker_model = TrackerModel(source, counter = c, frame = frame)


#     def update_value(self):
#         new_value = str(self.c.count)
#         self.value.set(new_value)


#     def update_value_loop(self):
#         self.update_value()
#         if self.c.frame is not None:
#             self.display_frame()
#         self.after(15, self.update_value_loop)

#     def display_frame(self):
#         # cv2.imshow("Frame", self.c.frame)

#         # b,g,r = cv2.split(self.c.frame)
#         # img = cv2.merge((r,g,b))
#         cv2_image = cv2.cvtColor(self.c.frame, cv2.COLOR_BGR2RGBA)
#         pil_image = Image.fromarray(cv2_image)
#         tk_image = ImageTk.PhotoImage(image=pil_image)

#             # Update the canvas with the new frame
#         self.canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
#         self.canvas.image = tk_image 





class GUIApp(ttk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Main Window")
        self.geometry("800x600")
        self.c = Counter()
        self.create_main_frame()
        self.create_left_panel()
        self.create_content_area()
        self.update_value_loop()

    def create_main_frame(self):
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill="both", expand=True)

    def create_left_panel(self):
        self.left_panel = ttk.Frame(self.main_frame, relief="raised", borderwidth=1, padx=10, pady=10)
        self.left_panel.pack(side="left", fill="both", expand=False)

        # Source label and entry field
        source_frame = ttk.Frame(self.left_panel)
        source_frame.pack(padx=10, pady=5, fill="x")
        source_label = ttk.Label(source_frame, text="Source:")
        source_label.pack(side="left", padx=5)
        self.source_entry = ttk.Entry(source_frame)
        self.source_entry.pack(side="left", fill="x", expand=True)

        # Work hours label and display
        work_hours_frame = ttk.Frame(self.left_panel)
        work_hours_frame.pack(padx=10, pady=5, fill="x")
        work_hours_label = ttk.Label(work_hours_frame, text="Work Hours:")
        work_hours_label.pack(side="left")
        self.work_hours_value = ttk.StringVar(value="0")
        work_hours_display = ttk.Label(work_hours_frame, textvariable=self.work_hours_value)
        work_hours_display.pack(side="left")

        # Start and Stop buttons
        button_frame = ttk.Frame(self.left_panel)
        button_frame.pack(padx=10, pady=10, fill="x", side="bottom")

        start_button = ttk.Button(button_frame, text="Start", command=self.start_timer)
        start_button.pack(side="top", fill="x", expand=True)

        stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_timer)
        stop_button.pack(side="bottom", fill="x", expand=True)

    def create_content_area(self):
        self.content_area = ttk.Frame(self.main_frame)
        self.content_area.pack(side="left", fill="both", expand=True)

        label = ttk.Label(self.content_area, text="Main Content Area")
        label.pack(padx=20, pady=20)

    def start_timer(self):
        # Implement your start timer logic here
        self.run_function()

    def stop_timer(self):
        # Implement your stop timer logic here
        self.c.set_true()

    def run_function(self):
        source = self.source_entry.get()
        fps, width, height = get_video_details(source)
        print(f"FPS: {fps}, Width: {width}, Height: {height}")

        self.canvas = ttk.Canvas(self.content_area, width=width, height=height)
        self.canvas.pack()

        object_creation_thread = threading.Thread(target=self.create_tracker_model, args=(source,self.c, self.frame))
        object_creation_thread.start()

    def stop(self):
        self.c.set_true()
    

    def create_tracker_model(self, source, c, frame):
        self.tracker_model = TrackerModel(source, counter = c, frame = frame)


    def update_value(self):
        new_value = str(self.c.count)
        self.work_hours_value.set(new_value)


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
        self.canvas.create_image(0, 0, anchor=ttk.NW, image=tk_image)
        self.canvas.image = tk_image 

