#!/usr/bin/env python
#pip install PyOpenGL PyOpenGL_accelerate

import sys
import random
from math import pi

trisize = 0.05
gentriframes = 5  # new tri every X frames

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
            self.initial = Tri(world)
            self.lasttri = self.initial
            return

        # append new
        self.framecount += 1
        if self.initial == self.lasttri or (self.framecount % gentriframes == 0):
            last = self.lasttri
            lastpos = last.tripos
            ang = lastpos.ang

            # get existing child angles
            seenang = [ ang ]
            # don't want same angle as parent
            if last.triparentang.ang != None:
                seenang.append(last.triparentang.ang)
            for child in last.trichildren.children:
                seenang.append(child.tripos.ang)
            if len(seenang) > 4:
                print "Too many children, can't add new tri"
                return

            # get new unique child angle
            newang = random.randint(0, 3) * 90
            while newang in seenang:
                newang = random.randint(0, 3) * 90

            # position new child according to angles of parent and child
            if ang == 0:
                if newang == 90:
                    x = lastpos.x
                    y = lastpos.y - trisize*2
                elif newang == 180:
                    x = lastpos.x
                    y = lastpos.y
                elif newang == 270:
                    x = lastpos.x - trisize*2
                    y = lastpos.y
            elif ang == 90:
                if newang == 0:
                    x = lastpos.x
                    y = lastpos.y + trisize*2
                elif newang == 180:
                    x = lastpos.x - trisize*2
                    y = lastpos.y
                elif newang == 270:
                    x = lastpos.x
                    y = lastpos.y
            elif ang == 180:
                if newang == 0:
                    x = lastpos.x
                    y = lastpos.y
                elif newang == 90:
                    x = lastpos.x + trisize*2
                    y = lastpos.y
                elif newang == 270:
                    x = lastpos.x + trisize*2
                    y = lastpos.y
            elif ang == 270:
                if newang == 0:
                    x = lastpos.x + trisize*2
                    y = lastpos.y
                elif newang == 90:
                    x = lastpos.x + trisize*2
                    y = lastpos.y
                elif newang == 180:
                    x = lastpos.x
                    y = lastpos.y + trisize*2
            else:
                print "unhandled angle: %s" % newang

            if x > 1 or x < -1 or y > 1 or y < -1:
                # reset
                resetnodes(self.initial)
                self.initial = None
                return

            z = lastpos.z
            t = Tri(world, x, y, z, newang, ang);
            last.trichildren.children.append(t)
            if len(last.trichildren.children) >= 2:
                self.lasttri = t

def resetnodes(root):
    for child in root.trichildren.children:
        resetnodes(child)
        child.delete()

class TriAng(object):
    def __init__(self, ang):
        self.ang = ang
class TriParentAng(TriAng):
    def __init__(self, ang):
        super(TriParentAng, self).__init__(ang)
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
class TriChildren(object):
    def __init__(self):
        self.children = []
class TriRenderer(object):
    def __init__(self):
        self.addedtime = SDL_GetTicks()
    def draw(self, pos, color):
        # cubic fade in
        if color.a < 1.0:
            t = (SDL_GetTicks() - self.addedtime) / 150.0
            color.a = 0.001*(t*t*t + 1)
        glPushMatrix()

        glTranslatef(pos.x, pos.y, pos.z)
        glRotatef(pos.ang, 0, 0, 1)
        glScalef(0.90, 0.90, 0.90)
        glBegin(GL_TRIANGLES)
        glColor4f(color.r, color.g, color.b, color.a)

        glVertex3f(-trisize, trisize, 0)
        glVertex3f(-trisize, -trisize, 0)
        glVertex3f(trisize, -trisize, 0)

        glEnd()
        glPopMatrix()

class Tri(sdl2ext.Entity):
    def __init__(self, world, posx=0, posy=0, posz=0, ang=0, parentang=None):
        r = random.uniform(0.8, 1.0)
        g = random.uniform(0.8, 1.0)
        b = random.uniform(0.1, 0.2)
        self.tricolor = TriColor(r, g, b, 0.0001)
        self.tripos = TriPos(posx, posy, posz, ang)
        self.trirenderer = TriRenderer()
        self.trichildren = TriChildren()
        self.triparentang = TriParentAng(parentang)

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
