#!/usr/bin/python

import pygame
from pygame import rect, draw, event
import time

from recombinations import *
from abstract_animation import Animation

# game variables

boardheight = 7
boardwidth = 7
currentcolor = 3
frame = 1.0/30
idletime = 1 * frame
droptime = 2 * frame
breaktime = 15 * frame
frametime = idletime # initial
gridsize = 40
boardoffset = int(gridsize/2)
maxcolor = 10
mouse = (0, 0)
turn = 0
score = 0


# init

scene = [] # decorations
dots = [] # dots

pygame.init()
scorefont = pygame.font.Font(pygame.font.get_default_font(), 14)
window = pygame.Rect(0, 0, gridsize*boardwidth + 2*boardoffset, gridsize*boardheight + 3*boardoffset)
screen = pygame.display.set_mode((gridsize*boardwidth + 2*boardoffset, gridsize*(boardheight+2) + 3*boardoffset)) # ??
#screen = pygame.display.set_mode(window...
window = screen.get_rect()

background = Animation(None, None)
background.draw = lambda: screen.fill(pygame.Color('gray'))
background.ended = lambda: False
scene.append(background)

heightlimit = Animation(None, None)
heightlimit.draw = lambda: draw.line(screen, gridcolor, (boardpos.left, boardpos.top + 2*gridsize), (boardpos.right, boardpos.top + 2*gridsize), 3)
scene.append(heightlimit)

border = Animation(None, None)
border.draw = lambda: draw.rect(screen, outlinecolor, boardpos, 4)
scene.append(border)

scoredisplay = Animation(None, None)
scoredisplay.draw = lambda: screen.blit(scorefont.render(str(score), True, gridcolor), scoreoffset)
scene.append(scoredisplay)

board = Board((boardheight, boardwidth), maxcolor)
boardpos = pygame.Rect((boardoffset, 2*boardoffset), (boardwidth*gridsize, (boardheight+2)*gridsize))
scoreoffset = (boardoffset, boardoffset)
combinecolors = ['green', 'yellow', 'orange', 'red', 'magenta', 'purple', 'blue', 'cyan', 'black', 'white']
combinecolors = [None] + list(map(pygame.Color, combinecolors)) # generate Color objects and put a placeholder in position 0
combinescores = [None, 5, 10, 15, 35, 295, 305, 315, 325, 335, 670]
drop = new_drop(currentcolor)
dropindex = 0
gridcolor = pygame.Color('white')
outlinecolor = pygame.Color('black')

validgroup = lambda l: len(l)>=3

def shutdown():
    pygame.event.clear()
    pygame.quit()
    print(turn, 'turns')
    print(score, 'points')
    quit()

def stateEvent(state):
    pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'state': state}))

# event loop

stateEvent('idle')

while True:
    start = time.clock()

    # check events
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            if   event.button == 1: # left
                stateEvent('drop')
            elif event.button == 4: # wheel
                stateEvent('spinRight')
            elif event.button == 5: # wheel
                stateEvent('spinLeft')
        
        if event.type == pygame.KEYDOWN:
            if   event.key == pygame.K_UP:
                stateEvent('spinRight')
            elif event.key == pygame.K_DOWN or event.key == pygame.K_SPACE:
                stateEvent('drop')
            elif event.key == pygame.K_LEFT:
                stateEvent('moveLeft')
            elif event.key == pygame.K_RIGHT:
                stateEvent('moveRight')
        if event.type == pygame.MOUSEMOTION:
            mouse = event.pos
            # game state is updated inside event handling to allow mouse+keyboard input
            ## Adjust mouse position by the border width, clip that at 0.
            ## Scale down by the size of each square and clip that at piece-width away from the right edge.
            dropwidth = len(drop[0]) if drop else 0
            dropindex = min(max(mouse[0]-boardoffset, 0) // gridsize, boardwidth - dropwidth)
        
        if event.type == pygame.QUIT:
            shutdown()
        
        if event.type == pygame.USEREVENT:
            print(event.state)
            # update stuff
            if event.state == 'spinLeft' and drop:
                drop = spin(drop, 'left')
            elif event.state == 'spinRight' and drop:
                drop = spin(drop, 'right')
            elif event.state == 'moveLeft' and drop:
                dropindex = max(0, dropindex - 1)
            elif event.state == 'moveRight' and drop:
                dropindex = min(dropindex + 1, boardwidth - len(drop[0]))
            elif event.state == 'drop' and drop:
                board.insert(drop, dropindex)
                drop = None
                turn += 1
                stateEvent('moving')
            
            elif event.state == 'moving':
                stateEvent('moving' if board.gravity() else 'breaking')
                frametime = droptime
            elif event.state == 'breaking':
                stateEvent('idle')
                groups = list(filter(validgroup, board.find_groups()))        
                if len(groups) > 0:
                    for group in groups:
                        groupcolor = board[group[0][0]][group[0][1]]
                        currentcolor = max(board.replace_group(group), currentcolor)
                        score += combinescores[groupcolor]*len(group)
                    frametime = breaktime
                    stateEvent('moving')
                else:
                    if board.overheight():
                        stateEvent('gameover')
                    else:
                        drop = new_drop(currentcolor)
                        frametime = idletime
                        stateEvent('idle')
            elif event.state == 'gameover':
                break

    # draw everything on the board
    for prop in scene:
        prop.draw()
        # these aren't going away
    for dot in dots:
        dot.draw()
    
    #colored blockies
    
    for level in range(1, currentcolor):
        r = pygame.Rect(0,0,0,0)
        r.top = 10
        r.height = gridsize/2
        r.left = boardwidth * gridsize - gridsize/2 * len(combinecolors) + gridsize/2 * level
        r.width = gridsize/2
        draw.ellipse(screen, combinecolors[level], pygame.Rect(r.left, r.top, r.width, r.height), 0)
        
    piece = pygame.Rect(boardpos) # to be reused
    piece.width = piece.height = gridsize
    
    if drop:
        # draw drop
        for i in range(0, len(drop)):
            for j in range(0, len(drop[0])):
                piece.top = boardpos.top + (1 - i)*gridsize
                offset = min(dropindex, boardwidth - len(drop[0]))
                piece.left = boardpos.left + (j + offset)*gridsize
                draw.ellipse(screen, combinecolors[drop[i][j]], piece, 0)
    
    # draw pieces
    
    for i in range(0, len(board.grid)):
        piece.bottom = boardpos.bottom - i*gridsize
        for j in range(0, len(board.grid[0])):
            piece.left = boardpos.left + j*gridsize
            if board[i][j] > 0:
                #draw.rect(screen, combinecolors[board[i][j]], piece, 0)
                draw.ellipse(screen, combinecolors[board[i][j]], piece, 0)
    
    pygame.display.flip()

    #timing

    elapsed = time.clock() - start
    if elapsed < frametime:
        time.sleep(frametime - elapsed)

# finally
shutdown()

