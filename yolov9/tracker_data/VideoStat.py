class VideoData:

    def __init__(self):
        self.count = 0
        
    def inc(self):
        self.count += 1
        print(f"count is now {self.count}")