class Animation:
    def __init__(self, starttime, endtime):
        self.starttime = starttime
        self.endtime = endtime
    def draw(self, time):
        pass
    def started(self, time):
        return time >= self.starttime
    def ended(self, time):
        return time > self.endtime
    def progress(self, time):
        return float(time - self.starttime)/(self.endtime - self.starttime)
