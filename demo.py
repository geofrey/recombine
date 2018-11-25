#!/usr/bin/python3
import pygame
import time
from abstract_animation import Animation

pygame.init()
surface = pygame.display.set_mode((500,500))
window = surface.get_rect()

throttle = 1.0/30

global_y = 0

class Slider(Animation):
    def __init__(self):
        now = time.time()
        super().__init__(now, now+5)
    def draw(self, time):
        if self.started(time) and not self.ended(time):
            x = window.left + self.progress(time) * (window.width)
            pygame.draw.circle(
                surface,
                pygame.Color('red'),
                (int(x), global_y),
                50,
                5
            )

class Seeker(Animation):
    def __init__(self, startpos, endpos):
        now = time.time()
        super().__init__(now+1, now+3)
        self.startpos = startpos
        self.endpos = endpos
        self.rect = pygame.Rect(0, 0, 40, 40)
    def draw(self, time):
        if self.started(time) and not self.ended(time):
            self.rect.centerx = self.startpos[0] + (self.endpos[0] - self.startpos[0]) * self.progress(time)
            self.rect.centery = self.startpos[1] + (self.endpos[1] - self.startpos[1]) * self.progress(time)
            pygame.draw.ellipse(surface, pygame.Color('yellow'), self.rect, 8)

animating = []

running = True
while running:
    framestart = time.time()
    # do things
    
    clicks = pygame.event.get(pygame.MOUSEBUTTONDOWN)
    for click in clicks:
        #animating.append(Slider())
        animating.append(Seeker(click.pos, surface.get_rect().center))
        print('click')
        print(len(animating))
    if len(pygame.event.get(pygame.QUIT))>0:
        print('quit')
        running = False
    
    # throw away everything else
    pygame.event.get()
    
    global_y = int(framestart * 100 % window.height)
    
    pygame.draw.rect(surface, pygame.Color('black'), window)
    
    for animate in animating:
        if animate.started(framestart):
            if animate.ended(framestart):
                animating.remove(animate)
                print('expire')
                print(len(animating))
            else:
                animate.draw(framestart)
    
    pygame.display.flip()
    
    elapsed = time.time() - framestart
    if elapsed < throttle:
        time.sleep((throttle - elapsed)/1000)

pygame.display.quit()
exit()
