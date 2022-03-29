import time
from pathlib import Path
from math import sqrt, floor

import pygame as pg
from pygame.locals import *

try:
    from pyClipTools import paste
except ImportError:
    def paste():
        return ""


# PyClipTools is an external module that allows text to be written to and
# read from the windows clipboard from within python

class Pgk(object):
    def __init__(self):  # Initialises pgkinter - creates all necessary globals
        pg.font.init()
        self.pgkGroup = pg.sprite.Group()

        imagesFolder = Path("resources/images/")
        self.pgkTypingCursor = pg.image.load(
            str(imagesFolder / "pgkTypingCursor.png"))
        self.pgkPointerCursor = pg.image.load(
            str(imagesFolder / "pgkPointerCursor.png"))
        self.pgkLetterChars = set(
            "aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpPqQrRsStTuUvVwWxXyYzZ")
        self.pgkNumberChars = set("1234567890")
        self.pgkMathsChars = set("-.eE")  # Include "e" for standard form
        self.pgkSpecialChars = set("¬`!\"£$%^&*()_-+={[}]:;@'~#<,>.?/|\\¦")
        self.pgkWhiteCrossImage = pg.image.load(
            str(imagesFolder / "pgkWhiteCross.png"))
        self.pgkBlackCrossImage = pg.image.load(
            str(imagesFolder / "pgkBlackCross.png"))
        print("Pgkinter V1.0.0 initialised successfully! Hello there!")

    def buttonDefaultAction(self):
        # Default action that will be assigned to buttons if none is assigned on
        # instantiation
        pass

    def getWidgets(self):
        return self.pgkGroup.sprites()

    def hoverEffect(self, rgb):
        # Returns an rgb code that is lighter or darker than the one passed to
        # the function, depending on whether the original is light or dark
        if self.isLight(rgb):
            return rgb[0] * 1 / 2, rgb[1] * 1 / 2, rgb[2] * 1 / 2
        else:
            return (
                rgb[0] + ((255 - rgb[0]) * 1 / 2),
                rgb[1] + ((255 - rgb[1]) * 1 / 2),
                rgb[2] + ((255 - rgb[2]) * 1 / 2))

    def isLight(self, rgb):  # Determines whether an rgb code is light or dark
        """Treats the rgb code as a 3D position vector and calculates the length of
        the line from the origin to the position vector. The longer the line,
        the lighter the colour.

        """
        if sqrt(rgb[0] ** 2 + rgb[1] ** 2 + rgb[2] ** 2) >= 220:
            return True

        else:
            return False

    # noinspection SpellCheckingInspection
    def update(self):  # Only need pgkinter.update() in main code
        self.pgkGroup.update()

    # noinspection SpellCheckingInspection,SpellCheckingInspection
    def eventHandler(self, event):
        # Takes an event list from the main pygame loop, and passes it to every
        # pgkinter sprite.
        handled = False
        for obj in self.pgkGroup.sprites():
            # InputBoxes can handle events even after one has been handled as
            # they need to be able to become inactive
            if not handled or isinstance(obj, InputBox):
                if obj.handleEvent(event):
                    handled = True
        return handled


# noinspection PyArgumentList
class Button(pg.sprite.Sprite):
    # noinspection SpellCheckingInspection
    def __init__(self, parent, screen, x, y, font=None, bgColour=None,
                 text=None, height=None, width=None,
                 action=None, image=None, hoverImage=None, container=None,
                 swellOnHover=None):
        super().__init__()  # Runs pygame sprite __init__() method
        self.__parent = parent
        self.__screen = screen
        self.__timer = 0.5  # Starts at 0.5 so button is usable instantly
        self.__previousFrame = time.time()
        self.__hovered = False

        try:  # Input validation
            x = int(x)
            y = int(y)
        except ValueError:
            raise Exception("Button coordinates must be integers")

        """Almost all attributes have default values that will be assigned if
        no values are passed on instantiation.

        """

        if font is None:
            self.__font = pg.font.SysFont("Helvetica", 30)
        else:
            self.__font = pg.font.SysFont(font[0], font[1])

        if bgColour is None:
            self.__bgColour = (255, 255, 255)
        else:
            self.__bgColour = bgColour

        if text is None:
            self.__text = ""
        else:
            self.__text = text

        # Changes text colour depending on whether the background colour is
        # light or not.
        if self.__parent.isLight(self.__bgColour):
            self.__displayText = self.__font.render(self.__text, True,
                                                    (0, 0, 0))
        else:
            self.__displayText = self.__font.render(self.__text, True,
                                                    (255, 255, 255))

        if not height:
            self.__height = self.__displayText.get_rect().h * 1.25
        else:
            self.__height = height

        if not width:
            self.__width = int(pg.display.get_surface().get_width() / 10)
        else:
            self.__width = width

        if not action:
            self.__action = self.__parent.buttonDefaultAction
        else:
            self.__action = action

        if image is None:
            self.__image = None
        else:
            self.__image = pg.transform.scale(image, (self.__width,
                                                      self.__height))

        if hoverImage is None:
            self.__hoverImage = None
        else:
            self.__hoverImage = pg.transform.scale(hoverImage, (self.__width,
                                                                self.__height))

        self.__bgColourHover = self.__parent.hoverEffect(self.__bgColour)

        self.__coords = [x, y]

        self.__rect = pg.Rect(x, y, self.__width, self.__height)

        # Uses 0.45 * height as 0.5 places text slightly below-centre
        self.__textRect = self.__displayText.get_rect(
            center=(x + 0.5 * self.__width, y + 0.45 * self.__height))

        if self.__image is not None:
            self.__rect = self.__image.get_rect(topleft=(x, y))

        if container is None:
            self.__container = None
        else:
            self.__container = container
            self.__container.addWidget(self)

        if swellOnHover is None:
            self.__swellOnHover = False
        else:
            self.__swellOnHover = True
            self.__origWidth = self.__width
            self.__origHeight = self.__height

        self.__parent.pgkGroup.add(self)

    def config(self, font=None, bgColour=None, text=None,
               height=None, width=None, action=None, image=None,
               hoverImage=None):
        """Config method allows the programmer to change any settings that may
        have a default value after instantiation.

        """

        if not font:
            pass
        else:
            self.__font = pg.font.SysFont(font[0], font[1])
            if self.__parent.isLight(self.__bgColour):
                self.__displayText = self.__font.render(self.__text, True,
                                                        (0, 0, 0))
            else:
                self.__displayText = self.__font.render(self.__text, True,
                                                        (255, 255, 255))

        if not bgColour:
            pass
        else:
            self.__bgColour = bgColour
            self.__bgColourHover = self.__parent.hoverEffect(bgColour)

        if not text:
            pass
        else:
            if self.__parent.isLight(self.__bgColour):
                self.__text = text
                self.__displayText = self.__font.render(self.__text, True,
                                                        (0, 0, 0))
            else:
                self.__text = text
                self.__displayText = self.__font.render(self.__text, True,
                                                        (255, 255, 255))

        if not height:
            pass
        else:
            self.__height = height

        if not width:
            pass
        else:
            self.__width = width

        if not action:
            pass
        else:
            self.__action = action

        if image is None:
            pass
        else:
            self.__image = pg.transform.scale(image, (int(self.__width),
                                                      int(self.__height)))

        if hoverImage is None:
            pass
        else:
            self.__hoverImage = pg.transform.scale(hoverImage,
                                                   (int(self.__width),
                                                    int(self.__height)))

        self.__textRect = self.__displayText.get_rect(
            center=(self.__rect.x + 0.5 * self.__width,
                    self.__rect.y + 0.45 * self.__height))

    def delete(self):
        # Need to set mouse back to normal, otherwise the mouse will remain
        # hidden after the widget has been deleted
        pg.mouse.set_cursor(*pg.cursors.arrow)
        self.__parent.pgkGroup.remove(self)

        if self.__container:
            self.__container.removeWidget(self)

        del self

    def draw(self):
        # Made draw its own function, as widgets need to be drawn in a
        # different order if they are in a container

        if self.__container:
            x, y = self.__container.getCorrectedCoords(self.__coords)
            self.__rect = pg.Rect(x, y, self.__width, self.__height)

            # Uses 0.45 * height as 0.5 places text slightly below-centre
            self.__textRect = self.__displayText.get_rect(
                center=(x + 0.5 * self.__width, y + 0.45 * self.__height))

        if self.__hovered and self.__timer > 0.5:
            if self.__image is None:
                # Draws button with hover colour variant
                pg.draw.rect(self.__screen, self.__bgColourHover, self.__rect)
                self.__screen.blit(self.__displayText, self.__textRect)
            else:
                self.__screen.blit(self.__hoverImage, self.__rect)

            pg.mouse.set_visible(False)
            # Draws custom mouse image over mouse location
            self.__pointerRect = self.__parent.pgkPointerCursor.get_rect(
                top=pg.mouse.get_pos()[1])
            self.__pointerRect.x = pg.mouse.get_pos()[
                                       0] - self.__pointerRect.w / 2
            self.__screen.blit(self.__parent.pgkPointerCursor,
                               self.__pointerRect)

        elif not self.__hovered or self.__timer < 0.5:
            if self.__image is None:
                # Draws button with regular colour
                pg.draw.rect(self.__screen, self.__bgColour, self.__rect)
                self.__screen.blit(self.__displayText, self.__textRect)
            else:
                self.__screen.blit(self.__image, self.__rect)

    def getHeight(self):
        return self.__height

    def getWidth(self):
        return self.__width

    def getPos(self):
        return self.__rect.x, self.__rect.y

    def isHovered(self):
        return self.__hovered

    # Swell and shrink are button animations that make the button change size
    # when you hover over it - gives the UI a more modern and sleek feel
    def swell(self):
        # Works very similarly to container animations

        # Multiplier controls how much the button swells by, in order to make
        # the animation last a certain length of time (0.25 seconds)
        multiplier = (time.time() - self.__previousFrame) / 0.25

        widthDifference = self.__origWidth * 1.05 - self.__origWidth
        heightDifference = self.__origHeight * 1.25 - self.__origHeight

        # Can only add increments greater than 0/5 as pygame rect dimensions
        # are stored as ints - anything smaller than 0.5 would have no effect
        # on the size, and would be stuck in an infinite loop
        if widthDifference * multiplier > 0.5:
            self.__width += widthDifference * multiplier
            self.__coords[0] -= widthDifference * multiplier / 2
        else:
            self.__width += 1
            self.__coords[0] -= 0.5

        if heightDifference * multiplier > 0.5:
            self.__height += heightDifference * multiplier
            self.__coords[1] -= heightDifference * multiplier / 2
        else:
            self.__height += 1
            self.__coords[1] -= 0.5

    def shrink(self):
        # Identical to swell function, but inverse signs
        multiplier = (time.time() - self.__previousFrame) / 0.25

        widthDifference = self.__origWidth * 1.05 - self.__origWidth
        heightDifference = self.__origHeight * 1.25 - self.__origHeight

        if widthDifference * multiplier > 0.5:
            self.__width -= widthDifference * multiplier
            self.__coords[0] += widthDifference * multiplier / 2
        else:
            self.__width -= 1
            self.__coords[0] += 0.5

        if heightDifference * multiplier > 0.5:
            self.__height -= heightDifference * multiplier
            self.__coords[1] += heightDifference * multiplier / 2
        else:
            self.__height -= 1
            self.__coords[1] += 0.5

    # noinspection PyAttributeOutsideInit
    def update(self):
        # 0.5 timer check ensures that button can only be clicked once every
        # 0.5 seconds
        if self.__rect.collidepoint(pg.mouse.get_pos()) and not self.__hovered:
            # Can only be hovered over if button is not obstructed by
            # container mask
            if (self.__container and not self.__container.mouseMasked()) or \
                    not self.__container:
                # Sets mouse cursor to invisible
                self.__hovered = True

        elif not self.__rect.collidepoint(
                pg.mouse.get_pos()) and self.__hovered:
            # Sets mouse cursor back to default
            pg.mouse.set_visible(True)
            self.__hovered = False

        if self.__swellOnHover and self.__hovered:
            if self.__rect.height < self.__origHeight * 1.25 and \
                    self.__rect.width < self.__origWidth * 1.05:
                self.swell()
            elif self.__rect.height > self.__origHeight * 1.25 or \
                    self.__rect.width > self.__origWidth * 1.05:
                self.__rect.height = self.__origHeight * 1.25
                self.__rect.width = self.__origWidth * 1.05

        if self.__swellOnHover and not self.__hovered:
            if self.__rect.height > self.__origHeight and \
                    self.__rect.width > self.__origWidth:
                self.shrink()
            if self.__rect.height < self.__origHeight or \
                    self.__rect.width < self.__origWidth:
                self.__rect.height = self.__origHeight
                self.__rect.width = self.__origWidth

        # If button is not in a container, it can be drawn normally
        if not self.__container:
            self.draw()

        self.__timer += time.time() - self.__previousFrame
        self.__previousFrame = time.time()

    def handleEvent(self, event):
        """ Due to the nature of pygame's events, you cannot have a for loop
                in the class update() method that checks for events, as each event can
                only be handled once, as it is effectively destroyed on handling.
                This means that you need a separate event handling function, which you
                can then pass events to from the main pygame loop.

                """

        if self.__hovered and self.__timer > 0.5:
            # Only checks for events if the pointer is on the button
            if event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    if self.__swellOnHover:
                        # Return button to normal size
                        self.__rect.height = self.__origHeight
                        self.__rect.width = self.__origWidth
                    self.__action()
                    pg.mouse.set_visible(True)
                    self.__hovered = False
                    self.__timer = 0
                    return True


# noinspection PyArgumentList
class Checkbox(pg.sprite.Sprite):

    # noinspection SpellCheckingInspection
    def __init__(self, parent, screen, x, y, font=None, bgColour=None,
                 textColour=None, inlineText=None, height=None, container=None):
        super().__init__()
        self.__parent = parent
        self.__screen = screen
        self.__hovered = False
        self.__output = False

        try:  # Coordinate input validation
            x = int(x)
            y = int(y)
        except ValueError:
            raise Exception("Checkbox coordinates must be integers")

        """Almost all attributes have default values that will be assigned if
        no values are passed on instantiation.

        """

        if not font:
            self.__font = pg.font.SysFont("Helvetica", 30)
        else:
            self.__font = pg.font.SysFont(font[0], font[1])

        if not bgColour:
            self.__bgColour = (255, 255, 255)
        else:
            self.__bgColour = bgColour

        if not textColour:
            self.__textColour = (0, 0, 0)
        else:
            self.__textColour = textColour

        if not inlineText:
            self.__inlineText = ""
        else:
            self.__inlineText = inlineText

        # Renders inlineText as a pygame surface object
        self.__inlineDisplayText = self.__font.render(self.__inlineText, True,
                                                      self.__textColour)

        if not height:
            # Height and width of checkbox scales with the font
            self.__height = self.__inlineDisplayText.get_rect().h * 1.25
            self.__width = self.__height
        else:
            self.__height = self.__width = height

        if container is None:
            self.__container = None
        else:
            self.__container = container
            self.__container.addWidget(self)

        self.__coords = (x, y)

        # Aligns text with the checkbox
        self.__inlineTextRect = self.__inlineDisplayText.get_rect(
            center=(x - self.__inlineDisplayText.get_rect().w * 0.6,
                    y + 0.45 * self.__height))

        self.__rect = pg.Rect(x, y, self.__width, self.__height)

        # Default output is blank (False)
        self.__outputDisplay = self.__font.render("", True, (0, 0, 0))

        # Ordering of widgets - Containers first, then labels, dropdowns,
        # input boxes, checkboxes, then buttons. Helps with widgets handling
        # events in the correct order - stops buttons 'hijacking' click
        # events from dropdown menus drawn on top of them.
        index = 0
        inGroup = False
        for i in self.__parent.pgkGroup.sprites():
            if isinstance(i, Button):
                after = self.__parent.pgkGroup.sprites()[index:]
                for sprite in after:
                    self.__parent.pgkGroup.remove(sprite)
                self.__parent.pgkGroup.add(self)
                for sprite in after:
                    self.__parent.pgkGroup.add(sprite)
                inGroup = True
            index += 1

        if not inGroup:
            self.__parent.pgkGroup.add(self)

    def config(self, font=None, bgColour=None, textColour=None,
               inlineText=None):
        # Allows modification of attributes that were not assigned during
        # instantiation

        if not font:
            pass
        else:
            self.__font = pg.font.SysFont(font[0], font[1])

        if not bgColour:
            pass
        else:
            self.__bgColour = bgColour

        if not textColour:
            pass
        else:
            self.__textColour = textColour

        if not inlineText:
            pass
        else:
            self.__inlineText = inlineText

        self.__inlineDisplayText = self.__font.render(self.__inlineText, True,
                                                      self.__textColour)

        self.__inlineTextRect = self.__inlineDisplayText.get_rect(
            center=(self.__rect.x - self.__inlineDisplayText.get_rect().w * 0.6,
                    self.__rect.y + 0.45 * self.__height))

        # Needs different outputDisplay depending on whether or not checkbox
        # has been activated
        if self.__output:
            # self.__parent.isLight function checks background colour - white cross on dark
            # backgrounds, black on light backgrounds.
            if self.__parent.isLight(self.__bgColour):
                self.__outputDisplay = self.__parent.pgkBlackCrossImage
            else:
                self.__outputDisplay = self.__parent.pgkWhiteCrossImage

            # Scales cross to fill the checkbox, no matter what size
            self.__outputDisplay = pg.transform.scale(self.__outputDisplay,
                                                      (floor(self.__width),
                                                       floor(self.__height)))

        else:
            self.__outputDisplay = self.__font.render("", True, (0, 0, 0))

    def click(self):
        if self.__output:
            self.__output = False
            self.__outputDisplay = self.__font.render("", True,
                                                      (0, 0, 0))
        else:
            self.__output = True

            if self.__parent.isLight(self.__bgColour):
                self.__outputDisplay = self.__parent.pgkBlackCrossImage
            else:
                self.__outputDisplay = self.__parent.pgkWhiteCrossImage

            self.__outputDisplay = pg.transform.scale(
                self.__outputDisplay, (floor(self.__width),
                                       floor(self.__height)))

    def delete(self):
        pg.mouse.set_cursor(*pg.cursors.arrow)
        self.__parent.pgkGroup.remove(self)

        if self.__container:
            self.__container.removeWidget(self)

        del self

    def draw(self):
        if self.__container:
            x, y = self.__container.getCorrectedCoords(self.__coords)
            # Aligns text with the checkbox
            self.__inlineTextRect = self.__inlineDisplayText.get_rect(
                center=(x - self.__inlineDisplayText.get_rect().w * 0.6,
                        y + 0.45 * self.__height))

            self.__rect = pg.Rect(x, y, self.__width, self.__height)

        pg.draw.rect(self.__screen, self.__bgColour, self.__rect)

        self.__screen.blit(self.__outputDisplay, self.__rect)

        if self.__hovered:
            # PointerRect is modified in order to appear similarly to how the
            # pointer appears in windows, with the top of the hand in line
            # with the location that the mouse is pointing to.
            self.__pointerRect = self.__parent.pgkPointerCursor.get_rect(
                top=pg.mouse.get_pos()[1])
            self.__pointerRect.x = pg.mouse.get_pos()[
                                       0] - self.__pointerRect.w / 2
            self.__screen.blit(self.__parent.pgkPointerCursor,
                               self.__pointerRect)

        self.__screen.blit(self.__inlineDisplayText, self.__inlineTextRect)

    def get(self):
        return self.__output

    def getHeight(self):
        return self.__height

    def getWidth(self):
        return self.__width

    def getPos(self):
        return self.__rect.x, self.__rect.y

    # noinspection PyAttributeOutsideInit
    def update(self):
        if self.__rect.collidepoint(pg.mouse.get_pos()) and not self.__hovered:
            # Can only be hovered over if checkbox is not obstructed by
            # container mask
            if (self.__container and not self.__container.mouseMasked()) or \
                    not self.__container:
                # Sets mouse cursor to invisible
                pg.mouse.set_visible(False)
                self.__hovered = True

        elif not self.__rect.collidepoint(
                pg.mouse.get_pos()) and self.__hovered:
            # Sets mouse cursor back to default
            pg.mouse.set_visible(True)
            self.__hovered = False

        if not self.__container:
            self.draw()

    def handleEvent(self, event):
        # Mouse click event is only checked for when the pointer is hovering
        # over the checkbox
        if self.__hovered and event.type == MOUSEBUTTONUP:
            if event.button == 1:
                self.click()
                return True


class Container(pg.sprite.Sprite):
    def __init__(self, parent, screen, outlineColour=None,
                 outlineThickness=None, bg=False, bgColour=None,
                 height=None, width=None, topleft=None, topright=None,
                 bottomleft=None, bottomright=None, centre=None,
                 startVisible=True, maskColour=None):
        super().__init__()
        self.__parent = parent
        self.__screen = screen

        self.__widgets = pg.sprite.Group()
        self.__animation = [None, None, None]

        if outlineColour is None:
            self.__outlineColour = (33, 33, 33)
        else:
            self.__outlineColour = outlineColour

        if outlineThickness is None:
            self.__outlineThickness = 0
        else:
            if outlineThickness < 0:
                outlineThickness = 0
            self.__outlineThickness = outlineThickness

        if bg:
            self.__bg = True
            if bgColour is None:
                self.__bgColour = (222, 222, 222)
            else:
                self.__bgColour = bgColour
        else:
            self.__bg = False

        if height is None:
            self.__height = 200
        else:
            self.__height = height

        if width is None:
            self.__width = 100
        else:
            self.__width = width

        # In order to create the outline, I will have two rects - outlineRect
        # and rect. outlineRect will be the colour of the outline, and will
        # be slightly bigger than rect. It will be drawn first, with rect on
        # top, so that only the edges will show, giving the appearance of an
        # outline.

        self.__fullHeight = self.__height + self.__outlineThickness * 2
        self.__halfHeight = int(self.__fullHeight / 2)
        self.__fullWidth = self.__width + self.__outlineThickness * 2
        self.__halfWidth = int(self.__fullWidth / 2)

        self.__rect = pg.Rect(0, 0, self.__width, self.__height)
        self.__outlineRect = pg.Rect(0, 0, self.__fullWidth,
                                     self.__fullHeight)

        if maskColour is None:
            self.__maskColour = (255, 255, 255)
        else:
            self.__maskColour = maskColour

        if topleft is not None:
            self.__rect.topleft = (int(topleft[0]), int(topleft[1]))

        elif topright is not None:
            self.__rect.topright = (int(topright[0]), int(topright[1]))

        elif bottomleft is not None:
            self.__rect.bottomleft = (int(bottomleft[0]), int(bottomleft[1]))

        elif bottomright is not None:
            self.__rect.bottomright = (int(bottomright[0]), int(bottomright[1]))

        elif centre is not None:
            self.__rect.center = (int(centre[0]), int(centre[1]))

        self.__outlineRect.center = self.__rect.center

        # In order to create the illusion of the container hiding widgets,
        # I will use a 'mask' rect that is the same size as the container -
        # this will be set to the same colour as the background in the main
        # part of my code, making a seamless look
        if startVisible:
            self.__maskLeftRect = pg.Rect(0, 0, 0, 0)
            self.__maskRightRect = pg.Rect(0, 0, 0, 0)
            self.__maskTopRect = pg.Rect(0, 0, 0, 0)
            self.__maskBottomRect = pg.Rect(0, 0, 0, 0)

        elif not startVisible:
            self.__maskLeftRect = pg.Rect(0, 0, self.__halfWidth,
                                          self.__fullHeight)
            self.__maskRightRect = pg.Rect(0, 0, self.__halfWidth,
                                           self.__fullHeight)
            self.__maskTopRect = pg.Rect(0, 0, self.__fullWidth,
                                         self.__halfHeight)
            self.__maskBottomRect = pg.Rect(0, 0, self.__fullWidth,
                                            self.__halfHeight)

        self.__maskLeftRect.topleft = self.__outlineRect.topleft
        self.__maskRightRect.topright = self.__outlineRect.topright
        self.__maskTopRect.topleft = self.__outlineRect.topleft
        self.__maskBottomRect.bottomleft = self.__outlineRect.bottomleft

        # This attribute will be set in the startAnimation method, and will
        # determine whether or not the container - and widgets inside of it -
        # will be deleted once the animation has finished. This means there
        # is no need for loads of timing variables in the main code.
        self.__deleteAfter = False

        if len(self.__parent.pgkGroup.sprites()) > 0:
            after = self.__parent.pgkGroup.sprites()[1:]
            for sprite in after:
                self.__parent.pgkGroup.remove(sprite)
            self.__parent.pgkGroup.add(self)
            for sprite in after:
                self.__parent.pgkGroup.add(sprite)

        else:
            self.__parent.pgkGroup.add(self)

        self.__previousFrame = time.time()

    def config(self, outlineColour=None,
               outlineThickness=None, bg=False, bgColour=None,
               height=None, width=None, topleft=None, topright=None,
               bottomleft=None, bottomright=None, centre=None,
               maskColour=None):

        if outlineColour is None:
            pass
        else:
            self.__outlineColour = outlineColour

        if outlineThickness is None:
            pass
        else:
            if outlineThickness < 0:
                outlineThickness = 0
            self.__outlineThickness = outlineThickness

        if bg:
            self.__bg = True
            if bgColour is None:
                self.__bgColour = (222, 222, 222)
            else:
                self.__bgColour = bgColour
        else:
            pass

        if height is None:
            pass
        else:
            self.__height = height

        if width is None:
            pass
        else:
            self.__width = width

        # In order to create the outline, I will have two rects - outlineRect
        # and rect. outlineRect will be the colour of the outline, and will
        # be slightly bigger than rect. It will be drawn first, with rect on
        # top, so that only the edges will show, giving the appearance of an
        # outline.

        self.__fullHeight = self.__height + self.__outlineThickness * 2
        self.__halfHeight = int(self.__fullHeight / 2)
        self.__fullWidth = self.__width + self.__outlineThickness * 2
        self.__halfWidth = int(self.__fullWidth / 2)

        if maskColour is None:
            pass
        else:
            self.__maskColour = maskColour

        if topleft is not None:
            self.__rect.topleft = (int(topleft[0]), int(topleft[1]))

        elif topright is not None:
            self.__rect.topright = (int(topright[0]), int(topright[1]))

        elif bottomleft is not None:
            self.__rect.bottomleft = (int(bottomleft[0]), int(bottomleft[1]))

        elif bottomright is not None:
            self.__rect.bottomright = (int(bottomright[0]), int(bottomright[1]))

        elif centre is not None:
            self.__rect.center = (int(centre[0]), int(centre[1]))

        self.__outlineRect.center = self.__rect.center

        self.__maskLeftRect.topleft = self.__outlineRect.topleft
        self.__maskRightRect.topright = self.__outlineRect.topright
        self.__maskTopRect.topleft = self.__outlineRect.topleft
        self.__maskBottomRect.bottomleft = self.__outlineRect.bottomleft

    def addWidget(self, widget):
        self.__widgets.add(widget)

    def delete(self):
        self.__parent.pgkGroup.remove(self)
        del self

    def getCorrectedCoords(self, coords):
        newX = self.__rect.topleft[0] + coords[0]
        newY = self.__rect.topleft[1] + coords[1]

        return newX, newY

    def getRect(self):
        return self.__rect

    def animationDone(self):
        if self.__animation == [None, None, None]:
            return True
        else:
            return False

    def handleEvent(self, event):
        pass

    def isEmpty(self):
        if len(self.__widgets.sprites()) == 0:
            return True
        else:
            return False

    def isMasked(self):
        if (self.__maskRightRect.width == self.__halfWidth and
            self.__maskLeftRect.width == self.__halfWidth) or \
                (self.__maskTopRect.height == self.__halfHeight and
                 self.__maskBottomRect.height == self.__halfHeight):
            return True
        else:
            return False

    def mouseMasked(self):
        # If the mouse is blocked by the masks, then this will be True - used
        # to prevent clickthrough, allowing the user to interact with buttons
        # even when they are hidden by the masks
        mouseCoords = pg.mouse.get_pos()
        for i in [self.__maskBottomRect, self.__maskLeftRect,
                  self.__maskTopRect, self.__maskRightRect]:
            if i.collidepoint(mouseCoords[0], mouseCoords[1]):
                return True
        return False

    def onScreen(self):
        if self.__animation[0] is None:
            sw, sh = pg.display.get_surface().get_size()
            if self.__rect.bottom <= 0:
                return False
            elif self.__rect.top >= sh:
                return False
            elif self.__rect.topright[0] <= 0:
                return False
            elif self.__rect.topleft[0] >= sw:
                return False
            else:
                return True

        return True

    def removeWidget(self, widget):
        self.__widgets.remove(widget)

    def startAnimation(self, type, time, inOut, startFrom=None,
                       deleteAfter=None, destination=None):
        self.__animation = [type, time, inOut]

        self.__deleteAfter = deleteAfter
        if startFrom is not None:
            # startFrom is needed for animations that involve the whole
            # container moving
            self.__animation.append(startFrom)

            # Can now specify where the container will finish its animation,
            # instead of always finishing where it was when the animation was
            # started. Useful if a container needs to slide off screen to the
            # left and come back on from the right, for example.
            if destination:
                self.__rect.x = destination[0]
                self.__rect.y = destination[1]

            self.__animation.append(self.__rect.x)
            self.__animation.append(self.__rect.y)

            if type in ["horizontalslide", "verticalslide"]:
                # Don't need masks for these animations, so set them all to be
                # invisible
                self.__maskLeftRect.width = 0
                self.__maskRightRect.width = 0
                self.__maskTopRect.height = 0
                self.__maskBottomRect.height = 0

            if type == "horizontalslide" and inOut != "out":
                self.__rect.x = startFrom

            elif type == "verticalslide" and inOut != "out":
                self.__rect.y = startFrom

    def centreAnimation(self):
        # Container, and widgets inside of it, will appear from the centre
        # outwards.
        time = self.__animation[1]
        inOut = self.__animation[2]

        # How much does the width/height change every frame?
        multiplier = self.__frameTime / time

        # Divide by 2 as each mask takes up half of its dimension
        widthChange = int(self.__fullWidth * multiplier / 2)
        heightChange = int(self.__fullHeight * multiplier / 2)

        # At small resolutions and high frame rates, these values will
        # occasionally be calculated to be 0, meaning the masks will not change
        # sizes. In that case, they need to be set to 1
        if widthChange < 1:
            widthChange = 1
        if heightChange < 1:
            heightChange = 1

        # If the container is appearing
        if inOut == "in":
            # Widths/heights of masks cannot go lower than 0, otherwise they
            # would extend out the other way, resulting in longer times for
            # disappearing animations
            if self.__maskLeftRect.width > 0:
                self.__maskLeftRect.width -= widthChange
            else:
                self.__maskLeftRect.width = 0

            if self.__maskRightRect.width > 0:
                self.__maskRightRect.width -= widthChange
            else:
                self.__maskRightRect.width = 0

            if self.__maskTopRect.height > 0:
                self.__maskTopRect.height -= heightChange
            else:
                self.__maskTopRect.height = 0

            if self.__maskBottomRect.height > 0:
                self.__maskBottomRect.height -= heightChange
            else:
                self.__maskBottomRect.height = 0

            # If all masks have completely disappeared, the animation is
            # finished
            if self.__maskLeftRect.width == 0 and \
                    self.__maskRightRect.width == 0 and \
                    self.__maskTopRect.height == 0 and \
                    self.__maskBottomRect.height == 0:
                self.__animation = [None, None, None]

                if self.__deleteAfter:
                    for widget in self.__widgets:
                        widget.delete()
                    self.delete()

        elif inOut == "out":
            # Same as for when the container is appearing, but invert the
            # width/height change
            widthChange *= -1
            heightChange *= -1

            # This time check dimensions of masks against the dimensions of
            # the container (divided by 2 as each mask takes up half of the
            # container)
            if self.__maskLeftRect.width < self.__halfWidth:
                self.__maskLeftRect.width -= widthChange
            else:
                self.__maskLeftRect.width = self.__halfWidth

            if self.__maskRightRect.width < self.__halfWidth:
                self.__maskRightRect.width -= widthChange
            else:
                self.__maskRightRect.width = self.__halfWidth

            if self.__maskTopRect.height < self.__halfHeight:
                self.__maskTopRect.height -= heightChange
            else:
                self.__maskTopRect.height = self.__halfHeight

            if self.__maskBottomRect.height < self.__halfHeight:
                self.__maskBottomRect.height -= heightChange
            else:
                self.__maskBottomRect.height = self.__halfHeight

            # If masks are completely blocking container, animation is finished
            if self.__maskLeftRect.width == self.__halfWidth and \
                    self.__maskRightRect.width == self.__halfWidth and \
                    self.__maskTopRect.height == self.__halfHeight and \
                    self.__maskBottomRect.height == self.__halfHeight:
                self.__animation = [None, None, None]

                if self.__deleteAfter:
                    for widget in self.__widgets:
                        widget.delete()
                    self.delete()

    def closeSideAnimation(self):
        # Appears as two 'sliding doors'
        time = self.__animation[1]
        inOut = self.__animation[2]
        multiplier = self.__frameTime * 1 / time

        # This animation only deals with width, so no need to calculate
        # height change
        widthChange = self.__fullWidth * multiplier / 2

        # Set top and bottom masks to have a height of 0 - makes them
        # invisible, as they are not needed for this animation
        self.__maskTopRect.height = 0
        self.__maskBottomRect.height = 0

        if inOut == "in":
            # Very similar to the centre animation, except only using
            # maskLeft and maskRight
            if self.__maskLeftRect.width > 0:
                self.__maskLeftRect.width -= widthChange
            else:
                self.__maskLeftRect.width = 0

            if self.__maskRightRect.width > 0:
                self.__maskRightRect.width -= widthChange
            else:
                self.__maskRightRect.width = 0

            if self.__maskLeftRect.width == 0 and \
                    self.__maskRightRect.width == 0:
                self.__animation = [None, None, None]

                if self.__deleteAfter:
                    for widget in self.__widgets:
                        widget.delete()
                    self.delete()


        elif inOut == "out":
            # Again, very similar to the appearance animation, except invert
            # the width change value
            widthChange *= -1

            if self.__maskLeftRect.width < self.__halfWidth:
                self.__maskLeftRect.width -= widthChange
            else:
                self.__maskLeftRect.width = self.__halfWidth

            if self.__maskRightRect.width < self.__halfWidth:
                self.__maskRightRect.width -= widthChange
            else:
                self.__maskRightRect.width = self.__halfWidth

            if self.__maskLeftRect.width == self.__halfWidth and \
                    self.__maskRightRect.width == self.__halfWidth:
                self.__animation = [None, None, None]

                if self.__deleteAfter:
                    for widget in self.__widgets:
                        widget.delete()
                    self.delete()

    def closeUpAnimation(self):
        # Appears the same as slideSideAnimation, but flipped by 90 degrees
        time = self.__animation[1]
        inOut = self.__animation[2]
        multiplier = self.__frameTime * 1 / time

        # This one only deals with height, so no need to calculate widthChange
        heightChange = self.__fullHeight * multiplier

        # Set the width of the left mask and the right mask to 0, making them
        # invisible, as they are not needed for this animation
        self.__maskLeftRect.width = 0
        self.__maskRightRect.width = 0

        if inOut == "in":

            if self.__maskTopRect.height > 0:
                self.__maskTopRect.height -= heightChange
            else:
                self.__maskTopRect.height = 0

            if self.__maskBottomRect.height > 0:
                self.__maskBottomRect.height -= heightChange
            else:
                self.__maskBottomRect.height = 0

            if self.__maskTopRect.height == 0 and \
                    self.__maskBottomRect.height == 0:
                self.__animation = [None, None, None]

                if self.__deleteAfter:
                    for widget in self.__widgets:
                        widget.delete()
                    self.delete()


        elif inOut == "out":
            heightChange *= -1

            if self.__maskTopRect.height < self.__halfHeight:
                self.__maskTopRect.height -= heightChange
            else:
                self.__maskTopRect.height = self.__halfHeight

            if self.__maskBottomRect.height < self.__halfHeight:
                self.__maskBottomRect.height -= heightChange
            else:
                self.__maskBottomRect.height = self.__halfHeight

            if self.__maskTopRect.height == self.__halfHeight and \
                    self.__maskBottomRect.height == self.__halfHeight:
                self.__animation = [None, None, None]

                if self.__deleteAfter:
                    for widget in self.__widgets:
                        widget.delete()
                    self.delete()

    def horizontalSlideAnimation(self):
        # Whole container slides in from the left or right
        time = self.__animation[1]
        inOut = self.__animation[2]
        startFrom = self.__animation[3]
        destination = self.__animation[4]
        distance = destination - startFrom
        multiplier = self.__frameTime / time

        # Calculate how much the container should move this frame
        posStep = abs(distance * multiplier)

        if (inOut == "in" and destination < startFrom) or \
                (inOut == "out" and destination > startFrom):
            if inOut == "out":
                destination = startFrom
            if self.__rect.x > destination:
                # Step needs to be able to round to 1 (greater than 0.5)
                # otherwise container won't move at all
                if posStep > 0.5:
                    self.__rect.x -= posStep
                else:
                    self.__rect.x -= 1
            else:
                self.__rect.x = destination
                self.__animation = [None, None, None]

                if self.__deleteAfter:
                    for widget in self.__widgets:
                        widget.delete()
                    self.delete()


        elif (inOut == "in" and destination > startFrom) or \
                (inOut == "out" and destination < startFrom):
            if inOut == "out":
                destination = startFrom
            if self.__rect.x < destination:
                if posStep > 0.5:
                    self.__rect.x += posStep
                else:
                    self.__rect.x += 1
            else:
                self.__rect.x = destination
                self.__animation = [None, None, None]

                if self.__deleteAfter:
                    for widget in self.__widgets:
                        widget.delete()
                    self.delete()

    def verticalSlideAnimation(self):
        # Whole container slides in from the top/bottom
        time = self.__animation[1]
        inOut = self.__animation[2]
        startFrom = self.__animation[3]
        destination = self.__animation[5]
        distance = destination - startFrom
        multiplier = self.__frameTime / time

        # Calculate how much the container should move this frame
        posStep = abs(distance * multiplier)

        if (inOut == "in" and destination < startFrom) or \
                (inOut == "out" and destination > startFrom):
            if inOut == "out":
                destination = startFrom
            if self.__rect.y > destination:
                # Step needs to be able to round to 1 (greater than 0.5)
                # otherwise container won't move at all
                if posStep > 0.5:
                    self.__rect.y -= posStep
                else:
                    self.__rect.y -= 1
            else:
                self.__rect.y = destination
                self.__animation = [None, None, None]

                if self.__deleteAfter:
                    for widget in self.__widgets:
                        widget.delete()
                    self.delete()


        elif (inOut == "in" and destination > startFrom) or \
                (inOut == "out" and destination < startFrom):
            if inOut == "out":
                destination = startFrom
            if self.__rect.y < destination:
                if posStep > 0.5:
                    self.__rect.y += posStep
                else:
                    self.__rect.y += 1
            else:
                self.__rect.y = destination
                self.__animation = [None, None, None]

                if self.__deleteAfter:
                    for widget in self.__widgets:
                        widget.delete()
                    self.delete()

    def update(self):
        # Only draw outline rect if the outline thickness is greater than 0 -
        # no point otherwise, as it will be completely obscured by the
        # container rect
        if self.__outlineThickness > 0:
            pg.draw.rect(self.__screen, self.__outlineColour,
                         self.__outlineRect)
        if self.__bg:
            pg.draw.rect(self.__screen, self.__bgColour, self.__rect)

        # Widgets contained within the container need to be drawn here so
        # that they will be on top of the container, but below the masks
        for widget in self.__widgets:
            widget.draw()

        pg.draw.rect(self.__screen, self.__maskColour, self.__maskLeftRect)
        pg.draw.rect(self.__screen, self.__maskColour, self.__maskRightRect)
        pg.draw.rect(self.__screen, self.__maskColour, self.__maskTopRect)
        pg.draw.rect(self.__screen, self.__maskColour, self.__maskBottomRect)

        self.__frameTime = time.time() - self.__previousFrame
        self.__previousFrame = time.time()

        # All different animation types - only check if the container should
        # be playing an animation
        if self.__animation[0]:
            if self.__animation[0] == 'centre':
                self.centreAnimation()
            elif self.__animation[0] == 'closeside':
                self.closeSideAnimation()
            elif self.__animation[0] == 'closeup':
                self.closeUpAnimation()
            elif self.__animation[0] == 'horizontalslide':
                self.horizontalSlideAnimation()
            elif self.__animation[0] == 'verticalslide':
                self.verticalSlideAnimation()

        self.__maskLeftRect.topleft = self.__outlineRect.topleft
        self.__maskRightRect.topright = self.__outlineRect.topright
        self.__maskTopRect.topleft = self.__outlineRect.topleft
        self.__maskBottomRect.bottomleft = self.__outlineRect.bottomleft


# Will be used for dropdown menus (in cases where there are multiple options
# to select from)
class Dropdown(pg.sprite.Sprite):

    def __init__(self, parent, screen, x, y, options, font=None,
                 bgColour=None, inlineText=None, width=None,
                 container=None):
        super().__init__()
        self.__parent = parent
        self.__screen = screen
        self.__options = options

        # Need to save the original order of the options list, so that it
        # remains the same order when items are selected
        self.__originalOptions = options.copy()

        self.__currentOption = options[0]

        if font is None:
            self.__font = pg.font.SysFont("Helvetica", 30)
            self.__arrowFont = pg.font.SysFont("Helvetica", 20)
        else:
            self.__font = pg.font.SysFont(font[0], font[1])
            self.__arrowFont = pg.font.SysFont(font[0], int(font[1] * 2 / 3))

        if bgColour is None:
            self.__bgColour = (255, 255, 255)
        else:
            self.__bgColour = bgColour

        if inlineText is None:
            self.__inlineText = ""
        else:
            self.__inlineText = inlineText

        if width is None:
            self.__width = int(pg.display.get_surface().get_width() / 10)
        else:
            self.__width = width

        if container is None:
            self.__container = None
        else:
            self.__container = container
            self.__container.addWidget(self)

        if self.__parent.isLight(self.__bgColour):
            self.__textColour = (0, 0, 0)
        else:
            self.__textColour = (255, 255, 255)

        self.__hoverColour = self.__parent.hoverEffect(self.__bgColour)

        self.__inlineDisplayText = self.__font.render(self.__inlineText, True,
                                                      self.__textColour)

        # Scales height based on size of text
        self.__height = self.__inlineDisplayText.get_rect().h * 1.25

        # Using a dict for rendered text objects  - easier to retrieve when
        # needed than using indices in a list
        self.__optionDisplays = { }
        for i in self.__options:
            self.__optionDisplays[i] = self.__font.render(i, True,
                                                          self.__textColour)

        # Using a list for rects as there only needs to be 6 (current option
        # + 5 others)
        self.__rects = []
        for i in range(0, 5):
            self.__rects.append(pg.Rect(x, y + self.__height * i, self.__width,
                                        self.__height))

        self.__coords = (x, y)

        # Aligns text with input box
        self.__inlineTextRect = self.__inlineDisplayText.get_rect(
            center=(x - self.__inlineDisplayText.get_rect().w * 0.6,
                    y + 0.45 * self.__height))

        self.__sideArrow = self.__arrowFont.render(">", True, self.__textColour)
        self.__downArrow = pg.transform.rotate(self.__sideArrow, -90)
        self.__upArrow = pg.transform.rotate(self.__sideArrow, 90)

        bottomRight = self.__rects[0].bottomright
        self.__arrowRect = self.__upArrow.get_rect(bottomright=bottomRight)

        self.__expanded = False
        self.__hovered = False

        self.__hoverRect = self.__rects[0]

        # These are the indices for the range of items that will be displayed
        # when the dropdown is expanded
        self.__lower = 1
        self.__upper = 5

        index = 0
        inGroup = False
        for i in self.__parent.pgkGroup.sprites():
            if isinstance(i, Button):
                after = self.__parent.pgkGroup.sprites()[index:]
                for sprite in after:
                    self.__parent.pgkGroup.remove(sprite)
                self.__parent.pgkGroup.add(self)
                for sprite in after:
                    self.__parent.pgkGroup.add(sprite)
                inGroup = True
            index += 1

        if not inGroup:
            self.__parent.pgkGroup.add(self)

    def config(self, options=None, font=None, bgColour=None, textColour=None,
               inlineText=None, width=None, container=None):

        if options is None:
            pass
        else:
            self.__options = options
            # Need to save the original order of the options list, so that it
            # remains the same order when items are selected
            self.__originalOptions = options.copy()
            self.__currentOption = options[0]

            # Using a dict for rendered text objects  - easier to retrieve when
            # needed than using indices in a list
            self.__optionDisplays = { }
            for i in self.__options:
                self.__optionDisplays[i] = self.__font.render(i, True,
                                                              self.__textColour)

        if font is None:
            pass
        else:
            self.__font = pg.font.SysFont(font[0], font[1])

        if bgColour is None:
            pass
        else:
            self.__bgColour = bgColour

        if textColour is None:
            pass
        else:
            self.__textColour = textColour

        if inlineText is None:
            pass
        else:
            self.__inlineText = inlineText

        if width is None:
            pass
        else:
            self.__width = width

        if container is None:
            pass
        else:
            self.__container = container
            self.__container.addWidget(self)

        self.__inlineDisplayText = self.__font.render(self.__inlineText, True,
                                                      self.__textColour)

        # Scales height based on size of text
        self.__height = self.__inlineDisplayText.get_rect().h * 1.25

        x, y = self.__coords[0], self.__coords[1]

        # Aligns text with input box
        self.__inlineTextRect = self.__inlineDisplayText.get_rect(
            center=(x - self.__inlineDisplayText.get_rect().w * 0.6,
                    y + 0.45 * self.__height))

        self.__rect = pg.Rect(x, y, self.__width, self.__height)

    def delete(self):
        pg.mouse.set_cursor(*pg.cursors.arrow)
        self.__parent.pgkGroup.remove(self)

        if self.__container:
            self.__container.removeWidget(self)

        del self

    def draw(self):
        if self.__container and self.__coords != tuple(
                self.__container.getCorrectedCoords(self.__coords)):
            # Correct coordinates relative to container's topleft corner -
            # only if container has moved since last frame in order to save
            # performance
            x, y = self.__container.getCorrectedCoords(self.__coords)
            mult = 0
            for rect in self.__rects:
                rect.x = x
                rect.y = y + self.__height * mult
                mult += 1

            inlineTextWidth = self.__inlineDisplayText.get_rect().w
            self.__inlineTextRect.center = (x - inlineTextWidth * 0.6,
                                            y + 0.45 * self.__height)

            bottomRight = self.__rects[0].bottomright
            self.__arrowRect = self.__upArrow.get_rect(bottomright=bottomRight)

        pg.draw.rect(self.__screen, self.__bgColour, self.__rects[0])
        self.__screen.blit(self.__optionDisplays[self.__currentOption],
                           self.__rects[0])

        self.__screen.blit(self.__inlineDisplayText, self.__inlineTextRect)

        if self.__expanded:
            num = 1
            for i in self.__options[self.__lower:self.__upper]:
                # Draws the other 5 rects - and displays the text for the 5
                # shown options on top
                if self.__rects[num].center == self.__hoverRect.center and \
                        num != 0:
                    pg.draw.rect(self.__screen, self.__hoverColour,
                                 self.__rects[num])
                else:
                    pg.draw.rect(self.__screen, self.__bgColour,
                                 self.__rects[num])
                self.__screen.blit(self.__optionDisplays[i],
                                   self.__rects[num])
                num += 1

            self.__screen.blit(self.__upArrow, self.__arrowRect)

        else:
            self.__screen.blit(self.__downArrow, self.__arrowRect)

        if self.__hovered:
            pg.mouse.set_visible(False)
            # Draws custom mouse image over mouse location
            self.__pointerRect = self.__parent.pgkPointerCursor.get_rect(
                top=pg.mouse.get_pos()[1])
            self.__pointerRect.x = pg.mouse.get_pos()[
                                       0] - self.__pointerRect.w / 2
            self.__screen.blit(self.__parent.pgkPointerCursor,
                               self.__pointerRect)

    def get(self):
        return self.__currentOption

    def getHeight(self):
        return self.__height

    def setSelected(self, selected):
        self.__currentOption = selected

    def handleEvent(self, event):
        if event.type == MOUSEBUTTONUP:
            if event.button == 1:
                if self.__hovered and not self.__expanded:
                    self.__expanded = True
                    return True
                elif self.__hovered and self.__expanded:
                    # If user clicks on an option, then current option will
                    # be set to the option that is currently held within the
                    # rect that the user has clicked on
                    index = self.__rects.index(self.__hoverRect)
                    if index == 0:
                        self.__expanded = False
                        return True

                    try:
                        self.__currentOption = self.__options[self.__lower +
                                                              index - 1]
                    except IndexError:
                        # If an index error is thrown, then there aren't
                        # enough options in the dropdown menu to reach the
                        # mouse pointer. Therefore we return False as the
                        # event hasn't been handled
                        return False

                    # Returns option list back to its original order,
                    # and moves the selected option to the front of the list
                    # (so that it will be drawn in the first rect, and shown
                    # even when the dropdown is not expanded)
                    self.__options = self.__originalOptions.copy()
                    self.__options.remove(self.__currentOption)
                    self.__options.insert(0, self.__currentOption)
                    self.__expanded = False
                    return True
                elif not self.__hovered:
                    self.__expanded = False

        elif event.type == MOUSEBUTTONDOWN:
            if self.__expanded:
                if event.button == 4:
                    # Scroll wheel up
                    if self.__lower > 1:
                        self.__upper -= 1
                        self.__lower -= 1
                    return True
                elif event.button == 5:
                    # Scroll wheel down
                    if self.__upper < len(self.__options):
                        self.__upper += 1
                        self.__lower += 1
                    return True

    def update(self):
        if self.__rects[0].collidepoint(pg.mouse.get_pos()) and not \
                self.__hovered:
            # Can only be hovered over if dropdown is not obstructed by
            # container mask
            if (self.__container and not self.__container.mouseMasked()) or \
                    not self.__container:
                self.__hovered = True

        if self.__expanded:
            self.__hovered = False
            for rect in self.__rects:
                if rect.collidepoint(pg.mouse.get_pos()):
                    self.__hovered = True
                    self.__hoverRect = rect
            if not self.__hovered:
                pg.mouse.set_visible(True)

        elif not self.__rects[0].collidepoint(pg.mouse.get_pos()) and \
                self.__hovered and not self.__expanded:
            # Sets mouse cursor back to default
            pg.mouse.set_visible(True)
            self.__hovered = False

        # If dropdown is not in a container, it can be drawn normally
        if not self.__container:
            self.draw()


# noinspection PyArgumentList,PyArgumentList
class InputBox(pg.sprite.Sprite):

    def __init__(self, parent, screen, x, y, font=None, bgColour=None,
                 textColour=None, inlineText=None, width=None,
                 allowLetters=True, allowNumbers=True, allowMaths=True,
                 allowSpecial=True, allowSpace=True, charLimit=None,
                 defaultEntry=None, container=None, canUse=None):
        super().__init__()
        self.__parent = parent
        self.__screen = screen
        self.__outputText = ""
        self.__cursorText = ""
        self.__timer = 1
        self.__backspaceTimer = 1
        self.__backspaceFirstPress = False
        self.__backspaceDelay = 0.05
        self.__previousFrame = time.time()
        self.__hovered = False
        self.__active = False
        self.__caps = False

        self.__allowedChars = []

        try:
            x = int(x)
            y = int(y)
        except ValueError:
            raise Exception("InputBox coordinates must be integers")

        if not font:
            self.__font = pg.font.SysFont("Helvetica", 30)
        else:
            self.__font = pg.font.SysFont(font[0], font[1])

        if not bgColour:
            self.__bgColour = (255, 255, 255)
        else:
            self.__bgColour = bgColour

        if not textColour:
            self.__textColour = (0, 0, 0)
        else:
            self.__textColour = textColour

        if not inlineText:
            self.__inlineText = ""
        else:
            self.__inlineText = inlineText

        if not width:
            self.__width = int(pg.display.get_surface().get_width() / 10)
        else:
            self.__width = width

        # Acts as built-in input validation - only certain characters will be
        # allowed to be inputted
        # By default these attributes are set to True (in the arguments for
        # __init__), meaning they will be allowed.
        if allowLetters:
            self.__allowedChars += list(self.__parent.pgkLetterChars)

        if allowNumbers:
            self.__allowedChars += list(self.__parent.pgkNumberChars)

        if allowMaths:
            self.__allowedChars += list(self.__parent.pgkMathsChars)

        if allowSpecial:
            self.__allowedChars += list(self.__parent.pgkSpecialChars)

        if allowSpace:
            self.__allowedChars += [" "]

        if not charLimit:
            # By default, the character limit is set much higher than anybody
            # would realistically need - prevents errors when comparing to
            # string length
            self.__charLimit = 1000000
        else:
            self.__charLimit = charLimit

        if defaultEntry is None:
            self.__outputText = ""
        else:
            self.__outputText = defaultEntry

        self.__inlineDisplayText = self.__font.render(self.__inlineText, True,
                                                      self.__textColour)

        # Scales height based on size of text
        self.__height = self.__inlineDisplayText.get_rect().h * 1.25

        self.__coords = (x, y)

        # Aligns text with input box
        self.__inlineTextRect = self.__inlineDisplayText.get_rect(
            center=(x - self.__inlineDisplayText.get_rect().w * 0.6,
                    y + 0.45 * self.__height))

        self.__rect = pg.Rect(x, y, self.__width, self.__height)

        if self.__parent.isLight(self.__bgColour):
            self.__outputTextDisplay = self.__font.render(self.__outputText,
                                                          True, (0, 0, 0))
        else:
            self.__outputTextDisplay = self.__font.render(self.__outputText,
                                                          True, (255, 255, 255))

        if container is None:
            self.__container = None
        else:
            self.__container = container
            self.__container.addWidget(self)

        if canUse is None:
            self.__canUse = True
        else:
            self.__canUse = canUse

        index = 0
        inGroup = False
        for i in self.__parent.pgkGroup.sprites():
            if isinstance(i, Button):
                after = self.__parent.pgkGroup.sprites()[index:]
                for sprite in after:
                    self.__parent.pgkGroup.remove(sprite)
                self.__parent.pgkGroup.add(self)
                for sprite in after:
                    self.__parent.pgkGroup.add(sprite)
                inGroup = True
            index += 1

        if not inGroup:
            self.__parent.pgkGroup.add(self)

    def config(self, font=None, bgColour=None, textColour=None, inlineText=None,
               width=None, allowLetters=None, allowNumbers=None,
               allowSpecial=None, charLimit=None):

        # Same functionality as other config methods

        if not font:
            pass
        else:
            self.__font = pg.font.SysFont(font[0], font[1])

        if not bgColour:
            pass
        else:
            self.__bgColour = bgColour

        if not textColour:
            pass
        else:
            self.__textColour = textColour

        if not inlineText:
            pass
        else:
            self.__inlineText = inlineText

        if not width:
            pass
        else:
            self.__width = width
            self.__rect = pg.Rect(self.__rect.x, self.__rect.y, self.__width,
                                  self.__height)

        if allowLetters is None:
            pass
        else:
            self.__allowLetters = allowLetters

        if allowNumbers is None:
            pass
        else:
            self.__allowNumbers = allowNumbers

        if allowSpecial is None:
            pass
        else:
            self.__allowSpecial = allowSpecial

        if not charLimit:
            pass
        else:
            self.__charLimit = charLimit

        self.__inlineDisplayText = self.__font.render(self.__inlineText, True,
                                                      self.__textColour)
        self.__inlineTextRect = self.__inlineDisplayText.get_rect(
            center=(self.__rect.x - self.__inlineDisplayText.get_rect().w * 0.6,
                    self.__rect.y + 0.45 * self.__height))

    def delete(self):
        pg.mouse.set_cursor(*pg.cursors.arrow)
        self.__parent.pgkGroup.remove(self)

        if self.__container:
            self.__container.removeWidget(self)

        del self

    def draw(self):
        if self.__container:
            x, y = self.__container.getCorrectedCoords(self.__coords)
            # Aligns text with the checkbox
            self.__inlineTextRect = self.__inlineDisplayText.get_rect(
                center=(x - self.__inlineDisplayText.get_rect().w * 0.6,
                        y + 0.45 * self.__height))

            self.__rect = pg.Rect(x, y, self.__width, self.__height)

        pg.draw.rect(self.__screen, self.__bgColour, self.__rect)

        if self.__hovered:
            pg.mouse.set_visible(False)
            # Draws typing cursor on location of the mouse pointer
            typingRect = self.__parent.pgkTypingCursor.get_rect(
                center=pg.mouse.get_pos())
            self.__screen.blit(self.__parent.pgkTypingCursor, typingRect)

        self.__screen.blit(self.__outputTextDisplay, self.__rect)
        self.__screen.blit(self.__inlineDisplayText, self.__inlineTextRect)

    def get(self):
        try:
            if self.__outputText[-1] == "|":
                return self.__outputText[:-1]
            else:
                return self.__outputText
        except IndexError:
            return ""

    def getHeight(self):
        return self.__height

    def getWidth(self):
        return self.__width

    def getPos(self):
        return (self.__rect.x, self.__rect.y)

    def write(self, text):
        self.__outputText = text

    def update(self):
        if self.__active:
            # Backspace needs to be placed in the update loop as it uses an
            # updated method, which allows the user to hold it down to
            # delete long sections of text.
            keyPressed = pg.key.get_pressed()  # Dict of pressed keys
            if keyPressed[K_BACKSPACE] and self.__backspaceTimer >= \
                    self.__backspaceDelay:
                try:
                    self.__outputText = self.__outputText[:-1]

                except IndexError:
                    # In case there are no characters in output
                    pass
                self.__backspaceTimer = 0

                # Need a longer delay after first press - user won't
                # accidentally delete multiple characters
                if self.__backspaceFirstPress:
                    self.__backspaceDelay = 0.5
                    self.__backspaceFirstPress = False
                else:
                    self.__backspaceDelay = 0.05

        # Timer is used to add and remove the "|" character every 0.5
        # seconds, giving the appearance that the cursor is flashing when
        # typing -  acts as feedback that the inputBox is active.
        if self.__active and self.__timer > 0.5 and \
                self.__cursorText == "|":
            self.__cursorText = ""

        elif self.__active and self.__timer < 0.5 and \
                self.__cursorText != "|":
            self.__cursorText = "|"

        elif self.__timer > 1 and self.__cursorText != "|":
            self.__timer = 0

        # OutputTextDisplay needs to be rendered on every update due to the
        # fact that output can change
        if self.__parent.isLight(self.__bgColour):
            self.__outputTextDisplay = self.__font.render(self.__outputText +
                                                          self.__cursorText,
                                                          True, (0, 0, 0))
        else:
            self.__outputTextDisplay = self.__font.render(self.__outputText +
                                                          self.__cursorText,
                                                          True, (255, 255, 255))

        if self.__rect.collidepoint(pg.mouse.get_pos()) and not self.__hovered:
            # Can only be hovered over if checkbox is not obstructed by
            # container mask
            if (self.__container and not self.__container.mouseMasked()) or \
                    not self.__container:
                pg.mouse.set_visible(False)
                self.__hovered = True

        elif not self.__rect.collidepoint(
                pg.mouse.get_pos()) and self.__hovered:
            pg.mouse.set_visible(True)
            self.__hovered = False

        if not self.__container:
            self.draw()

        self.__timer += time.time() - self.__previousFrame
        self.__backspaceTimer += time.time() - self.__previousFrame
        self.__previousFrame = time.time()

    # noinspection SpellCheckingInspection
    def handleEvent(self, event):
        if event.type == MOUSEBUTTONUP:
            if event.button == 1:
                if self.__hovered and not self.__active and self.__canUse:
                    self.__active = True
                    self.__timer = 0
                    return True
                elif not self.__hovered and self.__active:
                    # Sets cursorText to an empty string - shows that box is
                    # not active
                    self.__cursorText = ""
                    self.__active = False

        # Will only check keydown events if checkbox is active
        if self.__active:
            if event.type == KEYUP:
                if event.key == K_BACKSPACE:
                    self.__backspaceDelay = 0.05
                    return True

            if event.type == KEYDOWN:
                if event.key == K_BACKSPACE:
                    self.__backspaceFirstPress = True

                elif event.unicode == "\x16":  # Unicode value for ctrl+v (
                    # paste)
                    text = []
                    try:
                        for i in paste():  # from pyClipTools
                            if i in self.__allowedChars:
                                pass
                            else:
                                text.append(i)
                        text = ''.join(text)

                    except TypeError:
                        text = ''

                    self.__outputText += text

                elif event.unicode in self.__allowedChars:
                    self.__outputText += event.unicode

                try:
                    if len(self.__outputText) > self.__charLimit:
                        self.__outputText = self.__outputText[:-1]
                    else:
                        pass

                except IndexError:
                    pass

                return True


class Label(pg.sprite.Sprite):
    def __init__(self, parent, screen, font=None, bgColour=None,
                 textColour=None, text=None, width=None, height=None,
                 container=None, topleft=None, topright=None, centre=None,
                 bottomleft=None, bottomright=None):
        super().__init__()
        self.__parent = parent
        self.__screen = screen

        if not font:
            self.__font = pg.font.SysFont("Helvetica", 30)
        else:
            self.__font = pg.font.SysFont(font[0], font[1])

        if not bgColour:
            self.__bgColour = None
        else:
            self.__bgColour = bgColour

        if not textColour:
            self.__textColour = (0, 0, 0)
        else:
            self.__textColour = textColour

        if not text:
            self.__text = ""
        else:
            # In case I need multi-line text (string will contain newline
            # character). Text gets broken up into a list of lines
            self.__text = [line for line in text.split('\n')]

        # Create list of rendered text surface objects
        self.__displayText = []
        for text in self.__text:
            self.__displayText.append(self.__font.render(text, True,
                                                         self.__textColour))

        if not width:
            self.__width = self.__displayText[0].get_rect().w * 1.25
        else:
            self.__width = width

        if not height:
            self.__height = self.__displayText[0].get_rect().h * 1.25
        else:
            self.__height = height

        self.__rect = pg.Rect(0, 0, self.__width, self.__height)

        if topleft is not None:
            self.__rect.topleft = (int(topleft[0]), int(topleft[1]))

        elif topright is not None:
            self.__rect.topright = (int(topright[0]), int(topright[1]))

        elif bottomleft is not None:
            self.__rect.bottomleft = (int(bottomleft[0]), int(bottomleft[1]))

        elif bottomright is not None:
            self.__rect.bottomright = (int(bottomright[0]), int(bottomright[1]))

        elif centre is not None:
            self.__rect.center = (int(centre[0]), int(centre[1]))

        # Positioning the text rects
        self.__textRects = []
        textGap = int(self.__displayText[0].get_rect().h * 1.25)
        num = 0

        for i in self.__displayText:
            self.__textRects.append(i.get_rect(centerx=(self.__rect.left +
                                                        self.__width / 2),
                                               top=(self.__rect.top +
                                                    textGap * num)))
            num += 1

        self.__coords = self.__rect.topleft

        if container is None:
            self.__container = None
        else:
            self.__container = container
            self.__container.addWidget(self)

        index = 0
        inGroup = False
        for i in self.__parent.pgkGroup.sprites():
            if isinstance(i, Button):
                after = self.__parent.pgkGroup.sprites()[index:]
                for sprite in after:
                    self.__parent.pgkGroup.remove(sprite)
                self.__parent.pgkGroup.add(self)
                for sprite in after:
                    self.__parent.pgkGroup.add(sprite)
                inGroup = True
            index += 1

        if not inGroup:
            self.__parent.pgkGroup.add(self)

    def config(self, font=None, bgColour=None, textColour=None, text=None,
               width=None, height=None):

        # Same functionality as other config methods

        if not font:
            pass
        else:
            self.__font = pg.font.SysFont(font[0], font[1])

        if not bgColour:
            pass
        else:
            self.__bgColour = bgColour

        if not textColour:
            pass
        else:
            self.__textColour = textColour

        if not text:
            pass
        else:
            self.__text = [line for line in text.split('\n')]

        self.__displayText = []
        for text in self.__text:
            self.__displayText.append(self.__font.render(text, True,
                                                         self.__textColour))

        if not width:
            pass
        else:
            self.__width = width

        if not height:
            pass
        else:
            self.__height = height

        self.__rect = pg.Rect(self.__rect.x, self.__rect.y, self.__width,
                              self.__height)

        self.__textRects = []
        textGap = int(self.__displayText[0].get_rect().h * 1.25)
        num = 0

        for i in self.__displayText:
            self.__textRects.append(i.get_rect(centerx=(self.__rect.left +
                                                        self.__width / 2),
                                               top=(self.__rect.top +
                                                    textGap * num)))
            num += 1

    def delete(self):
        pg.mouse.set_cursor(*pg.cursors.arrow)
        self.__parent.pgkGroup.remove(self)

        if self.__container:
            self.__container.removeWidget(self)

        del self

    def draw(self):
        if self.__container:
            x, y = self.__container.getCorrectedCoords(self.__coords)

            # Aligns text with the container
            self.__rect = pg.Rect(x, y, self.__width, self.__height)
            self.__textRects = []
            textGap = int(self.__displayText[0].get_rect().h * 1.25)
            num = 0

            for i in self.__displayText:
                self.__textRects.append(i.get_rect(centerx=(self.__rect.left +
                                                            self.__width / 2),
                                                   top=(self.__rect.top +
                                                        textGap * num)))
                num += 1

        if self.__bgColour is not None:
            pg.draw.rect(self.__screen, self.__bgColour, self.__rect)

        index = 0
        for i in self.__textRects:
            self.__screen.blit(self.__displayText[index], i)
            index += 1

    def update(self):
        pass

    def handleEvent(self, event):
        pass
