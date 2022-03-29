import math
import time
import random
import os
import ast
import winsound
from pathlib import Path

try:
    import ctypes

    USER32 = ctypes.windll.user32

except ImportError:
    # If user is not on a windows system, win32api will fail to import, 
    # and the program will instead use default window size
    USER32 = False

import pygame as pg
import pygame.math as pgmath
from pygame.locals import *

# An external library that I made - adds tkinter features in pygame
import pgkinter as pgk

pgkRoot = pgk.Pgk()


# Used to draw a line that follows a particle's path
class Graph(object):
    def __init__(self, surface, width, height, topleft, bgColour, xLabelGap,
                 yLabelGap):
        self.__screen = surface

        self.__width = width

        self.__height = height

        self.__bgColour = bgColour

        self.__rect = pg.Rect(0, 0, self.__width, self.__height)

        self.__rect.topleft = (int(topleft[0]), int(topleft[1]))

        self.__xLabels = []
        x = width
        while x > 0:
            self.__xLabels.append(width - x)
            x -= xLabelGap

        self.__yLabels = []
        y = height
        while y > 0:
            self.__yLabels.append(height - y)
            y -= yLabelGap

        self.__font = pg.font.SysFont("Helvetica", 18)

        self.lines = []

    def draw(self):

        pg.draw.rect(self.__screen, self.__bgColour, self.__rect)

        for i in self.__xLabels:
            pg.draw.line(self.__screen, (170, 170, 170),
                         (i, self.__rect.top), (i, self.__rect.bottom), 1)

        for i in self.__yLabels:
            pg.draw.line(self.__screen, (170, 170, 170),
                         (self.__rect.left, i), (self.__rect.right, i), 1)

        for i in self.lines:
            i.draw()

    def changeLabelGap(self, xLabelGap, yLabelGap):
        self.__xLabels = []
        x = self.__width
        while x > 0:
            self.__xLabels.append(self.__width - x)
            x -= xLabelGap

        self.__yLabels = []
        y = 0
        while y < self.__height:
            self.__yLabels.append(self.__height - y)
            y += yLabelGap

    def clearLines(self):
        for i in self.lines:
            del i

        self.lines = []


class Line(object):
    def __init__(self, surface, graph, colour):
        self.__screen = surface

        graph.lines.append(self)

        self.__colour = colour

        self.__plotCoords = []

    def draw(self):
        plots = self.__plotCoords

        if len(plots) > 1:
            pg.draw.lines(self.__screen, self.__colour, False, plots, 2)

    def addPlot(self, plot):
        self.__plotCoords.append((int(plot[0]), int(plot[1])))


class Particle(pg.sprite.Sprite):

    def __init__(self, coefficient, material, rad, density, v, colour, centre,
                 yA, xA=None):
        super().__init__()  # Runs pygame sprite __init__() method

        self.hasRandomVelocity = False
        self.line = False
        self.restCoefficient = coefficient
        self.material = material
        self.radius = rad
        self.density = density
        self.mass = 0
        self.vol = 0
        self.updateDimension(rad=self.radius)
        self.velocity = pgmath.Vector2(v)
        self.colour = colour
        self.rect = pg.draw.circle(screen, self.colour, centre,
                                   int(self.radius * scale))
        self.rect.x += int(self.radius * scale)
        self.rect.y += int(self.radius * scale)
        self.pos = pgmath.Vector2(self.rect.x, self.rect.y)
        if not xA:  # Assigns 0 as default x acceleration, if no value is passed
            self.acceleration = pgmath.Vector2(0, yA)
        else:
            self.acceleration = pgmath.Vector2(xA, yA)

        self.direction = 0
        self.updateDirection()

        # Dictionary storing data on each frame
        self.posDict = {
            0: (pgmath.Vector2(centre), pgmath.Vector2(v), tNow)
        }
        self.recentCollisions = []

    def angleTo(self, p2):
        xDistance = self.pos.x - p2.pos.x
        yDistance = self.pos.y - p2.pos.y

        # Uses inverse tan function on two lengths. Need to add pi/2 (90deg)
        # in order to align with pygame angles (measured from vertical)

        return math.atan2(xDistance, yDistance) + math.pi / 2

    def collide(self, p2):
        collisionDir = self.angleTo(p2)
        
        # Particles have collided - calculate new velocities
        m1, m2 = self.mass, p2.mass
        v1, v2 = self.velocity, p2.velocity
        pos1, pos2 = self.pos, p2.pos

        selfNewVelocity = v1 - ((2 * m2) / (m1 + m2)) * (
                ((v1 - v2).dot(pos1 - pos2)) / (
            (pos1 - pos2).length()) ** 2) * (pos1 - pos2)
        p2NewVelocity = v2 - ((2 * m1) / (m2 + m1)) * (
                ((v2 - v1).dot(pos2 - pos1)) / (
            (pos2 - pos1).length()) ** 2) * (pos2 - pos1)

        self.velocity, p2.velocity = selfNewVelocity, p2NewVelocity

    def delete(self):
        particles.remove(self)
        del self

    def draw(self):
        pg.draw.circle(screen, self.colour, (self.rect.x, self.rect.y),
                       int(self.radius * scale))

    def drawDirectionArrow(self):
        arrow = ARROW_IMAGE  # Prevents having to load image every time
        arrowscale = (self.radius * scale / arrow.get_width()) * 1.5
        # Rotate and scale arrow image to fit particle
        arrow = pg.transform.rotozoom(arrow, math.degrees(self.direction),
                                      arrowscale)
        arrowRect = arrow.get_rect(center=(self.rect.x, self.rect.y))
        screen.blit(arrow, arrowRect)

    def hasCollided(self, group):
        collisionList = []
        # Checks each sprite in the group and if the sum of their radii is less
        # than the absolute distance between their centres, they have collided.
        for sprite in group.sprites():
            totalRad = self.radius * scale + sprite.radius * scale
            if absoluteDistance(self.pos, sprite.pos) <= totalRad \
                    and sprite != self:
                collisionList.append(sprite)

        return collisionList

    def scalePosition(self):
        # If the scale has changed since last frame, then the particle will
        # get resized and relocated, so that it will be in the same place
        # relative to the window and other particles.
        if previousScale != scale:
            mouseX = pg.mouse.get_pos()[0]
            fromMouseX = mouseX - self.pos.x
            self.pos.x = mouseX - (fromMouseX * (scale / previousScale))
            fromFloor = SH - self.pos.y
            self.pos.y = SH - (fromFloor * (scale / previousScale))
            self.rect.x, self.rect.y = int(self.pos.x), int(self.pos.y)
        else:
            pass

    def updateDirection(self):
        # Gets direction of travel (in radians)
        # Multiply by -1 as pygame measures angles anti-clockwise.
        self.direction = math.atan2(self.velocity.y, self.velocity.x) * -1

    def updateDimension(self, rad=None, mass=None):
        # Apply equation v=(4/3)*pi*r^2 and v=m/d to update particles radius if
        # mass is changed, and vice-versa
        if rad is not None:
            self.radius = rad
            self.vol = (4 / 3) * math.pi * (self.radius ** 3)
            self.mass = roundToSigFig(self.vol * self.density, 3)

        elif mass is not None:
            self.mass = mass
            self.vol = self.mass / self.density
            rad = ((3 * self.vol) / (4 * math.pi)) ** (1 / 3)
            self.radius = roundToSigFig(rad, 3)

    def update(self):
        global frameNumber
        global tNow

        self.scalePosition()

        # If time is moving backwards
        if TIME_SCALES[currentTimescale] < 0:
            try:
                # Sets attributes to what they were at the current frame number
                p = self.posDict[frameNumber]
                self.pos = pgmath.Vector2(p[0].x, p[0].y)
                self.velocity = pgmath.Vector2(p[1].x, p[1].y)
                tNow = p[2]

            except KeyError:
                pass

            self.updateDirection()

            self.rect.x, self.rect.y = int(self.pos.x), int(self.pos.y)
            self.draw()
            self.drawDirectionArrow()

        # If time is moving forward
        elif TIME_SCALES[currentTimescale] > 0:

            # Only simulate particle's motion if current frame has not
            # already been simulated, otherwise simply retrieve its
            # positional data from the position dictionary
            if frameNumber not in self.posDict:
                # Checks if particle has collided with floor. Also checks
                # that particle's velocity would take it towards the floor
                # in order to make sure that the particle hasn't collided and
                # was turned around in the previous frame.
                if self.pos.y + self.radius * scale >= SH and \
                        self.velocity.y * timeMultiplier > 0:
                    self.velocity.y = roundToSigFig(
                        self.velocity.y * self.restCoefficient * -1, 4)
                    self.pos.y = SH - self.radius * scale

                # Has collided with ceiling
                elif self.pos.y - self.radius * scale <= 0 and \
                        self.velocity.y * timeMultiplier < 0:
                    self.velocity.y = roundToSigFig(
                        self.velocity.y * self.restCoefficient * -1, 4)
                    self.pos.y = 0 + self.radius * scale

                # Has collided with right wall
                if self.pos.x + self.radius * scale >= SW and \
                        self.velocity.x * timeMultiplier > 0:
                    self.velocity.x = roundToSigFig(
                        self.velocity.x * self.restCoefficient * -1, 4)
                    self.pos.x = SW - self.radius * scale

                # Has collided with left wall
                elif self.pos.x - self.radius * scale <= 0 and \
                        self.velocity.x * timeMultiplier < 0:
                    self.velocity.x = roundToSigFig(
                        self.velocity.x * self.restCoefficient * -1, 4)
                    self.pos.x = 0 + self.radius * scale
                #
                # Multiply by timeMultiplier in order to increase velocity by
                # the correct amount per second.
                self.velocity += self.acceleration * timeMultiplier

                self.updateDirection()

                # Multiply by scale as velocity is ms^-1, multiply by
                # timeMultiplier for the same reasons as before
                self.pos += self.velocity * scale * timeMultiplier

                # Rect coordinates need to be integers
                self.rect.x, self.rect.y = int(self.pos.x), int(self.pos.y)
                self.draw()
                self.drawDirectionArrow()
                collisionList = self.hasCollided(particles)
                for particle in collisionList:
                    # Self is included in collisionList, therefore != self
                    # check is required

                    # Also need to check if the particles are moving closer,
                    # otherwise two that collided last frame wil be treated as
                    # colliding again this frame.
                    if particle != self and particle not in \
                            self.recentCollisions:
                        # Need to both add the other particle to this
                        # particle's recentCollisions list, and the other way
                        # round. If I just added the other particle to this
                        # particle's collisions list, they would
                        # occasionally 'collide' twice, as the if not in
                        # self.recentCollisions check would pass in both
                        # particles' update methods
                        self.collide(particle)
                        self.recentCollisions.append(particle)
                        particle.recentCollisions.append(self)

                for particle in self.recentCollisions:
                    if particle not in collisionList:
                        self.recentCollisions.remove(particle)
                        particle.recentCollisions.remove(self)

                if self.line:
                    self.line.addPlot((self.pos.x, self.pos.y))

            elif frameNumber in self.posDict:
                # If current frame has already been simulated, grab values
                # from posDict
                p = self.posDict[frameNumber]
                self.pos = pgmath.Vector2(p[0].x, p[0].y)
                self.velocity = pgmath.Vector2(p[1].x, p[1].y)
                tNow = p[2]
                self.updateDirection()

                self.rect.x, self.rect.y = int(self.pos.x), int(self.pos.y)
                self.draw()
                self.drawDirectionArrow()

            p = pgmath.Vector2(self.pos.x, self.pos.y)
            v = pgmath.Vector2(self.velocity.x, self.velocity.y)

            # If time is set to x2 speed
            if currentTimescale == 5:
                # Need to add data to previous 1 and 1.5 frames
                # Interpolates what the position and velocity will be based
                # on current velocity and acceleration
                if (frameNumber - 1.5) not in self.posDict:
                    olderPos = p - (v * scale * timeMultiplier * 1.5)
                    self.posDict[frameNumber - 1.5] = (olderPos, v, tNow)

                if (frameNumber - 1) not in self.posDict:
                    oldPos = p - (v * scale * timeMultiplier)
                    self.posDict[frameNumber - 1] = (oldPos, v, tNow)

            # x1 or x2
            if currentTimescale in [4, 5]:
                # Need to add data to previous 1/2 of a frame
                # Interpolates what the position and velocity will be based
                # on current velocity and acceleration
                if (frameNumber - 0.5) not in self.posDict:
                    oldPos = p - (
                            v * scale * timeMultiplier * 0.5)
                    self.posDict[frameNumber - 0.5] = (oldPos, v, tNow)

            if frameNumber not in self.posDict:
                # Will always add data for the current frame if it is not
                # already in the dictionary
                self.posDict[frameNumber] = (p, v, tNow)

            # All of these checks mean that every frame (and the half frames
            # in between them) will be included in the dictionary, allowing
            # the user to rewind through at any speed.


def absoluteDistance(pVector1, pVector2):
    distance = pVector1 - pVector2
    return distance.length()


def drawDottedLine(start, end):
    # Used when resizing particles, to create the same look as in Blender
    # (Dotted line from the centre of the object being resized to the mouse)
    xLen = end[0] - start[0]
    yLen = end[1] - start[1]

    xStep = xLen / 10
    yStep = yLen / 10

    xCoord = start[0]
    yCoord = start[1]

    for i in range(0, 5):
        pg.draw.line(screen, (33, 33, 33), (xCoord, yCoord),
                     (xCoord + xStep, yCoord + yStep), 2)
        xCoord += 2 * xStep
        yCoord += 2 * yStep


# Code snippet found online - rounds a number, x, to a given number of
# significant figures, n.
def roundToSigFig(x, n):
    if x != 0:
        return round(x, -int(math.floor(math.log10(abs(x)))) + (n - 1))
    else:
        return 0


def timeChange(speedUp):
    global currentTimescale

    # User can only speed up if the current timescale is at most one less
    # than the maximum. Similarly, they can only decrease the timescale if it
    # is a least one more than the minimum. This is to prevent the timescale
    # from going out of bounds.
    if 0 <= currentTimescale < len(TIME_SCALES) - 1 and speedUp == 1:
        currentTimescale += 1
    elif 0 < currentTimescale <= len(TIME_SCALES) - 1 and speedUp == -1:
        currentTimescale -= 1


# Each procedure which contains a loop needs to have at least one argument,
# whether it is used or not, as the loop that prevents recursion needs to
# pass an argument (it passes *args, which cannot pass nothing). So I put a
# dummy argument in the procedures that don't need anything to be passed to
# them.
def mainMenu(dummyArg):
    global mainmenu
    global mainWidgets
    global currentTimescale
    global tNow
    global frameNumber
    global particleGraph
    global scale
    global previousScale

    def endFunction(widgets, goTo, args):
        # Can't use buttons to set variables, so I need to use this function
        # to set global variables that will be
        global nextFunc
        global nextArgs
        global mainmenu

        if goTo == instructions:
            instructions(*args)
            return

        widgets[-1].startAnimation("horizontalslide", 0.5, "out", 0 - SW, True)

        mainmenu, nextFunc, nextArgs = False, goTo, args

    def exitProgram():
        pg.quit()
        quit()

    global timeMultiplier
    dvdLogo = pg.image.load(
        str(imagesFolder / "DVDlogo.png")).convert_alpha()

    dvdLogo = pg.transform.scale(dvdLogo, (int(scaler(262, "x")), int(scaler(
        150, "y"))))

    x = random.randint(int(SW * 0.1), int(SW * 0.9))
    y = random.randint(int(SH * 0.1), int(SH * 0.9))

    dvdRect = dvdLogo.get_rect(center=(x, y))

    dvdXSpeed = random.choice([1, -1])
    dvdYSpeed = random.choice([1, -1])

    # Uncomment to hit corner
    #    x = 500
    #   y = 500
    #
    # dvdRect = dvdLogo.get_rect(topleft=(x, y))

    # dvdXSpeed = random.choice([-1])
    # dvdYSpeed = random.choice([-1])

    # Reset scale nd time-related globals to their default values - prevents
    # bugs when going from a simulation to the menu, and then into another
    # simulation
    currentTimescale = 4
    tNow = 0
    frameNumber = 0

    scale = scaler(100, "x")
    previousScale = scale

    particleGraph.clearLines()
    del particleGraph

    particleGraph = Graph(screen, SW, SH, (0, 0), BG_COLOUR, scale, scale)

    mainContainer = pgk.Container(pgkRoot, screen, topleft=(0, 0),
                                  width=SW, height=SH)

    mainWidgets = [
        pgk.Label(pgkRoot, screen, centre=(SW / 2, scaler(135, "y")),
                  font=LARGE_FONT,
                  text="Particle Simulator V3 or something idk",
                  container=mainContainer),
        pgk.Label(pgkRoot, screen, centre=(SW / 2, scaler(200, "y")),
                  font=SMALL_FONT,
                  text="'A man dies, when he is forgotten' - Theo",
                  container=mainContainer)
    ]

    buttonX = scaler(640, "x")

    mainWidgets += [
        pgk.Button(pgkRoot, screen, buttonX, scaler(425, "y"), font=MID_FONT,
                   bgColour=(33, 33, 33), text="Create a simulation",
                   height=scaler(115, "y"), width=scaler(640, "x"),
                   action=lambda: endFunction(mainWidgets, setup, (1,)),
                   container=mainContainer, swellOnHover=True),
        pgk.Button(pgkRoot, screen, buttonX, scaler(560, "y"), font=MID_FONT,
                   bgColour=(33, 33, 33), text="Load a saved simulation",
                   height=scaler(115, "y"), width=scaler(640, "x"),
                   action=lambda: endFunction(mainWidgets, loadSetup,
                                              (None,)),
                   container=mainContainer, swellOnHover=True),
        pgk.Button(pgkRoot, screen, buttonX, scaler(695, "y"), font=MID_FONT,
                   bgColour=(33, 33, 33), text="Instructions",
                   height=scaler(115, "y"), width=scaler(640, "x"),
                   action=lambda: endFunction(mainWidgets, instructions,
                                              (mainWidgets,)),
                   container=mainContainer, swellOnHover=True),
        pgk.Button(pgkRoot, screen, buttonX, scaler(830, "y"), font=MID_FONT,
                   bgColour=(33, 33, 33), text="Exit program :(",
                   height=scaler(115, "y"), width=scaler(640, "x"),
                   action=exitProgram,
                   container=mainContainer, swellOnHover=True),
    ]

    mainWidgets.append(mainContainer)

    del mainContainer

    mainWidgets[-1].startAnimation("horizontalslide", 0.5, "in", SW)

    mainmenu = True
    while mainmenu:
        for event in pg.event.get():
            pgkRoot.eventHandler(event)
            if event.type == QUIT:
                mainmenu = False
                pg.quit()
                quit()

        try:
            # If statement prevents 'jumping' of particles when user moves
            # the window
            if time.time() - previousFrame < 0.1:
                timeMultiplier = (time.time() - previousFrame)
                timeMultiplier *= TIME_SCALES[currentTimescale]
                # Calculates time between frames
                previousFrame = time.time()
        except NameError:
            # Will occur on the first frame, as there is no previous frame
            pass

        screen.fill(BG_COLOUR)

        if dvdRect.left <= 0 or dvdRect.right >= SW:
            dvdXSpeed = -dvdXSpeed
        if dvdRect.top <= 0 or dvdRect.bottom >= SH:
            dvdYSpeed = -dvdYSpeed

        dvdRect.x += dvdXSpeed
        dvdRect.y += dvdYSpeed
        screen.blit(dvdLogo, dvdRect)

        pgkRoot.update()

        pg.display.update()

        fps = str(int(clock.get_fps()))
        pg.display.set_caption('HAHA CIRCLE GO BRR | FPS: ' + fps)
        clock.tick()

    # Returns the function that runs next (setup) and the args to pass to that 
    # function (*args requires a tuple to unpack)
    return nextFunc, nextArgs


def instructions(mainMenuWidgets):
    global instructing

    def changePage(goToPage, pages, mainMenuWidgets):
        global instructing

        # First page slides to the right and gets deleted, main menu slides
        # back in from the left, and delete the second page
        if goToPage == -1:
            pages[0][-1].startAnimation("horizontalslide", 0.5, "out", SW, True)
            mainMenuWidgets[-1].startAnimation("horizontalslide", 0.5, "out", 0)
            for i in pages[1]:
                i.delete()

            instructing = False

        # First page slides to the left, second page slides in from the right
        elif goToPage == 0:
            pages[1][-1].startAnimation("horizontalslide", 0.5, "out", SW)
            pages[0][-1].startAnimation("horizontalslide", 0.5, "out", 0)

        # Second page slides to the right, second page slides in from the left
        elif goToPage == 1:
            pages[0][-1].startAnimation("horizontalslide", 0.5, "out", 0 - SW)
            pages[1][-1].startAnimation("horizontalslide", 0.5, "in", SW,
                                        destination=(0, 0))

        # Second page slides to the left and gets deleted, main menu slides
        # back in from the right, and delete the first page
        elif goToPage == 2:
            pages[1][-1].startAnimation("horizontalslide", 0.5, "out", 0 - SW,
                                        True)
            mainMenuWidgets[-1].startAnimation("horizontalslide", 0.5, "out",
                                               0, destination=(SW, 0))
            for i in pages[0]:
                i.delete()

            instructing = False

    mainMenuWidgets[-1].startAnimation("horizontalslide", 0.5, "out", 0 - SW)

    files = ["setupInstructions.txt", "mainInstructions.txt"]
    pageTitles = ["Setup", "Simulation"]
    pages = []
    currentPage = 0

    for i in files:
        # Iterate through instruction files, creating labels and buttons
        with open(i, "r") as f:
            lines = f.readlines()

        text = ''.join(lines)

        pageContainer = pgk.Container(pgkRoot, screen, topleft=(0, SW),
                                      width=SW, height=SH)
        page = [
            pgk.Label(pgkRoot, screen, centre=(SW / 2, scaler(135, "y")),
                      font=LARGE_FONT, text=pageTitles[currentPage],
                      container=pageContainer),
            pgk.Label(pgkRoot, screen, centre=(SW / 2,
                                               SH / 2 + scaler(135, "y")),
                      height=SH - scaler(135, "x"), width=SW * 0.8,
                      font=MID_FONT, text=text, container=pageContainer),
        ]

        # Need to explicitly state the page values for the buttons - can't
        # use currentPage + or - 1. This is because lambda passes the
        # arguments as they are at the time of the button press. In this case
        # that means that the previous page button will always pass 1,
        # and the next page will always pass 3.
        if currentPage == 0:
            page += [
                pgk.Button(pgkRoot, screen, 0, 0, height=SH, width=int(SW / 10),
                           action=lambda: changePage(-1, pages,
                                                     mainMenuWidgets),
                           image=L_MENU_IMG, hoverImage=L_MENU_IMG,
                           container=pageContainer),
                pgk.Button(pgkRoot, screen, SW - int(SW / 10), 0, height=SH,
                           width=int(SW / 10),
                           action=lambda: changePage(1, pages,
                                                     mainMenuWidgets),
                           image=NEXT_IMG, hoverImage=NEXT_IMG,
                           container=pageContainer),
                pageContainer
            ]

        else:
            page += [
                pgk.Button(pgkRoot, screen, 0, 0, height=SH, width=int(SW / 10),
                           action=lambda: changePage(0, pages,
                                                     mainMenuWidgets),
                           image=PREV_IMG, hoverImage=PREV_IMG,
                           container=pageContainer),
                pgk.Button(pgkRoot, screen, SW - int(SW / 10), 0, height=SH,
                           width=int(SW / 10),
                           action=lambda: changePage(2, pages,
                                                     mainMenuWidgets),
                           image=R_MENU_IMG, hoverImage=R_MENU_IMG,
                           container=pageContainer),
                pageContainer
            ]

        del pageContainer

        pages.append(page)

        currentPage += 1

    pages[0][-1].startAnimation("horizontalslide", 0.5, "in", SW,
                                destination=(0, 0))

    instructing = True
    while instructing:
        for event in pg.event.get():
            pgkRoot.eventHandler(event)
            if event.type == QUIT:
                instructing = False
                pg.quit()
                quit()

        screen.fill(BG_COLOUR)

        pgkRoot.update()

        pg.display.update()

        fps = str(int(clock.get_fps()))
        pg.display.set_caption('HAHA CIRCLE GO BRR | FPS: ' + fps)
        clock.tick()

    return


def setup(dummyArg):
    global scale
    global previousScale
    global setupTime
    global setting
    global editingParticle

    # Times the animation for setupContainer
    setupTime = None
    # Controls setup loop
    setting = True
    # List of widgets used when editing a placed particle
    editList = None
    # The particle being edited
    editingParticle = None

    # How many metres are shown in the scale display
    metres = 1

    def endFunction(widgetList):
        # Starts the setupContainer's slide out animation
        widgetList[-1].startAnimation("horizontalslide", 0.1, "out",
                                      SW + contWidth, deleteAfter=True)

    def endParticleEdit(editList):
        global editingParticle
        # Menu for editing a particle will disappear
        editList[-1].startAnimation("centre", 0.25, "out", deleteAfter=True)
        editingParticle = None

    # Delete all widgets - to start with a 'clean slate'
    # for i in pgkRoot.pgkGroup.sprites():
    #    i.delete()

    def updateParticle(pRef, inputs, editing=None):
        # Editing argument specifies whether or not the particle being
        # updated has already been placed
        try:
            # Easier to add new inputs - only need to change index here
            coefficientBox = inputs[0]
            coefficient = float(inputs[0].get())
            xVel = float(inputs[1].get())
            yVel = float(inputs[2].get())
            xAccel = float(inputs[3].get())
            yAccel = float(inputs[4].get())
            radBox = inputs[5]
            rad = float(radBox.get())
            massBox = inputs[6]
            mass = float(massBox.get())
            height = float(inputs[7].get())
            lockHeight = inputs[8].get()
            randomV = inputs[9].get()
            drawGraph = inputs[10].get()
            material = inputs[11].get()
            if material in MATERIALS:
                density, colour = MATERIALS[material][0], MATERIALS[material][1]
            else:
                density, colour = customMaterials[material][0], \
                                  customMaterials[material][1]

            pRef.colour = colour
        except ValueError:
            return

        mouseX = pg.mouse.get_pos()[0]
        mouseY = pg.mouse.get_pos()[1]

        if coefficient > 1:
            coefficientBox.write("1")
        elif coefficient < 0:
            coefficientBox.write("0")

        else:
            pRef.restCoefficient = coefficient

        if not randomV:
            pRef.velocity.x = xVel
            pRef.velocity.y = yVel
            pRef.hasRandomVelocity = False
        elif randomV and not pRef.hasRandomVelocity:
            upper = pRef.radius * 5
            lower = upper * -1

            # random.uniform instead of random.randint as uniform allows for
            # two floating point numbers as the bounds
            pRef.velocity.x = roundToSigFig(random.uniform(lower, upper), 3)
            pRef.velocity.y = roundToSigFig(random.uniform(lower, upper), 3)

            inputs[1].write(str(pRef.velocity.x))
            inputs[2].write(str(pRef.velocity.y))
            pRef.hasRandomVelocity = True

        if not drawGraph and pRef.line:
            pRef.line = False

        elif drawGraph and not pRef.line:
            pRef.line = Line(screen, particleGraph, colour)

        pRef.acceleration.x = xAccel
        pRef.acceleration.y = yAccel

        # If user has selected that they want the particle to be locked to a
        # certain height
        if lockHeight:
            if editing is None:
                pRef.pos.x = mouseX
                pRef.rect.x = mouseX
            pRef.pos.y = SH - int(height * scale) - pRef.radius * scale
            pRef.rect.y = SH - int(height * scale) - pRef.radius * scale
        else:
            if editing is None:
                pRef.pos.x = mouseX
                pRef.pos.y = mouseY
                pRef.rect.x = mouseX
                pRef.rect.y = mouseY

        minRad = roundToSigFig(scaler(10, "x") / scale, 3)
        maxRad = roundToSigFig((SW / 4) / scale, 3)

        # Only update particle's radius/mass if they are not already equal to
        # the values entered by the user
        if density != pRef.density:
            pRef.density = density
            pRef.colour = colour
            pRef.updateDimension(rad=rad)
            radBox.write(str(pRef.radius))
            massBox.write(str(pRef.mass))

        elif rad != pRef.radius and minRad <= rad <= maxRad:
            pRef.updateDimension(rad=rad)
            massBox.write(str(pRef.mass))

        elif mass != pRef.mass:
            pRef.updateDimension(mass=mass)
            radBox.write(str(pRef.radius))

        if pRef.radius > maxRad:
            pRef.updateDimension(rad=roundToSigFig((SW / 4) / scale, 3))
            radBox.write(str(pRef.radius))
            massBox.write(str(pRef.mass))

        elif pRef.radius < minRad:
            pRef.updateDimension(rad=roundToSigFig(scaler(10, "x") / scale, 3))
            radBox.write(str(pRef.radius))
            massBox.write(str(pRef.mass))

        pRef.material = material

    def deleteParticle(particle):
        particle.delete()

    def clearParticles():
        for particle in particles.sprites():
            particle.delete()

        particles.add(Particle(1, "Custom Material 1 - 1.0kgm^-3",
                               roundToSigFig((SW / 4) / scale, 3), 1, (0, 0),
                               (144, 202, 249),
                               (int(pg.mouse.get_pos()[0]),
                                int(pg.mouse.get_pos()[1])), 0, xA=0))

    setupContainer = pgk.Container(pgkRoot, screen,
                                   topright=(SW, 0),
                                   outlineThickness=0, width=scaler(400, "x"),
                                   height=scaler(520, "y"))

    contWidth = scaler(400, "x")
    offset = scaler(150, "x")
    boxWidth = scaler(125, "x")
    inputList = [
        pgk.InputBox(pgkRoot, screen, contWidth - offset, scaler(55, "y"),
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Coefficient of Restitution:",
                     width=boxWidth, allowLetters=False,
                     allowSpecial=False, allowSpace=False, charLimit=10,
                     defaultEntry="0.75", container=setupContainer),
        pgk.InputBox(pgkRoot, screen, contWidth - offset, scaler(105, "y"),
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Velocity to the right (ms^-1):",
                     width=boxWidth, allowLetters=False,
                     allowSpecial=False, allowSpace=False, charLimit=10,
                     defaultEntry="0", container=setupContainer),
        pgk.InputBox(pgkRoot, screen, contWidth - offset, scaler(155, "y"),
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Velocity downwards (ms^-1):",
                     width=boxWidth, allowLetters=False,
                     allowSpecial=False, allowSpace=False, charLimit=10,
                     defaultEntry="0", container=setupContainer),
        pgk.InputBox(pgkRoot, screen, contWidth - offset, scaler(205, "y"),
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Acceleration to the right (ms^-2):",
                     width=boxWidth, allowLetters=False,
                     allowSpecial=False, allowSpace=False, charLimit=10,
                     defaultEntry="0", container=setupContainer),
        pgk.InputBox(pgkRoot, screen, contWidth - offset, scaler(255, "y"),
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Acceleration downwards (ms^-2):",
                     width=boxWidth, allowLetters=False,
                     allowSpecial=False, allowSpace=False, charLimit=10,
                     defaultEntry="0", container=setupContainer),
        pgk.InputBox(pgkRoot, screen, contWidth - offset, scaler(305, "y"),
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Radius (m):", width=boxWidth, charLimit=10,
                     allowLetters=False, allowSpecial=False, allowSpace=False,
                     defaultEntry="0.5", container=setupContainer),
        pgk.InputBox(pgkRoot, screen, contWidth - offset, scaler(355, "y"),
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Mass (kg):", width=boxWidth, charLimit=10,
                     allowLetters=False, allowSpecial=False, allowSpace=False,
                     defaultEntry="0.5236", container=setupContainer),
        pgk.InputBox(pgkRoot, screen, contWidth - offset, scaler(405, "y"),
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Height off of ground (m):",
                     width=boxWidth, allowLetters=False,
                     allowSpecial=False, allowSpace=False, charLimit=10,
                     defaultEntry="0", container=setupContainer),
        pgk.Checkbox(pgkRoot, screen,
                     contWidth - scaler(50, "x"), scaler(455, "y"),
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Lock particle to height: ",
                     container=setupContainer),
        pgk.Checkbox(pgkRoot, screen,
                     contWidth - scaler(50, "x"), scaler(505, "y"),
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Select for random velocity: ",
                     container=setupContainer),
        pgk.Checkbox(pgkRoot, screen,
                     contWidth - scaler(50, "x"), scaler(555, "y"),
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Draw line following particle's motion: ",
                     container=setupContainer),

        # Create dropdown menu last as it needs to be drawn on top of the other
        # inputs
        pgk.Dropdown(pgkRoot, screen, contWidth - offset -
                     boxWidth, scaler(5, "y"), sortedCustoms + MATERIALS_SORTED,
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Select material (scroll to see more):",
                     width=boxWidth * 2, container=setupContainer)
    ]

    # Y distance between the buttons
    buttonGap = scaler(50, "y") + inputList[0].getHeight()

    inputList += [
        pgk.Button(pgkRoot, screen,
                   contWidth - scaler(350, "x"), scaler(605, "y"),
                   font=MID_FONT,
                   bgColour=(33, 33, 33),
                   text="Create Custom Material",
                   height=inputList[0].getHeight() * 2,
                   width=scaler(325, "x"),
                   action=lambda: createMaterial(widgetList),
                   container=setupContainer, swellOnHover=True),

        pgk.Button(pgkRoot, screen,
                   contWidth - scaler(350, "x"),
                   scaler(605, "y") + buttonGap, font=MID_FONT,
                   bgColour=(33, 33, 33),
                   text="Save Scenario",
                   height=inputList[0].getHeight() * 2,
                   width=scaler(325, "x"),
                   action=lambda: saveSetup(widgetList),
                   container=setupContainer, swellOnHover=True),

        pgk.Button(pgkRoot, screen,
                   contWidth - scaler(350, "x"),
                   scaler(605, "y") + buttonGap * 2, font=MID_FONT,
                   bgColour=(33, 33, 33),
                   text="Load Scenario",
                   height=inputList[0].getHeight() * 2,
                   width=scaler(325, "x"),
                   action=lambda: loadSetup(widgetList),
                   container=setupContainer, swellOnHover=True),

        pgk.Button(pgkRoot, screen,
                   contWidth - scaler(350, "x"),
                   scaler(605, "y") + buttonGap * 3, font=MID_FONT,
                   bgColour=(33, 33, 33),
                   text="Clear Scenario",
                   height=inputList[0].getHeight() * 2,
                   width=scaler(325, "x"), action=clearParticles,
                   container=setupContainer, swellOnHover=True),

        pgk.Button(pgkRoot, screen,
                   contWidth - scaler(350, "x"),
                   scaler(605, "y") + buttonGap * 4, font=MID_FONT,
                   bgColour=(33, 33, 33),
                   text="Done - Start Simulation",
                   height=inputList[0].getHeight() * 2,
                   width=scaler(325, "x"),
                   action=lambda: endFunction(widgetList),
                   container=setupContainer, swellOnHover=True),
    ]

    widgetList = inputList + [setupContainer]

    # Remove references - Collected by garbage collection
    del setupContainer
    del inputList

    widgetList[-1].startAnimation("horizontalslide", 0.25, "in",
                                  SW)

    particles.add(Particle(1, "Custom Material 1 - 1.0kgm^-3",
                           roundToSigFig((SW / 4) / scale, 3), 1, (0, 0),
                           (144, 202, 249),
                           (int(pg.mouse.get_pos()[0]),
                            int(pg.mouse.get_pos()[1])), 0, xA=0))

    pRef = particles.sprites()[-1]

    fpsFont = pg.font.SysFont(SMALL_FONT[0], SMALL_FONT[1])

    setting = True
    while setting:
        previousScale = scale
        for event in pg.event.get():
            if event.type == QUIT:
                pg.quit()
                quit()

            if not pgkRoot.eventHandler(event):
                if event.type == MOUSEBUTTONUP:
                    if event.button == 1:
                        # Check that looks at all possibilities to ensure
                        # that the particle will be placed on-screen and not
                        # intersecting with another particle
                        if pRef.pos.x + pRef.radius * scale > SW \
                                or pRef.pos.x - pRef.radius * scale < 0 \
                                or pRef.pos.y + pRef.radius * scale > SH \
                                or pRef.pos.y - pRef.radius * scale < 0 \
                                or len(pRef.hasCollided(particles)) != 0:
                            pass
                        else:
                            rad = roundToSigFig((SW / 4) / scale, 3)
                            particles.add(Particle(1, "Wood - 800kgm^-3",
                                                   rad, 10, (0, 0),
                                                   (144, 202, 249),
                                                   (int(pg.mouse.get_pos()[0]),
                                                    int(pg.mouse.get_pos()[1])),
                                                   0, xA=0))

                    elif event.button == 3:
                        # Editing particles after they have been placed
                        mouseCoords = pg.mouse.get_pos()
                        for i in particles.sprites()[:-1]:
                            if absoluteDistance(pgmath.Vector2(mouseCoords),
                                                i.pos) <= i.radius * scale:
                                if editList:
                                    for widget in editList:
                                        widget.delete()
                                    del editList
                                editingParticle = i

                                # Create container for widgets first,
                                # then position it so that it will always be
                                # on screen.
                                eContainer = pgk.Container(pgkRoot, screen,
                                                           centre=(0, 0),
                                                           outlineThickness=3,
                                                           width=scaler(310,
                                                                        "x"),
                                                           height=scaler(400,
                                                                         "y"),
                                                           bg=True,
                                                           bgColour=(255, 255,
                                                                     255),
                                                           startVisible=False)

                                # Container will be positioned so that one of
                                # its corners will be in the centre of the
                                # particle
                                pos = i.pos
                                if pos[1] + scaler(400, "y") <= SH:
                                    if pos[0] + scaler(310, "x") <= SW:
                                        eContainer.config(topleft=pos)
                                    else:
                                        eContainer.config(topright=pos)
                                else:
                                    if pos[0] + scaler(310, "x") <= SW:
                                        eContainer.config(bottomleft=pos)
                                    else:
                                        eContainer.config(bottomright=pos)

                                editContWidth = scaler(310, "x")
                                offset = scaler(150, "x") / 2
                                boxWidth = scaler(125, "x") / 2

                                # Creating list of widgets used in editing
                                # the particle
                                inputList = [
                                    pgk.InputBox(pgkRoot, screen,
                                                 editContWidth - offset,
                                                 scaler(28, "y"),
                                                 font=SMALLER_FONT,
                                                 bgColour=(222, 222, 222),
                                                 inlineText="Coefficient of "
                                                            "Restitution",
                                                 width=boxWidth,
                                                 allowLetters=False,
                                                 allowSpecial=False,
                                                 allowSpace=False, charLimit=10,
                                                 container=eContainer),
                                    pgk.InputBox(pgkRoot, screen,
                                                 editContWidth - offset,
                                                 scaler(53, "y"),
                                                 font=SMALLER_FONT,
                                                 bgColour=(222, 222, 222),
                                                 inlineText="Velocity to the "
                                                            "right (ms^-1):",
                                                 width=boxWidth,
                                                 allowLetters=False,
                                                 allowSpecial=False,
                                                 allowSpace=False, charLimit=10,
                                                 container=eContainer),
                                    pgk.InputBox(pgkRoot, screen,
                                                 editContWidth - offset,
                                                 scaler(78, "y"),
                                                 font=SMALLER_FONT,
                                                 bgColour=(222, 222, 222),
                                                 inlineText="Velocity "
                                                            "downwards ("
                                                            "ms^-1):",
                                                 width=boxWidth,
                                                 allowLetters=False,
                                                 allowSpecial=False,
                                                 allowSpace=False, charLimit=10,
                                                 container=eContainer),
                                    pgk.InputBox(pgkRoot, screen,
                                                 editContWidth - offset,
                                                 scaler(103, "y"),
                                                 font=SMALLER_FONT,
                                                 bgColour=(222, 222, 222),
                                                 inlineText="Acceleration to "
                                                            "the right ("
                                                            "ms^-2):",
                                                 width=boxWidth,
                                                 allowLetters=False,
                                                 allowSpecial=False,
                                                 allowSpace=False, charLimit=10,
                                                 container=eContainer),
                                    pgk.InputBox(pgkRoot, screen,
                                                 editContWidth - offset,
                                                 scaler(128, "y"),
                                                 font=SMALLER_FONT,
                                                 bgColour=(222, 222, 222),
                                                 inlineText="Acceleration "
                                                            "downwards ("
                                                            "ms^-2):",
                                                 width=boxWidth,
                                                 allowLetters=False,
                                                 allowSpecial=False,
                                                 allowSpace=False, charLimit=10,
                                                 container=eContainer),
                                    pgk.InputBox(pgkRoot, screen,
                                                 editContWidth - offset,
                                                 scaler(153, "y"),
                                                 font=SMALLER_FONT,
                                                 bgColour=(222, 222, 222),
                                                 inlineText="Radius (m):",
                                                 width=boxWidth,
                                                 allowLetters=False,
                                                 allowSpecial=False,
                                                 allowSpace=False, charLimit=10,
                                                 container=eContainer),
                                    pgk.InputBox(pgkRoot, screen,
                                                 editContWidth - offset,
                                                 scaler(178, "y"),
                                                 font=SMALLER_FONT,
                                                 bgColour=(222, 222, 222),
                                                 inlineText="Mass (kg):",
                                                 width=boxWidth,
                                                 allowLetters=False,
                                                 allowSpecial=False,
                                                 allowSpace=False, charLimit=10,
                                                 container=eContainer),
                                    pgk.InputBox(pgkRoot, screen,
                                                 editContWidth - offset,
                                                 scaler(203, "y"),
                                                 font=SMALLER_FONT,
                                                 bgColour=(222, 222, 222),
                                                 inlineText="Height off of "
                                                            "ground (m):",
                                                 width=boxWidth,
                                                 allowLetters=False,
                                                 allowSpecial=False,
                                                 allowSpace=False, charLimit=10,
                                                 defaultEntry="0",
                                                 container=eContainer),
                                    pgk.Checkbox(pgkRoot, screen,
                                                 editContWidth - scaler(50,
                                                                        "x"),
                                                 scaler(228, "y"),
                                                 font=SMALLER_FONT,
                                                 bgColour=(222, 222, 222),
                                                 inlineText="Lock particle to "
                                                            "height: ",
                                                 container=eContainer),
                                    pgk.Checkbox(pgkRoot, screen,
                                                 editContWidth - scaler(50,
                                                                        "x"),
                                                 scaler(253, "y"),
                                                 font=SMALLER_FONT,
                                                 bgColour=(222, 222, 222),
                                                 inlineText="Select for "
                                                            "random velocity:"
                                                            " ",
                                                 container=eContainer),
                                    pgk.Checkbox(pgkRoot, screen,
                                                 editContWidth - scaler(50,
                                                                        "x"),
                                                 scaler(278, "y"),
                                                 font=SMALLER_FONT,
                                                 bgColour=(222, 222, 222),
                                                 inlineText="Draw line "
                                                            "following "
                                                            "particle's "
                                                            "motion: ",
                                                 container=eContainer)
                                ]

                                buttonHeight = inputList[0].getHeight() * 2
                                fButton = pgk.Button(pgkRoot, screen,
                                                     editContWidth - scaler(225,
                                                                            "x"),
                                                     scaler(303, "y"),
                                                     font=SMALL_FONT,
                                                     bgColour=(33, 33, 33),
                                                     text="Finish Editing "
                                                          "Particle",
                                                     height=buttonHeight,
                                                     width=scaler(213, "x"),
                                                     action=lambda:
                                                     endParticleEdit(
                                                         editList),
                                                     container=eContainer,
                                                     swellOnHover=True)

                                delButton = pgk.Button(pgkRoot, screen,
                                                       editContWidth - scaler(
                                                           225, "x"),
                                                       scaler(353, "y"),
                                                       font=SMALL_FONT,
                                                       bgColour=(33, 33, 33),
                                                       text="Delete Particle",
                                                       height=buttonHeight,
                                                       width=scaler(213, "x"),
                                                       action=lambda:
                                                       deleteParticle(
                                                           editingParticle),
                                                       container=eContainer,
                                                       swellOnHover=True)

                                # Create dropdown menu last as it needs to be
                                # drawn on top of the other inputs
                                drop = (pgk.Dropdown(pgkRoot, screen,
                                                     editContWidth - offset -
                                                     boxWidth,
                                                     scaler(5, "y"),
                                                     sortedCustoms +
                                                     MATERIALS_SORTED,
                                                     font=SMALLER_FONT,
                                                     bgColour=(
                                                         222, 222,
                                                         222),
                                                     inlineText="Select "
                                                                "material "
                                                                "(scroll to see"
                                                                " more):",
                                                     width=boxWidth * 2,
                                                     container=eContainer))

                                # Write to the input boxes so that they so
                                # the selected particle's properties
                                inputList[0].write(str(i.restCoefficient))
                                inputList[1].write(str(i.velocity.x))
                                inputList[2].write(str(i.velocity.y))
                                inputList[3].write(str(i.acceleration.x))
                                inputList[4].write(str(i.acceleration.y))
                                inputList[5].write(str(i.radius))
                                inputList[6].write(str(i.mass))

                                if i.hasRandomVelocity:
                                    inputList[9].click()
                                if i.line:
                                    inputList[10].click()

                                drop.setSelected(i.material)

                                editList = inputList + [drop, fButton,
                                                        delButton, eContainer]

                                # Delete references
                                del inputList
                                del drop
                                del fButton
                                del eContainer

                                editList[-1].startAnimation("centre", 0.25,
                                                            "in")

                # Can only zoom in/out if no particles are being edited
                elif event.type == MOUSEBUTTONDOWN and editingParticle is None:
                    # Buttons 4 and 5 correspond to the scroll wheel up/down.
                    # These are used for changing the scale while still in
                    # the setup phase
                    if event.button == 4:
                        scale *= 1.02

                    elif event.button == 5:
                        scale *= 0.98

            if event.type == KEYDOWN:
                if event.key == K_s:
                    # Use s key (for 'scale') to change size of a particle
                    # using the mouse, rather than the input boxes
                    sizeChange(pRef, widgetList[5], widgetList[6], metres)

        pRef = particles.sprites()[-1]

        if widgetList[-1].isEmpty():
            setting = False

        screen.fill(BG_COLOUR)
        particleGraph.draw()

        updateParticle(pRef, widgetList)

        if editingParticle is not None:
            updateParticle(editingParticle, editList, True)

            # Finish editing if the particle is not in the sprite group (it
            # has been deleted), and if the finishing process has not
            # already started
            if editingParticle not in particles.sprites():
                endParticleEdit(editList)

        # Call scalePosition on all but the last sprite, as last sprite's
        # position is determined by the location of the mouse
        for sprite in particles.sprites()[:-1]:
            sprite.scalePosition()

        for sprite in particles.sprites():
            sprite.draw()
            sprite.updateDirection()
            sprite.drawDirectionArrow()
        pgkRoot.update()

        scaleLength = metres * scale

        if scaleLength > scaler(200, "x"):
            metres /= 10
            scaleLength = metres * scale
        elif scaleLength < scaler(20, "x"):
            metres *= 10
            scaleLength = metres * scale

        metres = roundToSigFig(metres, 1)

        particleGraph.changeLabelGap(scaleLength, scaleLength)

        scaleDisplay = pg.Rect(scaler(5, "x"), scaler(5, "y"), scaleLength,
                               scaler(5, "y"))

        scaleDisplayText = fpsFont.render(u"{0}m".format(str(metres)), True,
                                          (0, 0, 0))
        scaleTextRect = scaleDisplayText.get_rect(topleft=(scaler(15, "y"),
                                                           scaler(5, "x")))
        screen.blit(scaleDisplayText, scaleTextRect)

        pg.draw.rect(screen, (0, 0, 0), scaleDisplay)

        fps = str(int(clock.get_fps()))

        fpsText = fpsFont.render(u"FPS: {0}".format(fps), True, (0, 0, 0))
        fpsRect = fpsText.get_rect(midtop=(int(SW / 2), int(scaler(10, "y"))))
        screen.blit(fpsText, fpsRect)

        pg.display.update()

        pg.display.set_caption('HAHA CIRCLE GO BRR | FPS: ' + fps)
        clock.tick()

    try:
        return main, (widgetList + editList,)
    except TypeError:
        return main, (widgetList,)


def saveSetup(setupWidgets):
    def saveToFile(saveWidgets, setupWidgets):
        global saving
        saveWidgets[-1].startAnimation("horizontalslide", 0.5, "out",
                                       SW + scaler(350, "x"), True)

        fileName = u"{0}.txt".format(saveWidgets[0].get())

        saveData = [str(scale)]

        # Writing data from all particles to a list that will be written to
        # the txt file
        for p in particles.sprites()[:-1]:
            if p.line:
                line = True
            else:
                line = False
            pData = [p.hasRandomVelocity, line, p.restCoefficient,
                     p.material, p.radius, p.density, p.mass, p.vol,
                     (p.velocity.x, p.velocity.y), p.colour,
                     (p.rect.x, p.rect.y), (p.acceleration.x, p.acceleration.y)]
            saveData.append(str(pData))

        with open(str(saveLocation / fileName), "w") as f:
            f.writelines('\n'.join(saveData))

        setupWidgets[-1].startAnimation("horizontalslide", 0.5, "out",
                                        SW - scaler(400, "x"))

        saving = False

    global saving

    if len(particles) < 2:
        return

    takenNumbers = []
    for file in os.listdir(saveLocation):
        if file.endswith(".txt") and file.lower().startswith("custom scenario"):
            fileNum = int(file[15:-4])
            takenNumbers.append(fileNum)

    takenNumbers.sort()

    lowNum = 1
    for num in takenNumbers:
        if num == lowNum:
            lowNum += 1
        else:
            break

    setupWidgets[-1].startAnimation("horizontalslide", 0.5, "out",
                                    SW + scaler(350, "x"))

    saveContainer = pgk.Container(pgkRoot, screen,
                                  topright=(SW + scaler(400, "x"), 0),
                                  outlineThickness=0, width=scaler(400, "x"),
                                  height=scaler(205, "y"))

    contWidth = scaler(400, "x")
    offset = scaler(275, "x")
    boxWidth = scaler(250, "x")
    inputList = [
        pgk.InputBox(pgkRoot, screen, contWidth - offset, scaler(5, "y"),
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Scenario Name: ",
                     width=boxWidth, allowSpecial=False, charLimit=35,
                     defaultEntry=u"Custom Scenario {0}".format(str(lowNum)),
                     container=saveContainer),
    ]

    inputList += [
        pgk.Button(pgkRoot, screen,
                   contWidth - scaler(350, "x"), scaler(55, "y"),
                   font=MID_FONT,
                   bgColour=(33, 33, 33),
                   text="Save",
                   height=inputList[0].getHeight() * 2,
                   width=scaler(325, "x"),
                   action=lambda: saveToFile(saveWidgets, setupWidgets),
                   container=saveContainer, swellOnHover=True),
    ]

    saveWidgets = inputList + [saveContainer]

    # Remove references - Collected by garbage collection
    del saveContainer
    del inputList

    saving = True
    while saving:
        for event in pg.event.get():
            pgkRoot.eventHandler(event)
            if event.type == QUIT:
                saving = False
                pg.quit()
                quit()

        if setupWidgets[-1].animationDone():
            saveWidgets[-1].startAnimation("horizontalslide", 0.25, "out",
                                           SW - contWidth)

        screen.fill(BG_COLOUR)
        particleGraph.draw()

        # Exclude final particle - the one that was following the mouse
        # pointer when save button was pressed
        for i in particles.sprites()[:-1]:
            i.draw()
            i.drawDirectionArrow()

        pgkRoot.update()

        pg.display.update()

        fps = str(int(clock.get_fps()))
        pg.display.set_caption('HAHA CIRCLE GO BRR | FPS: ' + fps)
        clock.tick()

    return


def loadSetup(widgets):
    def loadFromFile(loadWidgets, widgets):
        global scale
        global previousScale
        global loading
        global particleGraph
        loadWidgets[-1].startAnimation("centre", 0.25, "out", deleteAfter=True)

        fileName = loadWidgets[0].get()

        with open(str(saveLocation / fileName), "r") as f:
            data = f.readlines()

        # Remove newline characters from lines
        newData = []
        for line in data:
            # ast.literal_eval reads the contents of the file, and evaluates the
            # string as a python expression - in this case a list
            newData.append(ast.literal_eval(line.rstrip("\n")))

        scale = newData[0]
        previousScale = scale
        particleGraph = Graph(screen, SW, SH, (0, 0), BG_COLOUR, scale, scale)
        for p in newData[1:]:
            particles.add(Particle(p[2], p[3], p[4], p[5], p[8], p[9], p[10],
                                   p[11][0], p[11][1]))

            particles.sprites()[-1].hasRandomVelocity = p[0]
            if p[1]:
                particles.sprites()[-1].line = Line(screen, particleGraph, p[9])
            else:
                particles.sprites()[-1].line = None
            particles.sprites()[-1].mass = p[6]
            particles.sprites()[-1].vol = p[7]

        if widgets:
            widgets[-1].startAnimation("horizontalslide", 0.5, "out",
                                       SW - scaler(400, "x"))

            particles.add(Particle(1, "Custom Material 1 - 1.0kgm^-3",
                                   roundToSigFig((SW / 4) / scale, 3), 1,
                                   (0, 0),
                                   (144, 202, 249),
                                   (int(pg.mouse.get_pos()[0]),
                                    int(pg.mouse.get_pos()[1])), 0, xA=0))

        loading = False

    global loading

    for particle in particles.sprites():
        particle.delete()

    if widgets:
        widgets[-1].startAnimation("horizontalslide", 0.5, "out",
                                   SW + scaler(350, "x"))

    loadContainer = pgk.Container(pgkRoot, screen, maskColour=BG_COLOUR,
                                  centre=(SW / 2, SH / 2),
                                  outlineThickness=0, width=scaler(400, "x"),
                                  height=scaler(205, "y"), startVisible=False)

    options = os.listdir(saveLocation)
    boxWidth = scaler(350, "x")
    # Define inputList as an empty list initially, as it needs to be
    # referenced by the button, which cannot be done if inputList and the
    # button are created at the same time.
    inputList = [
        pgk.Dropdown(pgkRoot, screen, scaler(25, "x"), scaler(5, "y"),
                     options, font=SMALL_FONT, bgColour=(222, 222, 222),
                     width=boxWidth),
    ]

    inputList += [
        pgk.Button(pgkRoot, screen, scaler(25, "x"), scaler(55, "y"),
                   font=MID_FONT, bgColour=(33, 33, 33), text="Load Scenario",
                   height=inputList[0].getHeight() * 2,
                   width=scaler(350, "x"),
                   action=lambda: loadFromFile(loadWidgets, widgets),
                   container=loadContainer, swellOnHover=True),
    ]

    # Add dropdown to container last as it needs to be drawn over the button
    inputList[0].config(container=loadContainer)

    loadWidgets = inputList + [loadContainer]

    # Remove references - Collected by garbage collection
    del loadContainer
    del inputList

    if not widgets:
        loadWidgets[-1].startAnimation("centre", 0.25, "in")

    for particle in particles.sprites():
        particle.delete()

    loading = True
    while loading:
        for event in pg.event.get():
            pgkRoot.eventHandler(event)
            if event.type == QUIT:
                loading = False
                pg.quit()
                quit()

        if widgets and widgets[-1].animationDone():
            loadWidgets[-1].startAnimation("centre", 0.25, "in")

        screen.fill(BG_COLOUR)

        pgkRoot.update()

        pg.display.update()

        fps = str(int(clock.get_fps()))
        pg.display.set_caption('HAHA CIRCLE GO BRR | FPS: ' + fps)
        clock.tick()

    # If widgets is None, that means the program got to this page from the
    # main menu, and therefore needs to move onto setup. If widgets exists,
    # however, this function was called from within setup, and we just need a
    # simple return statement
    if not widgets:
        return setup, (1,)
    else:
        return


def sizeChange(particle, radBox, massBox, metres):
    changing = True

    # Need to duplicate SCALE_TOOL_IMG as it needs to be modified with the
    # rotozoom method of pygame's image class. Using the original image will
    # mean that I will have to reload the image every time it is needed in
    # order to get the original, unmodified one.
    sizeArrow = SCALE_TOOL_IMG

    fpsFont = pg.font.SysFont(SMALL_FONT[0], SMALL_FONT[1])

    while changing:
        for event in pg.event.get():
            if event.type == QUIT:
                pg.quit()
                quit()
            if pgkRoot.eventHandler(event):
                return

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    # When the user initially presses the LMB,
                    # set startDistance equal to the distance between the
                    # mouse and the particle centre, and set startRad equal
                    # to the particle's current radius.
                    startDistance = absoluteDistance(particle.pos,
                                                     pgmath.Vector2(
                                                         pg.mouse.get_pos()))
                    startRad = roundToSigFig(float(radBox.get()), 3)

            elif event.type == KEYDOWN:
                # if ... in ... statement allows the user to use either the
                # main enter key, or the enter key on the numpad.
                if event.key in [K_RETURN, K_KP_ENTER]:
                    return

        screen.fill(BG_COLOUR)
        particleGraph.draw()

        for sprite in particles.sprites():
            sprite.draw()
            sprite.drawDirectionArrow()

        pg.mouse.set_visible(True)

        # If the user is holding down the LMB
        if pg.mouse.get_pressed()[0]:
            pg.mouse.set_visible(False)

            # Draw dotted line from centre of particle to mouse pointer,
            drawDottedLine(particle.pos, pg.mouse.get_pos())

            xDiff = pg.mouse.get_pos()[0] - particle.pos.x
            yDiff = pg.mouse.get_pos()[1] - particle.pos.y

            # Calculating angle by which to rotate the arrow
            dir = (math.atan2(yDiff, xDiff) * -1) + math.pi / 2
            blitArrow = pg.transform.rotate(sizeArrow, math.degrees(dir))

            arrowRect = blitArrow.get_rect(center=pg.mouse.get_pos())

            # Blit arrow on screen in the position of the mouse pointer,
            # to create the illusion that the pointer has changed to the arrow.
            screen.blit(blitArrow, arrowRect)

            posVector = pgmath.Vector2(pg.mouse.get_pos())
            currentDistance = absoluteDistance(particle.pos, posVector)
            diff = currentDistance - startDistance

            minRad = roundToSigFig(scaler(10, "x") / scale, 3)
            maxRad = roundToSigFig((SW / 4) / scale, 3)

            changeFactor = roundToSigFig(0.5 / scale, 3)

            if minRad <= startRad + (changeFactor * diff) <= maxRad:
                # Equation to calculate new size of particle, based on
                # distance that the mouse has moved away from the particle's
                # centre (diff)
                newRad = startRad + (changeFactor * diff)

                # Update dimensions of particle and write the new dimensions
                # to the input boxes.
                particles.sprites()[-1].updateDimension(rad=newRad)
                radBox.write(str(roundToSigFig(newRad, 3)))
                massBox.write(str(particles.sprites()[-1].mass))

        pgkRoot.update()

        scaleLength = metres * scale

        scaleDisplay = pg.Rect(scaler(5, "x"), scaler(5, "y"), scaleLength,
                               scaler(5, "y"))

        scaleDisplayText = fpsFont.render(u"{0}m".format(str(metres)), True,
                                          (0, 0, 0))
        scaleTextRect = scaleDisplayText.get_rect(topleft=(scaler(15, "y"),
                                                           scaler(5, "x")))
        screen.blit(scaleDisplayText, scaleTextRect)

        pg.draw.rect(screen, (0, 0, 0), scaleDisplay)

        fps = str(int(clock.get_fps()))
        fpsText = fpsFont.render(u"FPS: {0}".format(fps), True, (0, 0, 0))
        fpsRect = fpsText.get_rect(midtop=(int(SW / 2), int(scaler(10, "y"))))
        screen.blit(fpsText, fpsRect)

        pg.display.update()
        pg.display.set_caption('HAHA CIRCLE GO BRR | FPS: ' + fps)
        clock.tick()


def createMaterial(widgetList):
    global materialTimer

    def startExit(widgets, colour):
        global customMaterials
        global sortedCustoms
        name = widgets[4].get()
        density = widgets[3].get()
        newMaterial = u"""    "{0} - {1}kgm^-3": [{2}, {3}],""".format(name,
                                                                       density,
                                                                       density,
                                                                       colour)

        with open("customMaterials.txt", "r+") as file:
            lines = file.readlines()[:-1]
            lines += [newMaterial + "\n", "}"]
            # file.truncate(0) clears the file, which is needed as otherwise
            # lines will be added on to the end of the file, effectively
            # duplicating everything and ruining the formatting of the
            # dictionary
            file.truncate(0)

            # Seek after truncate prevents null bytes being inserted - when
            # truncate is used, the file tries to write from the same memory
            # location as it was before truncation, resulting in null bytes
            # being inserted. Seek(0) moves to the start of the file
            # preventing null bytes
            file.seek(0)
            file.writelines(lines)

        with open("customMaterials.txt", "r") as file:
            contents = file.read()

        customMaterials = ast.literal_eval(contents)
        sortedCustoms = sorted(customMaterials)

        widgets[-1].startAnimation("horizontalslide", 0.25, "out", SW,
                                   deleteAfter=True)

    def randomiseColour(widgets):
        widgets[5].write(str(random.randint(0, 255)))
        widgets[6].write(str(random.randint(0, 255)))
        widgets[7].write(str(random.randint(0, 255)))

    widgetList[-1].startAnimation("horizontalslide", 0.5, "out",
                                  SW + scaler(350, "x"))

    materialContainer = pgk.Container(pgkRoot, screen,
                                      topleft=(SW, 0), outlineThickness=0,
                                      width=scaler(400, "x"),
                                      height=scaler(520, "y"))

    contWidth = scaler(400, "x")
    offset = scaler(150, "x")
    boxWidth = scaler(125, "x")
    rgbOffset = scaler(275, "x")
    rgbWidth = scaler(50, "x")

    # A unique name will be automatically  generated for each new material
    # created, in the form of "Custom Material <number>"
    # This loop decides what number that will be, based on how many materials
    # are already named in that form
    customNum = 1
    for i in sortedCustoms:
        if i.lower().startswith("custom material"):
            customNum += 1

    createWidgets = [
        pgk.InputBox(pgkRoot, screen, contWidth - offset, scaler(5, "y"),
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Desired radius (m) (maximum 10m):",
                     width=boxWidth, allowLetters=False,
                     allowSpecial=False, allowSpace=False, charLimit=10,
                     defaultEntry="1", container=materialContainer),
        pgk.InputBox(pgkRoot, screen, contWidth - offset, scaler(55, "y"),
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Desired Volume (m^3) (maximum 33.5m^3):",
                     width=boxWidth, allowLetters=False,
                     allowSpecial=False, allowSpace=False, charLimit=10,
                     defaultEntry="1", container=materialContainer),
        pgk.InputBox(pgkRoot, screen, contWidth - offset, scaler(105, "y"),
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Desired mass (kg):",
                     width=boxWidth, allowLetters=False,
                     allowSpecial=False, allowSpace=False, charLimit=10,
                     defaultEntry="1", container=materialContainer),
        pgk.InputBox(pgkRoot, screen, contWidth - offset, scaler(155, "y"),
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Density (kgm^-3):",
                     width=boxWidth, allowLetters=False,
                     allowSpecial=False, allowSpace=False, charLimit=10,
                     defaultEntry="0", container=materialContainer),
        pgk.InputBox(pgkRoot, screen, contWidth - offset, scaler(205, "y"),
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Material name:",
                     width=boxWidth, charLimit=17,
                     defaultEntry="Custom Material " + str(customNum),
                     container=materialContainer),
        pgk.InputBox(pgkRoot, screen, contWidth - rgbOffset, scaler(255, "y"),
                     font=SMALL_FONT, bgColour=(222, 222, 222),
                     inlineText="Material color: (R)",
                     width=rgbWidth, allowLetters=False, allowMaths=False,
                     allowSpecial=False, allowSpace=False,
                     charLimit=3, defaultEntry="126",
                     container=materialContainer),
        pgk.InputBox(pgkRoot, screen, contWidth - rgbOffset + rgbWidth * 2,
                     scaler(255, "y"), font=SMALL_FONT,
                     bgColour=(222, 222, 222), inlineText="(G)",
                     width=rgbWidth, allowLetters=False, allowMaths=False,
                     allowSpecial=False, allowSpace=False,
                     charLimit=3, defaultEntry="25",
                     container=materialContainer),
        pgk.InputBox(pgkRoot, screen, contWidth - rgbOffset + rgbWidth * 4,
                     scaler(255, "y"), font=SMALL_FONT,
                     bgColour=(222, 222, 222), inlineText="(B)",
                     width=rgbWidth, allowLetters=False, allowMaths=False,
                     allowSpecial=False, allowSpace=False,
                     charLimit=3, defaultEntry="27",
                     container=materialContainer),
    ]

    buttonGap = scaler(50, "y") + createWidgets[0].getHeight()

    randomButton = pgk.Button(pgkRoot, screen,
                              contWidth - scaler(350, "x"),
                              scaler(305, "y"), font=MID_FONT,
                              bgColour=(33, 33, 33),
                              text="Randomise Colour",
                              height=createWidgets[0].getHeight() * 2,
                              width=scaler(325, "x"),
                              action=lambda: randomiseColour(createWidgets),
                              container=materialContainer, swellOnHover=True)

    doneButton = pgk.Button(pgkRoot, screen,
                            contWidth - scaler(350, "x"),
                            scaler(305, "y") + buttonGap, font=MID_FONT,
                            bgColour=(33, 33, 33), text="Finish and Save",
                            height=createWidgets[0].getHeight() * 2,
                            width=scaler(325, "x"),
                            action=lambda: startExit(createWidgets,
                                                     materialColour),
                            container=materialContainer, swellOnHover=True)

    # Cannot be added to the list immediately as they rely on the list for
    # their height attribute
    createWidgets += [randomButton, doneButton, materialContainer]

    # Remove references
    del materialContainer
    del randomButton
    del doneButton

    # Displays the current colour that the user has chosen
    rgbTestRect = pg.Rect((int(SW - contWidth - scaler(60, "x")),
                           int(scaler(255, "y"))),
                          (rgbWidth, createWidgets[0].getHeight()))

    previousRad = createWidgets[0].get()
    previousVol = None
    previousMass = createWidgets[2].get()

    isCreating = False

    changing = True

    while changing:
        for event in pg.event.get():
            if event.type == QUIT:
                pg.quit()
                quit()
            if pgkRoot.eventHandler(event):
                pass

        screen.fill(BG_COLOUR)
        particleGraph.draw()

        for sprite in particles.sprites():
            sprite.draw()
            sprite.drawDirectionArrow()
        # If animation has finished for the creation container, length will
        # be 0 as all widgets will have been deleted
        if createWidgets[-1].isEmpty():
            del createWidgets

            widgetList[-7].config(options=sortedCustoms + MATERIALS_SORTED)
            widgetList[-1].startAnimation("horizontalslide", 0.5, "out",
                                          SW - contWidth)
            return

        # isCreating is used to ensure that this only runs once
        if widgetList[-1].animationDone() and not isCreating:
            # Need to use a slide out animation, rather than in.
            # Otherwise the container will be displayed in its final
            # position until the animation starts - it needs to be
            # offscreen until it starts.
            createWidgets[-1].startAnimation("horizontalslide", 0.25,
                                             "out", SW - contWidth)
            isCreating = True

        # Need to except ValueError here in case the user deletes all
        # characters (calling int() on an empty string throws a ValueError
        try:
            for i in [createWidgets[5], createWidgets[6], createWidgets[7]]:
                if int(i.get()) > 255:
                    i.write("255")

            r = int(createWidgets[5].get())
            g = int(createWidgets[6].get())
            b = int(createWidgets[7].get())

            materialColour = (r, g, b)
        except ValueError:
            pass

        try:
            if createWidgets[0].get() != previousRad:
                previousRad = createWidgets[0].get()

                rad = roundToSigFig(float(createWidgets[0].get()), 3)
                vol = roundToSigFig((4 / 3) * math.pi * rad ** 3, 3)

                createWidgets[1].write(str(vol))
                createWidgets[3].write(
                    str(roundToSigFig(float(createWidgets[2].get()) /
                                      vol, 3)))

            if createWidgets[1].get() != previousVol:
                previousVol = createWidgets[1].get()

                vol = roundToSigFig(float(createWidgets[1].get()), 3)
                rad = roundToSigFig(((3 * vol) / (4 * math.pi)) ** (1 / 3), 3)
                previousRad = str(rad)
                createWidgets[0].write(str(rad))
                createWidgets[3].write(
                    str(roundToSigFig(float(createWidgets[2].get()) /
                                      vol, 3)))

            if createWidgets[2].get() != previousMass:
                previousMass = createWidgets[3].get()
                createWidgets[3].write(
                    str(roundToSigFig(float(createWidgets[2].get()) /
                                      float(createWidgets[1].get()),
                                      3)))

        # Need to catch both errors here, as the inputs involve dividing
        # by user input, meaning they may end up dividing by zero
        # Also ValueError in case the user deletes everything in one input box
        except (ValueError, ZeroDivisionError):
            pass

        pgkRoot.update()

        fps = str(int(clock.get_fps()))
        fpsFont = pg.font.SysFont(SMALL_FONT[0], SMALL_FONT[1])
        fpsText = fpsFont.render(u"FPS: {0}".format(fps), True, (0, 0, 0))
        fpsRect = fpsText.get_rect(midtop=(int(SW / 2), int(scaler(10, "y"))))
        screen.blit(fpsText, fpsRect)
        pg.draw.rect(screen, materialColour, rgbTestRect)

        pg.display.update()
        pg.display.set_caption('HAHA CIRCLE GO BRR | FPS: ' + fps)
        clock.tick()


def main(widgetList):
    global mainprogram
    global tNow
    global frameNumber
    global timeMultiplier
    global timeShown
    timeShown = False

    def showTimeControls(timeContainer):
        global timeShown
        if not timeShown:
            timeContainer.startAnimation("verticalslide", 0.25, "out",
                                         SH - scaler(100, "y"))
            timeShown = True
        else:
            timeContainer.startAnimation("verticalslide", 0.25, "out", SH)
            timeShown = False

    # Delete particle that gets placed on button press
    particles.remove(particles.sprites()[-1])

    timeWidgets = [
        pgk.Container(pgkRoot, screen, centre=(SW / 2, SH + scaler(50, "y")),
                      width=scaler(450, "x"), height=scaler(100, "y"))
    ]

    contWidth = scaler(450, "x")
    contHeight = scaler(100, "y")

    timeWidgets += [
        pgk.Button(pgkRoot, screen, contWidth / 2 - scaler(40, "x"),
                   contHeight - scaler(145, "y"), height=scaler(40, "y"),
                   width=scaler(80, "x"),
                   action=lambda: showTimeControls(timeWidgets[0]),
                   image=TT_IMG, hoverImage=H_TT_IMG,
                   container=timeWidgets[0]),
        pgk.Button(pgkRoot, screen, contWidth / 2 - scaler(75, "x"),
                   contHeight - scaler(105, "y"), height=scaler(100, "y"),
                   width=scaler(150, "x"),
                   action=lambda: pauseMenu(timeWidgets),
                   image=PAUSE_IMG, hoverImage=H_PAUSE_IMG,
                   container=timeWidgets[0]),
        pgk.Button(pgkRoot, screen, contWidth / 2 - scaler(175, "x"),
                   contHeight - scaler(105, "y"), height=scaler(100, "y"),
                   width=scaler(100, "x"), action=lambda: timeChange(-1),
                   image=RW_IMG, hoverImage=H_RW_IMG,
                   container=timeWidgets[0]),
        pgk.Button(pgkRoot, screen, contWidth / 2 + scaler(75, "x"),
                   contHeight - scaler(105, "y"), height=scaler(100, "y"),
                   width=scaler(100, "x"), action=lambda: timeChange(1),
                   image=FF_IMG, hoverImage=H_FF_IMG,
                   container=timeWidgets[0]),
    ]

    for widget in widgetList:
        widget.delete()
        del widget
        # Remove references to widgets - will get collected by Python's
        # garbage collection

    mainprogram = True

    while mainprogram:
        for event in pg.event.get():
            pgkRoot.eventHandler(event)
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pauseMenu(timeWidgets)

            if event.type == QUIT:
                mainprogram = False
                pg.quit()
                quit()

        frameNumber += TIME_SCALES[currentTimescale]
        if frameNumber < 1:
            frameNumber = 1
        try:
            # If statement prevents 'jumping' of particles when user moves
            # the window
            if time.time() - previousFrame < 0.1:
                timeMultiplier = (time.time() - previousFrame)
                timeMultiplier *= TIME_SCALES[currentTimescale]
                # Calculates time between frames
        except NameError:
            # Will occur on the first frame, as there is no previous frame
            pass

        previousFrame = time.time()

        if tNow <= 0 and currentTimescale < 3:
            pauseMenu(timeWidgets)

        screen.fill(BG_COLOUR)
        particleGraph.draw()
        particles.update()

        if timeMultiplier > 0:
            tNow += timeMultiplier

        # Set up text that shows current time
        tDisplay = round(tNow, 4)
        timeFont = pg.font.SysFont(MID_FONT[0], MID_FONT[1])
        timeText = timeFont.render("Time: T+" + str(tDisplay), True, (0, 0, 0))
        tRect = timeText.get_rect(topleft=(10, 10))

        timescaleFont = pg.font.SysFont(SMALL_FONT[0], SMALL_FONT[1])
        tscaleText = timescaleFont.render("Time Multiplier: x" +
                                          str(TIME_SCALES[currentTimescale]),
                                          True, (0, 0, 0))
        tscaleRect = tscaleText.get_rect(topleft=(scaler(10, "x"),
                                                  scaler(50, "y")))

        screen.blit(timeText, tRect)
        screen.blit(tscaleText, tscaleRect)

        pgkRoot.update()

        fps = str(int(clock.get_fps()))

        # Create text that shows the fps that the program is running at
        fpsFont = pg.font.SysFont(SMALL_FONT[0], SMALL_FONT[1])
        fpsText = fpsFont.render(u"FPS: {0}".format(fps), True, (0, 0, 0))
        fpsRect = fpsText.get_rect(midtop=(int(SW / 2), int(scaler(10, "y"))))
        screen.blit(fpsText, fpsRect)

        pg.display.update()
        pg.display.set_caption('HAHA CIRCLE GO BRR | FPS: ' + fps)

        clock.tick()

    for i in particles.sprites():
        i.delete()
    return mainMenu, (1,)


# Runs when user presses esc
def pauseMenu(timeWidgets):
    # returnToMain ends both the pause loop and the main loop, so that the
    # program will return back to the main menu
    def returnToMain(menuWidgets, timeWidgets):
        global paused
        global mainprogram
        paused = False
        mainprogram = False

        # Get rid of the time controls
        timeWidgets[0].startAnimation("verticalslide", 0.25, "out", SH, True)

        # Will be true if timeWidgets has not been expanded
        if timeWidgets[0].getRect().centery > SH:
            for i in timeWidgets[1:]:
                i.delete()
            timeWidgets[0].delete()
            del timeWidgets

        # Get rid of the menu
        menuWidgets[-1].startAnimation("centre", 0.25, "out", deleteAfter=True)

    def exitPause(menuWidgets, timeWidgets):
        # Simply ends the pause loop, and starts the disappearing animation
        # for the menu
        global paused
        paused = False
        global currentTimescale
        # Change play button into a pause button
        timeWidgets[2].config(action=lambda: pauseMenu(timeWidgets),
                              image=PAUSE_IMG, hoverImage=H_PAUSE_IMG)

        menuWidgets[-1].startAnimation("centre", 0.25, "out", deleteAfter=True)
        # If current time is earlier or equal to the time that the simulation
        # started, set timescale to 1x, as the user shouldn't be able to rewind
        # to earlier than the beginning of the sim
        if tNow <= 0:
            currentTimescale = 4

    def exitProgram():
        pg.quit()
        quit()

    def hideStats(statList):
        # Menu for showing stats will disappear
        statList[-1].startAnimation("centre", 0.25, "out", deleteAfter=True)

    global paused

    pauseContainer = pgk.Container(pgkRoot, screen,
                                   centre=(SW / 2, SH / 2),
                                   bg=True, bgColour=BG_COLOUR,
                                   maskColour=BG_COLOUR, outlineThickness=3,
                                   outlineColour=(33, 33, 33),
                                   width=scaler(345, "x"),
                                   height=scaler(125, "y"), startVisible=False)

    contWidth = scaler(400, "x")
    gap = scaler(55, "y")

    # Need to initially create menuWidgets as an empty list, so that the
    # buttons can reference it when passing arguments to their functions
    menuWidgets = []
    statList = []

    menuWidgets += [
        pgk.Button(pgkRoot, screen,
                   contWidth - scaler(390, "x"), scaler(10, "y"),
                   font=MID_FONT,
                   bgColour=(33, 33, 33),
                   text="Main Menu",
                   height=scaler(50, "y"),
                   width=scaler(325, "x"),
                   action=lambda: returnToMain(menuWidgets, timeWidgets),
                   container=pauseContainer, swellOnHover=True),
        pgk.Button(pgkRoot, screen,
                   contWidth - scaler(390, "x"), gap + scaler(10, "y"),
                   font=MID_FONT,
                   bgColour=(33, 33, 33),
                   text="Exit Program",
                   height=scaler(50, "y"),
                   width=scaler(325, "x"), action=exitProgram,
                   container=pauseContainer, swellOnHover=True)
    ]

    menuWidgets += [pauseContainer]

    del pauseContainer

    menuWidgets[-1].startAnimation("centre", 0.25, "in")

    # Change pause button into a play button
    timeWidgets[2].config(action=lambda: exitPause(menuWidgets, timeWidgets),
                          image=PLAY_IMG,
                          hoverImage=H_PLAY_IMG)
    pausedFont = pg.font.SysFont(LARGE_FONT[0], LARGE_FONT[1])
    pausedText = pausedFont.render("PAUSED", True, (0, 0, 0))
    pRect = pausedText.get_rect(center=(int(SW / 2), int(scaler(380, "y"))))

    tDisplay = round(tNow, 4)
    timeFont = pg.font.SysFont(MID_FONT[0], MID_FONT[1])
    timeText = timeFont.render("Time: T+" + str(tDisplay), True, (0, 0, 0))
    tRect = timeText.get_rect(topleft=(scaler(10, "x"), scaler(10, "y")))

    # The pause loop is just an empty loop - only showing the UI elements
    # such as fps text, paused text, and time text
    paused = True
    while paused:
        for event in pg.event.get():
            pgkRoot.eventHandler(event)
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    exitPause(menuWidgets, timeWidgets)

            if event.type == MOUSEBUTTONUP:
                if event.button == 3:
                    # Showing particle stat
                    mouseCoords = pg.mouse.get_pos()
                    for i in particles.sprites():
                        if absoluteDistance(pgmath.Vector2(mouseCoords),
                                            i.pos) <= i.radius * scale:
                            if statList:
                                for widget in statList:
                                    widget.delete()
                                del statList

                            # Create container for widgets first,
                            # then position it so that it will always be
                            # on screen.
                            eContainer = pgk.Container(pgkRoot, screen,
                                                       centre=(0, 0),
                                                       outlineThickness=3,
                                                       width=scaler(310,
                                                                    "x"),
                                                       height=scaler(250,
                                                                     "y"),
                                                       bg=True,
                                                       bgColour=(255, 255,
                                                                 255),
                                                       startVisible=False)

                            # Container will be positioned so that one of
                            # its corners will be in the centre of the
                            # particle
                            pos = i.pos
                            if pos[1] + scaler(400, "y") <= SH:
                                if pos[0] + scaler(310, "x") <= SW:
                                    eContainer.config(topleft=pos)
                                else:
                                    eContainer.config(topright=pos)
                            else:
                                if pos[0] + scaler(310, "x") <= SW:
                                    eContainer.config(bottomleft=pos)
                                else:
                                    eContainer.config(bottomright=pos)

                            editContWidth = scaler(310, "x")
                            offset = scaler(150, "x") / 2
                            boxWidth = scaler(125, "x") / 2

                            # Creating list of widgets used in editing
                            # the particle
                            inputList = [
                                pgk.InputBox(pgkRoot, screen,
                                             editContWidth - offset,
                                             scaler(3, "y"),
                                             font=SMALLER_FONT,
                                             bgColour=(222, 222, 222),
                                             inlineText="Coefficient of "
                                                        "Restitution",
                                             width=boxWidth,
                                             allowLetters=False,
                                             allowSpecial=False,
                                             allowSpace=False, charLimit=10,
                                             container=eContainer, canUse=False),
                                pgk.InputBox(pgkRoot, screen,
                                             editContWidth - offset,
                                             scaler(28, "y"),
                                             font=SMALLER_FONT,
                                             bgColour=(222, 222, 222),
                                             inlineText="Velocity to the "
                                                        "right (ms^-1):",
                                             width=boxWidth,
                                             allowLetters=False,
                                             allowSpecial=False,
                                             allowSpace=False, charLimit=10,
                                             container=eContainer, canUse=False),
                                pgk.InputBox(pgkRoot, screen,
                                             editContWidth - offset,
                                             scaler(53, "y"),
                                             font=SMALLER_FONT,
                                             bgColour=(222, 222, 222),
                                             inlineText="Velocity "
                                                        "downwards ("
                                                        "ms^-1):",
                                             width=boxWidth,
                                             allowLetters=False,
                                             allowSpecial=False,
                                             allowSpace=False, charLimit=10,
                                             container=eContainer, canUse=False),
                                pgk.InputBox(pgkRoot, screen,
                                             editContWidth - offset,
                                             scaler(78, "y"),
                                             font=SMALLER_FONT,
                                             bgColour=(222, 222, 222),
                                             inlineText="Acceleration to "
                                                        "the right ("
                                                        "ms^-2):",
                                             width=boxWidth,
                                             allowLetters=False,
                                             allowSpecial=False,
                                             allowSpace=False, charLimit=10,
                                             container=eContainer, canUse=False),
                                pgk.InputBox(pgkRoot, screen,
                                             editContWidth - offset,
                                             scaler(103, "y"),
                                             font=SMALLER_FONT,
                                             bgColour=(222, 222, 222),
                                             inlineText="Acceleration "
                                                        "downwards ("
                                                        "ms^-2):",
                                             width=boxWidth,
                                             allowLetters=False,
                                             allowSpecial=False,
                                             allowSpace=False, charLimit=10,
                                             container=eContainer, canUse=False),
                                pgk.InputBox(pgkRoot, screen,
                                             editContWidth - offset,
                                             scaler(128, "y"),
                                             font=SMALLER_FONT,
                                             bgColour=(222, 222, 222),
                                             inlineText="Radius (m):",
                                             width=boxWidth,
                                             allowLetters=False,
                                             allowSpecial=False,
                                             allowSpace=False, charLimit=10,
                                             container=eContainer, canUse=False),
                                pgk.InputBox(pgkRoot, screen,
                                             editContWidth - offset,
                                             scaler(153, "y"),
                                             font=SMALLER_FONT,
                                             bgColour=(222, 222, 222),
                                             inlineText="Mass (kg):",
                                             width=boxWidth,
                                             allowLetters=False,
                                             allowSpecial=False,
                                             allowSpace=False, charLimit=10,
                                             container=eContainer, canUse=False),
                                pgk.InputBox(pgkRoot, screen,
                                             editContWidth - offset,
                                             scaler(178, "y"),
                                             font=SMALLER_FONT,
                                             bgColour=(222, 222, 222),
                                             inlineText="Height off of "
                                                        "ground (m):",
                                             width=boxWidth,
                                             allowLetters=False,
                                             allowSpecial=False,
                                             allowSpace=False, charLimit=10,
                                             defaultEntry="0",
                                             container=eContainer, canUse=False),
                            ]

                            buttonHeight = inputList[0].getHeight() * 2
                            closeButton = pgk.Button(pgkRoot, screen,
                                                 editContWidth - scaler(225,
                                                                        "x"),
                                                 scaler(203, "y"),
                                                 font=SMALL_FONT,
                                                 bgColour=(33, 33, 33),
                                                 text="Hide Particle Stats",
                                                 height=buttonHeight,
                                                 width=scaler(213, "x"),
                                                 action=lambda: hideStats(statList),
                                                 container=eContainer,
                                                 swellOnHover=True)

                            # Write to the input boxes so that they so
                            # the selected particle's properties
                            inputList[0].write(str(i.restCoefficient))
                            inputList[1].write(str(roundToSigFig(i.velocity.x,
                                                                 3)))
                            inputList[2].write(str(roundToSigFig(i.velocity.y,
                                                                 3)))
                            inputList[3].write(str(i.acceleration.x))
                            inputList[4].write(str(i.acceleration.y))
                            inputList[5].write(str(roundToSigFig(i.radius, 3)))
                            inputList[6].write(str(roundToSigFig(i.mass, 3)))
                            height = (SH - i.pos.y) / scale - i.radius
                            inputList[7].write(str(roundToSigFig(height, 3)))

                            statList = inputList + [closeButton, eContainer]

                            # Delete references
                            del inputList
                            del eContainer

                            statList[-1].startAnimation("centre", 0.25,
                                                        "in")

            if event.type == QUIT:
                paused = False
                pg.quit()
                quit()

        screen.fill(BG_COLOUR)
        particleGraph.draw()

        for sprite in particles.sprites():
            sprite.draw()
            sprite.drawDirectionArrow()

        pgkRoot.update()

        timescaleFont = pg.font.SysFont(SMALL_FONT[0], SMALL_FONT[1])
        tscaleText = timescaleFont.render("Time Multiplier: x" +
                                          str(TIME_SCALES[currentTimescale]),
                                          True, (0, 0, 0))
        tscaleRect = tscaleText.get_rect(topleft=(scaler(10, "x"),
                                                  scaler(50, "y")))

        screen.blit(timeText, tRect)
        screen.blit(tscaleText, tscaleRect)
        screen.blit(pausedText, pRect)

        fps = str(int(clock.get_fps()))
        fpsFont = pg.font.SysFont(SMALL_FONT[0], SMALL_FONT[1])
        fpsText = fpsFont.render(u"FPS: {0}".format(fps), True, (0, 0, 0))
        fpsRect = fpsText.get_rect(midtop=(int(SW / 2), int(scaler(10, "y"))))
        screen.blit(fpsText, fpsRect)

        pg.display.update()

        pg.display.set_caption('HAHA CIRCLE GO BRR | FPS: ' + fps)
        clock.tick()


# noinspection PyUnboundLocalVariable


if __name__ == "__main__":  # If program is run as a script, this will run

    exitProgram = False
    while not exitProgram:
        pg.init()
        pg.font.init()


        # scales sizes relative to screen width/height - gives a consistent feel
        # across all devices
        def scaler(toscale, axis):
            if axis == 'x':
                return int(toscale * (SW / 1920))
            else:
                return int(toscale * (SH / 1080))


        # Does the opposite of scaler - needed when saving scenarios, as the
        # values will need to be rescaled when the scenario is loaded
        def descaler(toscale, axis):
            if axis == "x":
                return int(toscale * (1920 / SW))
            else:
                return int(toscale * (1080 / SH))


        if USER32:
            USER32.SetProcessDPIAware()
            SW = USER32.GetSystemMetrics(0)
            SH = USER32.GetSystemMetrics(1)
        else:
            SW = 1920
            SH = 1080

        BG_COLOUR = (244, 244, 244)

        scale = scaler(100, "x")
        previousScale = scale

        # Fullscreen doesn't work with pg.mouse.set_visible() (mouse gets
        # centred every time function is called), so I am using a borderless
        # window that is the same size as the screen instead. os.environ
        # positions the window in the top left corner of the screen
        os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

        # Display flags: NOFRAME to simulate a fullscreen display, and DOUBLEBUF
        # to prevent flickering - it also slightly improves fps
        screen = pg.display.set_mode((SW, SH), NOFRAME | DOUBLEBUF)
        screen.set_alpha(None)

        particleGraph = Graph(screen, SW, SH, (0, 0), BG_COLOUR, scale, scale)

        # Read a dictionary in from a file
        with open("materials.txt", "r") as file:
            contents = file.read()

        # ast.literal_eval reads the contents of the file, and evaluates the
        # string as a python expression - in this case a dictionary
        MATERIALS = ast.literal_eval(contents)
        MATERIALS_SORTED = sorted(MATERIALS)

        with open("customMaterials.txt", "r") as file:
            contents = file.read()

        customMaterials = ast.literal_eval(contents)
        sortedCustoms = sorted(customMaterials)

        timeMultiplier = 1 / 60  # Initial value for time between frames
        TIME_SCALES = [-2, -1, -0.5, 0.5, 1, 2]
        currentTimescale = 4
        tNow = 0
        frameNumber = 0

        imagesFolder = Path("resources/images/")
        saveLocation = Path("Saved Scenarios/")

        # Used for drawDirectionArrow method
        ARROW_IMAGE = pg.image.load(
            str(imagesFolder / "arrow.png")).convert_alpha()

        SCALE_TOOL_IMG = pg.image.load(
            str(imagesFolder / "resizeCursor.png")).convert_alpha()

        PAUSE_IMG = pg.image.load(
            str(imagesFolder / "pausedNormal.png")).convert_alpha()
        H_PAUSE_IMG = pg.image.load(
            str(imagesFolder / "pausedHovered.png")).convert_alpha()

        PLAY_IMG = pg.image.load(
            str(imagesFolder / "playNormal.png")).convert_alpha()
        H_PLAY_IMG = pg.image.load(
            str(imagesFolder / "playHovered.png")).convert_alpha()

        FF_IMG = pg.image.load(
            str(imagesFolder / "ffNormal.png")).convert_alpha()
        H_FF_IMG = pg.image.load(
            str(imagesFolder / "ffHovered.png")).convert_alpha()

        RW_IMG = pg.transform.flip(FF_IMG, True, False)
        H_RW_IMG = pg.transform.flip(H_FF_IMG, True, False)

        TT_IMG = pg.image.load(
            str(imagesFolder / "timeTabNormal.png")).convert_alpha()
        H_TT_IMG = pg.image.load(
            str(imagesFolder / "timeTabHovered.png")).convert_alpha()

        PREV_IMG = pg.image.load(
            str(imagesFolder / "prevPage.png")).convert_alpha()
        NEXT_IMG = pg.image.load(
            str(imagesFolder / "nextPage.png")).convert_alpha()

        R_MENU_IMG = pg.image.load(
            str(imagesFolder / "rMainMenu.png")).convert_alpha()
        L_MENU_IMG = pg.image.load(
            str(imagesFolder / "lMainMenu.png")).convert_alpha()
        
        if SW / 1920 > SH / 1080:
            # Scales font sizes relative to whichever axis has been 'scaled
            # down' more, to prevent text being larger than the widget it is in
            SMALLER_FONT = ("Helvetica", scaler(12, "y"))
            SMALL_FONT = ("Helvetica", scaler(18, "y"))
            MID_FONT = ("Helvetica", scaler(30, "y"))
            LARGE_FONT = ("Helvetica", scaler(72, "y"))

        else:
            SMALLER_FONT = ("Helvetica", scaler(12, "x"))
            SMALL_FONT = ("Helvetica", scaler(18, "x"))
            MID_FONT = ("Helvetica", scaler(30, "x"))
            LARGE_FONT = ("Helvetica", scaler(72, "x"))

        mainmenu = False
        setting = False
        mainprogram = False
        paused = False
        mainWidgets = []

        pg.display.set_caption('HAHA CIRCLE GO BRRRRRR')
        clock = pg.time.Clock()
        particles = pg.sprite.Group()

        nextFunction, args = mainMenu(1)
        # Prevents recursion (For example, mainMenu would be called
        # from within main, which would be called from within setup, which would
        # be called from within mainMenu, and so on) which would
        while True:
            nextFunction, args = nextFunction(*args)
