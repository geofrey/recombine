import pygame
from pygame import draw
from abstract_animation import Animation
import functools
import time

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
#</Ball>

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
        self.background.draw = lambda frame: self.screen.fill(pygame.Color('gray'))
        self.background.ended = lambda frame: False
        
        self.decorations = set()
        
        whitecolor = pygame.Color('white')
        heightlimit = Animation(None, None)
        heightlimit.draw = lambda frame: draw.line(self.screen, whitecolor, (self.grid_rect.left, self.grid_rect.top + 2*self.gridsize), (self.grid_rect.right, self.grid_rect.top + 2*self.gridsize), 3)
        self.decorations.add(heightlimit)
        
        border = Animation(None, None)
        border.draw = lambda frame: draw.rect(self.screen, pygame.Color('black'), self.grid_rect, 4)
        self.decorations.add(border)
        
        scoredisplay = Animation(None, None)
        scorefont = pygame.font.Font(pygame.font.get_default_font(), 14)
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
    
    def gravity(self):
        moved = False
        for i in range(len(self.grid)-1-1, 0-1, -1): # scan bottom-1 to top
            for j in range(len(self.grid[0])):
                if self.grid[i][j] and not self.grid[i+1][j]:
                    to_drop = self.grid[i][j]
                    self.grid[i+1][j] = to_drop
                    self.grid[i][j] = None
                    #self.grid[i+1][j].y -= 1
                    to_drop.move_to((j, len(self.grid)-i-1), time.time(), time.time()+0.10)
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
        
    def replace_group(self, group):
        # zero out and find the lowest, leftmost piece
        remainder = (0, len(self.grid[0])) # top right
        groupcolor = self.grid[group[0][0]][group[0][1]].color
        removed = []
        for piece in group:
            outgoing = self.grid[piece[0]][piece[1]]
            outgoing.vanish(time.time(), time.time()+1.0)
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
            newball.appear(time.time(), time.time()+1.0)
            inserted = newball
        else:
            inserted = None
        self.currentcolor = max(inserted.color if inserted else 0, self.currentcolor)
        self.score += self.scorevalues[groupcolor]*len(group)
        return removed, inserted
    
    def physics(self):
        if self.gravity():
            return True
        else:
            groups = list(filter(lambda l: len(l)>=3, self.find_groups()))
            if groups:
                for group in groups:
                    self.replace_group(group)
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
        rect = pygame.Rect(
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
        r = pygame.Rect(0,0,0,0)
        r.top = self.grid_rect.top/2
        r.height = self.gridsize/2
        r.width = self.gridsize/2
        for level in range(1, self.currentcolor):
            #r.left = boardwidth * gridsize - gridsize/2 * len(combinecolors) + gridsize/2 * level
            r.left = self.gridsize/2 * (self.dimensions[0]*2 - len(self.drawingcolors) + level)
            draw.ellipse(self.screen, self.drawingcolors[level], pygame.Rect(r.left, r.top, r.width, r.height), 0)
        
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                if self.grid[i][j]:
                    self.grid[i][j].draw(frame)
#</Board>

import random
# this is the only function that uses random

def new_drop(maxcolor):
    return [[random.randint(1, maxcolor-1), random.randint(1, maxcolor-1)]]

def spin(old, direction):
    if old == None:
        return None
    if len(old) == 2: # vertical
        if direction == 'left':
            new = [[old[0][0], old[1][0]]]
        elif direction == 'right':
            new = [[old[1][0], old[0][0]]]
    elif len(old) == 1: # horizontal
        if direction == 'left':
            new = [[old[0][1]], [old[0][0]]]
        elif direction == 'right':
            new = [[old[0][0]], [old[0][1]]]
    return new 
