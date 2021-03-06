#!/usr/bin/env python

import sys
import random
from random import choice, shuffle
from math import pi, sin
from collections import namedtuple

trisize = 0.035
triscale = 0.9
rotspeed = .3
gentriframes = 1  # new tri every X frames
boundary = 0.8    # edge of world
screenwidth = 1280
screenheight = 720

try:
    from OpenGL.GL import *
    import OpenGL.GLU as glu
    from sdl2 import *
    import sdl2.ext as sdl2ext
except ImportError:
    import traceback
    traceback.print_exc()
    sys.exit(1)

TriTup = namedtuple("TriTup", ['x', 'y', 'ang'])

# find a node with no children
def find_random_leaf(root):
    children = root.trichildren.children
    shuffle(children)
    if len(children):
        # pick random child, return that or one of its children
        shuffle(children)
        for child in children:
            if len(child.trichildren.children):
                return find_random_leaf(child)
            else:
                return child
    else:
        print "returning root"
        return root

class TriGenerator(sdl2ext.Applicator):
    def __init__(self):
        super(TriGenerator, self).__init__()
        self.componenttypes = [ TriPos, TriColor ]
        self.initial = None
        self.existing = {}
        self.neednewleaf = False
    def process(self, world, componentsets):        
        # generate root
        if not self.initial:
            self.initial = Tri(world)
            self.lasttri = self.initial
            return

        # append new
        if world.framecount % gentriframes == 0:
            if self.neednewleaf:
                self.lasttri = find_random_leaf(self.initial)
                if not self.lasttri:
                    print "failed to find new leaf"
                    return
                self.neednewleaf = False

            last = self.lasttri

            lastpos = last.tripos
            ang = lastpos.ang

            # get valid angles for new tri
            seenang = [ ang ]
            # don't want same angle as parent
            if last.triparentang.ang != None:
                seenang.append(last.triparentang.ang)
            # get existing child angles
            for child in last.trichildren.children:
                seenang.append(child.tripos.ang)
            if len(seenang) > 4:
                print "Too many children, can't add new tri"
                return

            # get new unique child angle
            newang = random.randint(0.0, 3.0) * 90.0
            while newang in seenang:
                newang = random.randint(0.0, 3.0) * 90.0

            # position new child according to angles of parent and child
            x = lastpos.x
            y = lastpos.y
            if ang == 0:
                if newang == 90:
                    x -= trisize*2.0
                elif newang == 270:
                    y -= trisize*2.0
            elif ang == 90:
                if newang == 0:
                    x += trisize*2.0
                elif newang == 180:
                    y -= trisize*2.0
            elif ang == 180:
                if newang == 90:
                    y += trisize*2.0
                elif newang == 270:
                    x += trisize*2.0
            elif ang == 270:
                if newang == 0:
                    y += trisize*2.0
                elif newang == 180:
                    x -= trisize*2.0
            else:
                print "unhandled angle: %s" % newang

            if x > boundary or x < 0-boundary or y > boundary or y < 0-boundary:
                # reset
                resetnodes(self.initial)
                self.initial = None
                self.existing = {}
                world.reset_colors()
                return

            # somehow x/y can end up as 0.100000000000003, i do not know why
            # i would love to know why
            x = round(x, 10)
            y = round(y, 10)
            # does something already exist in dest?
            tt = TriTup(x=x, y=y, ang=newang)
            # don't allow partial overlap
            ttl = TriTup(x=x, y=y, ang=((newang+90.0) % 360.0))
            ttr = TriTup(x=x, y=y, ang=((newang+270.0) % 360.0))
            ttf = TriTup(x=x, y=y, ang=((newang+180.0) % 360.0))
            if self.existing.has_key(tt) or self.existing.has_key(ttl) or self.existing.has_key(ttr):
                self.neednewleaf = True
                return
            self.existing[tt] = True

            z = random.uniform(0, 0.05)
            # z = lastpos.z
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
    def draw(self, world, pos, color, children):
        # cubic fade in
        if color.a < 1.0:
            t = (SDL_GetTicks() - self.addedtime) / 300.0
            color.a = 0.001*(t*t*t + 1)
        glPushMatrix()

        zscale = 0 #(sin(world.framecount / 10.0)+1.01)/2.0 * 4
        glTranslatef(pos.x, pos.y, -0.9)
        glRotatef(pos.ang, 0, 0, 1)
        glScalef(triscale, triscale, triscale)
        glBegin(GL_TRIANGLES)
        # glColor4f(color.r / (1+len(children.children)), 0.1, 0.1, color.a)
        glColor4f(color.r, color.g, color.b, color.a)

        glVertex3f(-trisize, trisize, zscale*pos.z)
        glVertex3f(-trisize, -trisize, zscale*pos.z)
        glVertex3f(trisize, -trisize, zscale*pos.z)

        glEnd()
        glPopMatrix()

class Tri(sdl2ext.Entity):
    def __init__(self, world, posx=0.0, posy=0.0, posz=0.0, ang=0.0, parentang=None):
        # calculate color for new triangle
        frame_mod = ((sin(world.framecount / 10) + 1) / 2) / 15  # 0-1/15
        rmin = frame_mod + world.rgb_scale[0]
        rmax = rmin + 0.5*world.rgb_scale[0]
        gmin = frame_mod + world.rgb_scale[1]
        gmax = gmin + 0.5*world.rgb_scale[1]
        bmin = frame_mod + world.rgb_scale[2]
        bmax = bmin + 0.5*world.rgb_scale[2]
        r = random.uniform(rmin, rmax)
        g = random.uniform(gmin, gmax)
        b = random.uniform(bmin, bmax)
        self.tricolor = TriColor(r, g, b, 0.0001)
        self.tripos = TriPos(posx, posy, posz, ang)
        self.trirenderer = TriRenderer()
        self.trichildren = TriChildren()
        self.triparentang = TriParentAng(parentang)

class TriWorld(sdl2ext.World):
    def __init__(self):
        super(TriWorld, self).__init__()
        self.framecount = 0.0
        self.reset_colors()
    def reset_colors(self):
        color_mode = random.randint(0, 5)
        if color_mode == 0:
            self.rgb_scale = (.2, .01, .01)
        elif color_mode == 1:
            self.rgb_scale = (.01, .2, .01)
        elif color_mode == 2:
            self.rgb_scale = (.01, .01, .2)
        elif color_mode == 3:
            self.rgb_scale = (.2, .13, .01)
        elif color_mode == 4:
            self.rgb_scale = (.01, .2, .2)
        elif color_mode == 5:
            self.rgb_scale = (.2, .01, .2)

class WorldRenderer(sdl2ext.Applicator):
    def __init__(self, window):
        super(WorldRenderer, self).__init__()
        self.componenttypes = [ TriRenderer, TriPos, TriColor, TriChildren ]
        self.window = window
        self.rotate_x_speed = 0.01 * rotspeed
        self.rotate_y_speed = 0.20 * rotspeed
        self.rotate_z_speed = 0.50 * rotspeed

        # init gl
        SDL_GL_SetAttribute(SDL_GL_MULTISAMPLEBUFFERS, 1);
        SDL_GL_SetAttribute(SDL_GL_MULTISAMPLESAMPLES,16);
        self.glcontext = SDL_GL_CreateContext(window.window)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    def __del__(self):
        super(WorldRenderer, self)
        SDL_GL_DeleteContext(self.glcontext)
    def process(self, world, componentsets):
        world.framecount += 1.0
        fovy = 60 + sin(world.framecount / 150.0)*15

        glLoadIdentity()
        glu.gluPerspective(fovy, float(screenwidth)/float(screenheight), 0.01, 2);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)

        glPushMatrix()
        ticks = SDL_GetTicks()
        glRotatef(ticks/100.0, self.rotate_x_speed, self.rotate_y_speed, self.rotate_z_speed)
        # render each tri
        for renderer, pos, color, children in componentsets:
            renderer.draw(world, pos, color, children)
        glPopMatrix()
        SDL_GL_SwapWindow(self.window.window)

def run():
    sdl2ext.init()

    # init window
    window = sdl2ext.Window("tri", size=(screenwidth, screenheight), flags=SDL_WINDOW_OPENGL | SDL_WINDOW_FULLSCREEN_DESKTOP)
    window.show()

    # init renderer and generator
    worldrenderer = WorldRenderer(window)
    trigen = TriGenerator()

    # init world
    world = TriWorld()
    world.add_system(worldrenderer)
    world.add_system(trigen)

    # hide cursor
    SDL_ShowCursor(SDL_DISABLE)

    running = True
    while running:
        start = SDL_GetTicks()
        # main loop party time
        events = sdl2ext.get_events()
        for event in events:
            if event.type == SDL_QUIT:
                running = False
                break
        world.process()

        # try and do 60fps
        elapsed = (SDL_GetTicks() - start) / 1000.0
        delay = 16.6 - elapsed
        if delay > 0:
            SDL_Delay(int(delay))

    SDL_ShowCursor(SDL_ENABLE)
    return 0

if __name__ == "__main__":
    sys.exit(run())
