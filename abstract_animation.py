class Animation:
    def __init__(self, starttime, endtime):
        self.start = starttime
        self.end = endtime
    def draw(self, time):
        pass
    def started(self, time):
        return time > self.start
    def ended(self, time):
        return time > self.end
    def progress(self, time):
        return float(time - self.start)/(self.end - self.start)
