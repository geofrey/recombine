from abstract_animation import Animation
from pygame import draw

class Ball(Animation):
    def __init__(self, board, location, color):
        super().__init__(1,2)
        self.board = board
        self.color = color
        self.prior_location = None
        self.location = self.board.get_rect(*location)
        self.draw = self.draw_static
    def draw_static(self, frame):
        draw.ellipse(self.board.screen, self.board.drawingcolors[self.color], self.location, 0)
    def draw_moving(self, frame):
        if self.ended(frame):
            self.draw = self.draw_static
            self.draw(frame)
        else:
            pseudoprogress = self.progress(frame)
            currentlocation = self.prior_location.move((self.location.left - self.prior_location.left)*pseudoprogress, (self.location.top - self.prior_location.top)*pseudoprogress)
            draw.ellipse(self.board.screen, self.board.drawingcolors[self.color], currentlocation, 0)
    def draw_appearing(self, frame):
        if self.ended(frame):
            self.draw = self.draw_static
            self.draw(frame)
        else:
            scale = self.progress(frame)-1.0
            currentdimensions = self.location.inflate(scale*self.location.width, scale*self.location.height)
            draw.ellipse(self.board.screen, self.board.drawingcolors[self.color], currentdimensions, 0)
    def draw_nothing(self, frame):
        pass
    def draw_vanishing(self, frame):
        if self.ended(frame):
            self.draw = self.draw_nothing
        else:
            scale = 0.0-self.progress(frame)
            currentdimensions = self.location.inflate(scale*self.location.width, scale*self.location.height)
            draw.ellipse(self.board.screen, self.board.drawingcolors[self.color], currentdimensions, 0)
    def move_to(self, destinationxy, starttime, endtime):
        self.starttime = starttime
        self.endtime = endtime
        self.prior_location = self.location
        self.location = self.board.get_rect(*destinationxy)
        self.draw = self.draw_moving
    def appear(self, starttime, endtime):
        self.starttime = starttime
        self.endtime = endtime
        self.draw = self.draw_appearing
    def vanish(self, starttime, endtime):
        self.starttime = starttime
        self.endtime = endtime
        self.draw = self.draw_vanishing
    def __repr__(self):
        return str(self.color)

