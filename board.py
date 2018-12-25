from abstract_animation import Animation
from ball import Ball
import functools
from pygame import Color, draw, font, Rect

class Board:
    # dimensions - 2-tuple
    def __init__(self, screen, drawing_area, dimensions, maxcolor, drawingcolors, basescores):
        self.screen = screen
        self.grid_rect = drawing_area
        self.gridsize = drawing_area.width / dimensions[0]
        # grid has 2 extra rows at the top for incoming drops
        self.dimensions = dimensions
        self.grid = [[None for j in range(dimensions[0])] for i in range(dimensions[1]+2)]
        self.maxcolor = maxcolor
        self.currentcolor = 2 # green + yellow
        self.drawingcolors = drawingcolors
        self.scorevalues = basescores
        self.score = 0
        
        self.init_decorations()
    
    def init_decorations(self):
        self.background = Animation(None, None)
        self.background.draw = lambda frame: self.screen.fill(Color('gray'))
        self.background.ended = lambda frame: False
        
        self.decorations = set()
        
        whitecolor = Color('white')
        heightlimit = Animation(None, None)
        heightlimit.draw = lambda frame: draw.line(self.screen, whitecolor, (self.grid_rect.left, self.grid_rect.top + 2*self.gridsize), (self.grid_rect.right, self.grid_rect.top + 2*self.gridsize), 3)
        self.decorations.add(heightlimit)
        
        border = Animation(None, None)
        border.draw = lambda frame: draw.rect(self.screen, Color('black'), self.grid_rect, 4)
        self.decorations.add(border)
        
        scoredisplay = Animation(None, None)
        scorefont = font.Font(font.get_default_font(), 14)
        scoredisplay.draw = lambda frame: self.screen.blit(scorefont.render(str(self.score), True, whitecolor), (self.grid_rect.left, self.grid_rect.left))
        self.decorations.add(scoredisplay)
        
        self.temporary_objects = set() # need a place to store vanishing balls since they're not in the grid anymore
    
    def ended(self, frame):
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                if self.grid[i][j] != None:
                    if not self.grid[i][j].ended(frame):
                        return False
        return True
    
    def __getitem__(self, i):
        return self.grid[i]
    def __setitem__(self, i, x):
        self.grid[i] = x
    
    def gravity(self, time):
        moved = False
        for i in range(len(self.grid)-1-1, 0-1, -1): # scan bottom-1 to top
            for j in range(len(self.grid[0])):
                if self.grid[i][j] and not self.grid[i+1][j]:
                    to_drop = self.grid[i][j]
                    self.grid[i+1][j] = to_drop
                    self.grid[i][j] = None
                    #self.grid[i+1][j].y -= 1
                    to_drop.move_to((j, len(self.grid)-i-1), time, time+0.10)
                    moved = True
        return moved
    
    def get_neighbors(self, i, j):
        neighbors = []
        if i > 0:
            neighbors.append((i-1, j))
        if j > 0:
            neighbors.append((i, j-1))
        if i < len(self.grid)-1:
            neighbors.append((i+1, j))
        if j < len(self.grid[0])-1:
            neighbors.append((i, j+1))
        return neighbors
    
    def find_group(self, i, j):
        if self.grid[i][j]:
            return self.find_group_rec(i, j, [], self.grid[i][j].color)
        else:
            return []

    def find_group_rec(self, i, j, group, color):
        if (i, j) not in group and self.grid[i][j] and self.grid[i][j].color == color:
            group.append((i, j))
            for n in self.get_neighbors(i, j):
                self.find_group_rec(n[0], n[1], group, color)
        return group
    
    def find_groups(self):
        checked = []
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                if (i, j) not in checked and self.grid[i][j]:
                    group = self.find_group(i, j)
                    checked += group
                    if len(group) > 0:
                        yield group
        
    def replace_group(self, group, time):
        # zero out and find the lowest, leftmost piece
        remainder = (0, len(self.grid[0])) # top right
        groupcolor = self.grid[group[0][0]][group[0][1]].color
        removed = []
        for piece in group:
            outgoing = self.grid[piece[0]][piece[1]]
            outgoing.vanish(time, time+0.50)
            self.temporary_objects.add(outgoing)
            removed.append(outgoing)
            self.grid[piece[0]][piece[1]] = None
            if piece[0] > remainder[0]:
                remainder = piece
            if piece[0] == remainder[0] and piece[1] < remainder[1]:
                remainder = piece
        if groupcolor < self.maxcolor:
            newball = Ball(self, (remainder[1], len(self.grid)-remainder[0]), groupcolor + 1)
            self.grid[remainder[0]][remainder[1]] = newball
            newball.appear(time, time+0.50)
            inserted = newball
        else:
            inserted = None
        self.currentcolor = max(inserted.color if inserted else 0, self.currentcolor)
        self.score += self.scorevalues[groupcolor]*len(group)
        return removed, inserted
    
    def physics(self, time):
        if self.gravity(time):
            return True
        else:
            groups = list(filter(lambda l: len(l)>=3, self.find_groups()))
            if groups:
                for group in groups:
                    self.replace_group(group, time)
                return True
            else:
                return False
    
    def insert(self, incoming, index):
        balls = [] # giggle
        for i in range(len(incoming)):
            for j in range(len(incoming[0])):
                if incoming[i][j]:
                    x,y = index+j, self.dimensions[1]+2-i
                    ball = Ball(self, (x, y), incoming[i][j])
                    self.grid[i][index+j] = ball
                    balls.append(ball)
        return balls
    
    def overheight(self):
        return functools.reduce(lambda accum, item: accum or item != None, self.grid[1], False)
    
    def get_rect(self, x, y):
        rect = Rect(
            self.grid_rect.left + x*self.gridsize, 
            self.grid_rect.bottom - y*self.gridsize,
            self.gridsize,
            self.gridsize)
        return rect
    
    def draw(self, frame):
        # draw everything on the board
        self.background.draw(frame)
        for prop in self.decorations:
            prop.draw(frame)
        
        for temp in self.temporary_objects.copy():
            if temp.ended(frame):
                self.temporary_objects.remove(temp)
            else:
               temp.draw(frame)
       
        # TODO pre-generate the score indicator and just hide the balls until they're needed
        r = Rect(0,0,0,0)
        r.top = self.grid_rect.top/2
        r.height = self.gridsize/2
        r.width = self.gridsize/2
        for level in range(1, self.currentcolor):
            #r.left = boardwidth * gridsize - gridsize/2 * len(combinecolors) + gridsize/2 * level
            r.left = self.gridsize/2 * (self.dimensions[0]*2 - len(self.drawingcolors) + level)
            draw.ellipse(self.screen, self.drawingcolors[level], Rect(r.left, r.top, r.width, r.height), 0)
        
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                if self.grid[i][j]:
                    self.grid[i][j].draw(frame)

#

