#!/usr/bin/env python
#pip install PyOpenGL PyOpenGL_accelerate

import sys
import random
from math import pi

try:
    from OpenGL.GL import *
    from sdl2 import *
    import sdl2.ext as sdl2ext
except ImportError:
    import traceback
    traceback.print_exc()
    sys.exit(1)

class TriGenerator(sdl2ext.Applicator):
    def __init__(self):
        super(TriGenerator, self).__init__()
        self.componenttypes = [ TriPos, TriColor ]
        self.framecount = 0
        self.initial = None
    def process(self, world, componentsets):
        # generate initial
        if not self.initial:
            self.initial = Tri(world, 0, 0, 0, 0)
            self.last = self.initial
            return

        # append new
        self.framecount += 1
        for pos, color in componentsets:
            # append triangle
            True
        if (self.framecount % 60 == 0):
            x = random.random() * 2 - 1
            y = random.random() * 2 - 1
            z = random.random() * 2 - 1
            ang = random.randint(0, 3) * 90
            t = Tri(world, x, y, z, ang);

class TriPos(object):
    def __init__(self, posx, posy, posz, ang):
        self.x = posx
        self.y = posy
        self.z = posz
        self.ang = ang
class TriColor(object):
    def __init__(self, r, g, b, a):
        self.r = r
        self.g = g
        self.b = b
        self.a = a
class TriRenderer(object):
    def __init__(self):
        self.addedtime = SDL_GetTicks()
    def draw(self, pos, color):
        # cubic fade in
        if color.a < 1.0:
            t = (SDL_GetTicks() - self.addedtime) / 150.0
            color.a = 0.001*(t*t*t + 1)
        glPushMatrix()
        size = 0.04
        glTranslatef(pos.x, pos.y, pos.z)
        glRotatef(pos.ang, 0, 0, 1)
        glBegin(GL_TRIANGLES)
        glColor4f(color.r, color.g, color.b, color.a)
        glVertex3f(-size, size, 0)
        glVertex3f(-size, -size, 0)
        glVertex3f(size, size, 0)
        glEnd()
        glPopMatrix()

class Tri(sdl2ext.Entity):
    def __init__(self, world, posx=0, posy=0, posz=0, ang=0):
        r = random.uniform(0.8, 1.0)
        g = random.uniform(0.8, 1.0)
        b = random.uniform(0.1, 0.2)
        self.tricolor = TriColor(r, g, b, 0.0001)
        self.tripos = TriPos(posx, posy, posz, ang)
        self.trirenderer = TriRenderer()

class WorldRenderer(sdl2ext.Applicator):
    def __init__(self, window):
        super(WorldRenderer, self).__init__()
        self.componenttypes = [ TriRenderer, TriPos, TriColor ]
        self.window = window
        self.rotate_x_speed = 0.01
        self.rotate_y_speed = 0.01
        self.rotate_z_speed = 1.0

        # init gl
        # SDL_GL_SetAttribute(SDL_GL_ALPHA_SIZE, 8)
        SDL_GL_SetAttribute(SDL_GL_MULTISAMPLEBUFFERS, 1);
        SDL_GL_SetAttribute(SDL_GL_MULTISAMPLESAMPLES,16);
        self.glcontext = SDL_GL_CreateContext(window.window)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLoadIdentity()

    def __del__(self):
        super(WorldRenderer, self)
        SDL_GL_DeleteContext(self.glcontext)

    def process(self, world, componentsets):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # glMatrixMode(GL_PROJECTION | GL_MODELVIEW)
        glPushMatrix()
        ticks = SDL_GetTicks()
        glRotatef(ticks/300.0, self.rotate_x_speed, self.rotate_y_speed, self.rotate_z_speed)
        for renderer, pos, color in componentsets:
            renderer.draw(pos, color)
        glPopMatrix()
        SDL_GL_SwapWindow(self.window.window)

def run():
    sdl2ext.init()

    # init window
    window = sdl2ext.Window("tri", size=(1280, 800), flags=SDL_WINDOW_OPENGL|SDL_WINDOW_FULLSCREEN_DESKTOP)
    window.show()

    worldrenderer = WorldRenderer(window)
    trigen = TriGenerator()

    world = sdl2ext.World()
    world.add_system(worldrenderer)
    world.add_system(trigen)

    running = True
    while running:
        events = sdl2ext.get_events()
        for event in events:
            if event.type == SDL_QUIT:
                running = False
                break
        world.process()
        SDL_Delay(5)
    return 0

if __name__ == "__main__":
    sys.exit(run())
