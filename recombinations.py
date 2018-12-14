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
    def draw(self, time):
        if self.ended(time):
            self.prior_location = None
        if self.prior_location:
            pseudoprogress = self.progress(time)
            currentlocation = self.prior_location.move((self.location.left - self.prior_location.left)*pseudoprogress, (self.location.top - self.prior_location.top)*pseudoprogress)
        else:
            currentlocation = self.location
        draw.ellipse(self.board.screen, self.board.drawingcolors[self.color], currentlocation, 0)
    def ended(self, time):
        if self.prior_location:
            return super().ended(time)
        else:
            return True
    def move_to(self, destinationxy, starttime, endtime):
        self.starttime = starttime
        self.endtime = endtime
        self.prior_location = self.location
        self.location = self.board.get_rect(*destinationxy)
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
        self.background.draw = lambda time: self.screen.fill(pygame.Color('gray'))
        self.background.ended = lambda time: False
        
        self.decorations = set()
        
        whitecolor = pygame.Color('white')
        heightlimit = Animation(None, None)
        heightlimit.draw = lambda time: draw.line(self.screen, whitecolor, (self.grid_rect.left, self.grid_rect.top + 2*self.gridsize), (self.grid_rect.right, self.grid_rect.top + 2*self.gridsize), 3)
        self.decorations.add(heightlimit)
        
        border = Animation(None, None)
        border.draw = lambda time: draw.rect(self.screen, pygame.Color('black'), self.grid_rect, 4)
        self.decorations.add(border)
        
        scoredisplay = Animation(None, None)
        scorefont = pygame.font.Font(pygame.font.get_default_font(), 14)
        scoredisplay.draw = lambda time: self.screen.blit(scorefont.render(str(self.score), True, whitecolor), (self.grid_rect.left, self.grid_rect.left))
        self.decorations.add(scoredisplay)
    
    def ended(self, time):
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                if self.grid[i][j] != None:
                    if not self.grid[i][j].ended(time):
                        return False
        return True
    
    def __getitem__(self, i):
        return self.grid[i]
    def __setitem__(self, i, x):
        self.grid[i] = x
    
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
    
    def gravity(self):
        moved = False
        for i in range(len(self.grid)-1-1, 0-1, -1): # scan bottom-1 to top
            for j in range(len(self.grid[0])):
                if self.grid[i][j] and not self.grid[i+1][j]:
                    to_drop = self.grid[i][j]
                    self.grid[i+1][j] = to_drop
                    self.grid[i][j] = None
                    #self.grid[i+1][j].y -= 1
                    to_drop.move_to((j, len(self.grid)-i-1), time.time(), time.time()+0.20)
                    moved = True
        return moved
    
    def find_groups(self):
        groups = []
        checked = []
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                if (i, j) not in checked and self.grid[i][j]:
                    group = self.find_group(i, j)
                    checked += group
                    if len(group) > 0:
                        groups.append(group)
        return groups
    
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
    
    def replace_group(self, group):
        # zero out and find the lowest, leftmost piece
        remainder = (0, len(self.grid[0])) # top right
        groupcolor = self.grid[group[0][0]][group[0][1]].color
        removed = []
        for piece in group:
            removed.append(self.grid[piece[0]][piece[1]])
            self.grid[piece[0]][piece[1]] = None
            if piece[0] > remainder[0]:
                remainder = piece
            if piece[0] == remainder[0] and piece[1] < remainder[1]:
                remainder = piece
        if groupcolor < self.maxcolor:
            newball = Ball(self, (remainder[1], len(self.grid)-remainder[0]), groupcolor + 1)
            self.grid[remainder[0]][remainder[1]] = newball
            inserted = newball
        self.currentcolor = max(inserted.color, self.currentcolor)
        self.score += self.scorevalues[groupcolor]*len(group)
        return removed, inserted
    
    def overheight(self):
        return functools.reduce(lambda accum, item: accum or item != None, self.grid[1], False)
    
    def get_rect(self, x, y):
        rect = pygame.Rect(
            self.grid_rect.left + x*self.gridsize, 
            self.grid_rect.bottom - y*self.gridsize,
            self.gridsize,
            self.gridsize)
        return rect
    
    def draw(self, time):
        # draw everything on the board
        self.background.draw(time)
        for prop in self.decorations:
            prop.draw(time)
        
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
                    self.grid[i][j].draw(time)
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
