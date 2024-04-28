from yolov9.get_video_details import get_video_details
import re

class VideoStat(object):
    def __init__(self, source, save_file=True, view_img=False, draw_trails=False):
        self.source = str(source)
        self.count = 0
        self.fps, self.width, self.height = get_video_details(source)
        self.vid_stride = (round(self.fps) / 15)
        self.vid_stride = 1 if self.vid_stride <= 1 else self.vid_stride
        if self.source.isnumeric() or  self.source.startswith('rtsp://') or self.source.startswith('http://') or self.source.startswith('https://'):
            # Numeric source
            self.vid_stride = self.vid_stride 
        else:
            self.vid_stride = 1  
        self.save_file = save_file
        self.view_img = view_img
        self.draw_trails = draw_trails
        self.frame = None
        self.stop = False

    def increment(self):
        self.count += 1

    def decrement(self):
        self.count -= 1

    def set_frame(self, frame):
        self.frame = frame

    def set_true(self):
        self.stop = True
    
    def set_draw_trails(self, draw_trails):
        self.draw_trails = draw_trails
    def inc(self, value):
        self.count += value

    