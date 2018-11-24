#!/usr/bin/python

import pygame
from pygame import rect, draw, event
import time

from recombinations import *
from abstract_animation import Animation

# game variables

boardheight = 7
boardwidth = 7
combinecolors = ['green', 'yellow', 'orange', 'red', 'magenta', 'purple', 'blue', 'cyan', 'black', 'white']
combinecolors = [None] + list(map(pygame.Color, combinecolors)) # generate Color objects and put a placeholder in position 0
combinescores = [None, 5, 10, 15, 35, 295, 305, 315, 325, 335, 670]
currentcolor = 3
frametime = 1.0/30
gridsize = 40
boardoffset = int(gridsize/2)
maxcolor = 10
mouse = (0, 0)
turn = 0
score = 0


# init

background = set() # behind everything
scene = set() # decorations
dots = set() # dots

pygame.init()
scorefont = pygame.font.Font(pygame.font.get_default_font(), 14)

pygame.display.set_caption('ReCombine')
screen = pygame.display.set_mode((gridsize*boardwidth + 2*boardoffset, gridsize*(boardheight+2) + 3*boardoffset)) # ??

boardpos = pygame.Rect((boardoffset, 2*boardoffset), (boardwidth*gridsize, (boardheight+2)*gridsize))
board = Board(screen, boardpos, (boardheight, boardwidth), maxcolor, combinecolors)
scoreoffset = (boardoffset, boardoffset)

grayfield = Animation(None, None)
grayfield.draw = lambda time: screen.fill(pygame.Color('gray'))
grayfield.ended = lambda time: False
background.add(grayfield)

heightlimit = Animation(None, None)
heightlimit.draw = lambda time: draw.line(screen, gridcolor, (boardpos.left, boardpos.top + 2*gridsize), (boardpos.right, boardpos.top + 2*gridsize), 3)
scene.add(heightlimit)

border = Animation(None, None)
border.draw = lambda time: draw.rect(screen, outlinecolor, boardpos, 4)
scene.add(border)

scoredisplay = Animation(None, None)
scoredisplay.draw = lambda time: screen.blit(scorefont.render(str(score), True, gridcolor), scoreoffset)
scene.add(scoredisplay)

drop = new_drop(currentcolor)
dropindex = 0
gridcolor = pygame.Color('white')
outlinecolor = pygame.Color('black')

validgroup = lambda l: len(l)>=3

def shutdown():
    pygame.event.clear()
    pygame.quit()
    print(str(turn) + ' turns')
    print(str(score) + ' points')
    quit()

def stateEvent(state):
    pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'state': state}))

# event loop

animate = True
stateEvent('idle')

while animate:
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
            elif event.key == pygame.K_ESCAPE:
                stateEvent('gameover')
        if event.type == pygame.MOUSEMOTION:
            # game state is updated inside event handling to allow mouse+keyboard input
            ## Adjust mouse position by the border width, clip that at 0.
            ## Scale down by the size of each square and clip that at piece-width away from the right edge.
            dropwidth = len(drop[0]) if drop else 0
            dropindex = min(max(event.pos[0]-boardoffset, 0) // gridsize, boardwidth - dropwidth)
        
        if event.type == pygame.QUIT:
            shutdown()
        
        if event.type == pygame.USEREVENT:
            #print(event.state)
            #print('')
            #print('\n'.join(map(lambda row: ' '.join(map(lambda ball: str(ball) if ball else '.', row)), board.grid)))
            
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
                added = board.insert(drop, dropindex)
                dots.update(added)
                drop = None
                turn += 1
                stateEvent('moving')
            
            elif event.state == 'moving':
                stateEvent('moving' if len(board.gravity())>0 else 'breaking')
            elif event.state == 'breaking':
                groups = list(filter(validgroup, board.find_groups()))        
                if len(groups) > 0:
                    for group in groups:
                        groupcolor = board[group[0][0]][group[0][1]].color
                        removed, inserted = board.replace_group(group)
                        currentcolor = max(inserted.color, currentcolor)
                        dots.difference_update(removed)
                        dots.add(inserted)
                        score += combinescores[groupcolor]*len(group)
                    stateEvent('moving')
                else:
                    if board.overheight():
                        stateEvent('gameover')
                    else:
                        drop = new_drop(currentcolor)
                        stateEvent('idle')
            elif event.state == 'gameover':
                animate = False
    
    # draw everything on the board
    for distant in background:
        distant.draw(start)
    for prop in scene:
        prop.draw(start)
        # these aren't going away
    for dot in dots:
        dot.draw(start)
    
    #colored blockies
    
    for level in range(1, currentcolor):
        r = pygame.Rect(0,0,0,0)
        r.top = 10
        r.height = gridsize/2
        r.left = boardwidth * gridsize - gridsize/2 * len(combinecolors) + gridsize/2 * level
        r.width = gridsize/2
        draw.ellipse(screen, combinecolors[level], pygame.Rect(r.left, r.top, r.width, r.height), 0)
    
    if drop:
        # draw drop
        for i in range(0, len(drop)):
            for j in range(0, len(drop[0])):
                if drop[i][j]:
                    draw.ellipse(screen, combinecolors[drop[i][j]], board.get_rect(dropindex+j, boardheight+2-i), 0)
   
    
    pygame.display.flip()

    #timing

    elapsed = time.clock() - start
    if elapsed < frametime:
        time.sleep(frametime - elapsed)

# finally
shutdown()

