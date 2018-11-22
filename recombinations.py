from pygame import draw
from abstract_animation import Animation
import functools

class Ball(Animation):
    def __init__(self, screen, x, y, color):
        self.screen = screen
        self.x = x
        self.y = y
        self.color = color
    def draw(self, time):
        draw.ellipse(self.screen, self.color, (self.x, self.y), 0)

class Board:
    # dimensions - 2-tuple
    def __init__(self, screen, dimensions, maxcolor):
        self.screen = screen
        # grid has 2 extra rows at the top for incoming drops
        self.grid = [[None for j in range(dimensions[1])] for i in range(dimensions[0]+2)]
        self.maxcolor = maxcolor
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
        for j in range(len(self.grid[0])):
            for src in range(1, len(self.grid)):
                if not self.grid[src-1][j] and self.grid[src][j]:
                    #self.grid[src-1][j] = self.grid[src][j]
                    self.grid[src-1][j] = Ball(self.screen, src-1, j, self.grid[src][j].color)
                    self.grid[src][j] = None
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
        self.grid[-1] = [None for j in range(len(self.grid[0]))]
        self.grid[-2] = [None for j in range(len(self.grid[0]))]
        offset = min(index, len(self.grid[0]) - len(incoming[0]))
        for i in range(len(incoming)):
            for j in range(len(incoming[0])):
                self.grid[-2 + i][offset + j] = Ball(self.screen, i, j, incoming[i][j])
    
    def replace_group(self, group):
        # zero out and find the lowest, leftmost piece
        remainder = (len(self.grid), len(self.grid[0]))
        groupcolor = self.grid[group[0][0]][group[0][1]].color # color to replace with
        for piece in group:
            self.grid[piece[0]][piece[1]] = None
            if piece[0] < remainder[0]:
                remainder = piece
            if piece[0] == remainder[0] and piece[1] < remainder[1]:
                remainder = piece
        if groupcolor < self.maxcolor:
            self.grid[remainder[0]][remainder[1]] = Ball(self.screen, remainder[0], remainder[1], groupcolor + 1)
        return min(groupcolor + 1, self.maxcolor)
    
    def overheight(self):
        return functools.reduce(lambda accum, item: accum or item != None, self.grid[-2], False)
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
