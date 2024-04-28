import tkinter as ttk
from PIL import Image, ImageTk
import cv2
import threading

from yolov9.tracker_model import TrackerModel
from yolov9.get_video_details import get_video_details
from yolov9.video_stat import VideoStat




class GUIApp(ttk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Main Window")
        self.geometry("800x600")
        self.video_stat = None
        self.canvas = None
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
        
        spacing = ttk.Label(self.left_panel, text="")
        spacing.pack(fill="both", expand=True)
    
        # Work hours label and display
        source_frame = ttk.Frame(self.left_panel)
        source_frame.pack(padx=10, pady=5, fill="x")
        fps_frame = ttk.Frame(self.left_panel)
        fps_frame.pack(padx=10, pady=5, fill="x")
        work_hours_frame = ttk.Frame(self.left_panel)
        work_hours_frame.pack(padx=10, pady=5, fill="x")
        
        work_hours_label = ttk.Label(work_hours_frame, text="Work(s) :")
        work_hours_label.pack(side="left")
        self.work_hours_value = ttk.StringVar(value="0")
        work_hours_display = ttk.Label(work_hours_frame, textvariable=self.work_hours_value)
        work_hours_display.pack(side="left")

        source_label = ttk.Label(source_frame, text="Source :")
        source_label.pack(side="left")
        self.source_value = ttk.StringVar(value="0")
        source_display = ttk.Label(source_frame, textvariable=self.source_value)
        source_display.pack(side="left")

        fps_label = ttk.Label(fps_frame, text="Fps :")
        fps_label.pack(side="left")
        self.fps_value = ttk.StringVar(value="0")
        fps_display = ttk.Label(fps_frame, textvariable=self.fps_value)
        fps_display.pack(side="left")


        detc_frame = ttk.Frame(self.left_panel)
        detc_frame.pack(padx=10, pady=5, fill="x")

        detc_label = ttk.Label(detc_frame, text="Fps :")
        detc_label.pack(side="left")
        self.detc_value = ttk.StringVar(value="0")
        detc_display = ttk.Label(detc_frame, textvariable=self.detc_value)
        detc_display.pack(side="left")

        # Start and Stop buttons
        button_frame = ttk.Frame(self.left_panel)
        button_frame.pack(padx=10, pady=10, fill="x", side="bottom")

        self.start_button = ttk.Button(button_frame, text="Start", command=self.start_timer)
        self.start_button.pack(side="top", fill="x", expand=True)

        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_timer, default="disabled")
        self.stop_button.pack(side="bottom", fill="x", expand=True)

    def create_content_area(self):
        self.content_area = ttk.Frame(self.main_frame)
        self.content_area.pack(side="left", fill="both", expand=True)

    def start_timer(self):
        # Implement your start timer logic here
        self.run_function()

    def stop_timer(self):
        # Implement your stop timer logic here
        self.stop()

    def run_function(self):
        if self.canvas is not None:
            self.canvas.destroy()
        source = self.source_entry.get()
        self.video_stat = VideoStat(source)

        self.source_value.set(self.video_stat.vid_stride)
        self.fps_value.set(self.video_stat.fps)

        print(f"FPS: {self.video_stat.fps}, Width: {self.video_stat.width}, Height: {self.video_stat.height}")
        self.canvas = ttk.Canvas(self.content_area, width=self.video_stat.width, height=self.video_stat.height)
        self.canvas.pack()

        object_creation_thread = threading.Thread(target=self.create_tracker_model, args=(source,self.video_stat, self.frame))
        object_creation_thread.start()
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

    def stop(self):
        self.video_stat.set_true()
        self.start_button.config(state="normal")

        
    

    def create_tracker_model(self, source, video_stat, frame):
        self.tracker_model = TrackerModel(source, video_stat = video_stat)


    def update_value(self):
        if self.video_stat is None:
            return
        new_value = str(round((self.video_stat.count / self.video_stat.fps ) * self.video_stat.vid_stride,2))
        # *(self.video_stat.vid_stride+ (self.video_stat.vid_stride / 10) + (self.video_stat.vid_stride)),2 ))
        self.work_hours_value.set(new_value)
        self.detc_value.set(str(self.video_stat.count))


    def update_value_loop(self):
        self.update_value()
        if self.video_stat is not None and self.video_stat.frame is not None:
            self.display_frame()
        self.after(15, self.update_value_loop)

    def display_frame(self):
        # cv2.imshow("Frame", self.c.frame)

        # b,g,r = cv2.split(self.c.frame)
        # img = cv2.merge((r,g,b))
        cv2_image = cv2.cvtColor(self.video_stat.frame, cv2.COLOR_BGR2RGBA)
        pil_image = Image.fromarray(cv2_image)
        tk_image = ImageTk.PhotoImage(image=pil_image)

            # Update the canvas with the new frame
        self.canvas.create_image(0, 0, anchor=ttk.NW, image=tk_image)
        self.canvas.image = tk_image 

