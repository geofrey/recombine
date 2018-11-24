import pygame
from pygame import draw
from abstract_animation import Animation
import functools

class Ball(Animation):
    def __init__(self, board, x, y, color):
        self.board = board
        self.color = color
        self.x = x
        self.y = y
    def draw(self, time):
        draw.ellipse(self.board.screen, self.board.drawingcolors[self.color], self.board.get_rect(self.x, self.y), 0)
    def __repr__(self):
        return str(self.color)

class Board:
    # dimensions - 2-tuple
    def __init__(self, screen, drawing_area, dimensions, maxcolor, drawingcolors):
        self.screen = screen
        self.grid_rect = drawing_area
        self.gridsize = drawing_area.width / dimensions[0]
        # grid has 2 extra rows at the top for incoming drops
        self.dimensions = dimensions
        self.grid = [[None for j in range(dimensions[0])] for i in range(dimensions[1]+2)]
        self.maxcolor = maxcolor
        self.drawingcolors = drawingcolors
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
        moved = set()
        for i in range(len(self.grid)-1-1, 0-1, -1): # scan bottom-1 to top
            for j in range(len(self.grid[0])):
                if self.grid[i][j] and not self.grid[i+1][j]:
                    self.grid[i+1][j] = self.grid[i][j]
                    self.grid[i][j] = None
                    self.grid[i+1][j].y -= 1
                    moved.add(self.grid[i+1][j])
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
                    ball = Ball(self, x, y, incoming[i][j])
                    self.grid[i][index+j] = ball
                    balls.append(ball)
        return balls
    
    def replace_group(self, group):
        # zero out and find the lowest, leftmost piece
        remainder = (0, len(self.grid[0])) # top right
        groupcolor = self.grid[group[0][0]][group[0][1]].color # color to replace with
        removed = []
        for piece in group:
            removed.append(self.grid[piece[0]][piece[1]])
            self.grid[piece[0]][piece[1]] = None
            if piece[0] > remainder[0]:
                remainder = piece
            if piece[0] == remainder[0] and piece[1] < remainder[1]:
                remainder = piece
        if groupcolor < self.maxcolor:
            newball = Ball(self, remainder[1], len(self.grid)-remainder[0], groupcolor + 1)
            self.grid[remainder[0]][remainder[1]] = newball
            inserted = newball
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
