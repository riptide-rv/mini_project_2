class Counter(object):
    def __init__(self):
        self.count = 0
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

    