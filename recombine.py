#!/usr/bin/python3

import pygame
from pygame import draw, Color, event, Rect
import time
from ball import Ball
import board
import random


# game variables

boardheight = 7
boardwidth = 7
combinecolors = ['green', 'yellow', 'orange', 'red', 'magenta', 'purple', 'blue', 'cyan', 'black', 'white']
combinecolors = [None] + list(map(pygame.Color, combinecolors)) # generate Color objects and put a placeholder in position 0
combinescores = [None, 5, 10, 15, 35, 295, 305, 315, 325, 335, 670]
frametime = 1.0/30
gridsize = 40
boardoffset = int(gridsize/2)
maxcolor = len(combinecolors)-1
turn = 0
droptarget = 0
dropindex = 0

def new_drop(maxcolor, start_time):
    newdrop = [
      [ None, None ],
      [
        Ball(gameboard, (1, dropindex), random.randint(1, maxcolor-1)),
        Ball(gameboard, (1, dropindex+1), random.randint(1, maxcolor-1))
      ]
    ]
    newdrop[1][0].appear(start_time, start_time + board.appear_duration)
    newdrop[1][1].appear(start_time, start_time + board.appear_duration)
    return newdrop

def adjust_dropindex(target):
    offset = -1 if drop[0][0] == None and drop[1][0] == None else 0
    dropmax = boardwidth - (1 if drop[0][1] != None or drop [1][1] != None else 0) - 1
    target = min(max(0, target) + offset, dropmax)
    return target
 
def spin(old, direction):
  if old == None:
    return None
  elif direction == 'left':
    return [ [old[0][1], old[1][1]], [old[0][0], old[1][0]] ]
  elif direction == 'right':
    return [ [old[1][0], old[0][0]], [old[1][1], old[0][1]] ]
  else:
    raise ValueError('got "%" instead of left or right' % direction)


pygame.init()

pygame.display.set_caption('ReCombine')
screen = pygame.display.set_mode((gridsize*boardwidth + 2*boardoffset, gridsize*(boardheight+2) + 3*boardoffset)) # ??

boardpos = pygame.Rect((boardoffset, 2*boardoffset), (boardwidth*gridsize, (boardheight+2)*gridsize))
gameboard = board.Board(screen, boardpos, (boardwidth, boardheight), maxcolor, combinecolors, combinescores)

drop = new_drop(gameboard.currentcolor, time.time())

def stateEvent(state):
    pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'state': state}))

def shutdown():
    pygame.event.clear()
    pygame.quit()
    print(str(turn) + ' turns')
    print(str(gameboard.score) + ' points')
    quit()

# event loop

animate = True
while animate:
    start = time.time()
    original_droptarget = droptarget
    
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
            ## clamp mouse position to the board area
            ## adjust bounds based on the shape of the drop
            if drop:
                droptarget = min(max(event.pos[0]-boardoffset, 0) // gridsize, boardwidth)
        
        if event.type == pygame.QUIT:
            shutdown()
        
        if event.type == pygame.USEREVENT:
            #print(event.state)
            # update stuff
            
            if event.state == 'spinLeft' and drop:
                drop = spin(drop, 'left')
                original_droptarget = None
            elif event.state == 'spinRight' and drop:
                drop = spin(drop, 'right')
                original_droptarget = None
            elif event.state == 'moveLeft' and drop:
                droptarget = min(max(0, droptarget - 1), boardwidth)
            elif event.state == 'moveRight' and drop:
                droptarget = min(max(0, droptarget + 1), boardwidth)
            elif event.state == 'drop' and drop:
                added = gameboard.insert(drop, dropindex)
                drop = None
                turn += 1
                stateEvent('moving')
            elif event.state == 'newdrop':
                drop = new_drop(gameboard.currentcolor, start)
                original_droptarget = None
            elif event.state == 'moving':
                if gameboard.ended(start):
                    if gameboard.physics(start):
                        stateEvent('moving')
                    elif gameboard.overheight():
                        stateEvent('gameover')
                    else:
                        stateEvent('ready')
                else:
                    stateEvent('moving')
            elif event.state == 'ready':
                if gameboard.ended(start):
                    stateEvent('newdrop')
                else:
                    stateEvent('ready')
            elif event.state == 'gameover':
                animate = False
            
        if droptarget != original_droptarget:
            dropindex = adjust_dropindex(droptarget)
    
    # draw everything
    gameboard.draw(start)
    
    # draw drop
    # TODO stop doing this manually
    if drop:
        for i in range(0, len(drop)):
            for j in range(0, len(drop[0])):
                ball = drop[i][j]
                if ball:
                    ball.location = gameboard.get_rect(dropindex+j, boardheight+len(drop)-i)
                    ball.draw(start)
   
    
    pygame.display.flip()

    #timing

    elapsed = time.time() - start
    if elapsed < frametime:
        # frame rate throttle
        time.sleep(frametime - elapsed)
# /loop

# finally
shutdown()

