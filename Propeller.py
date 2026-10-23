import math
import FreeCAD
import FreeCADGui

import Part
import CurvedShapes
from FreeCAD import Vector, Rotation, Placement
from PySide.QtCore import QT_TRANSLATE_NOOP

# A three bladed propeller made with CurvedRailsArray. The leading and trailing edge of a blade are 3D curves,
# the twist of the blade follows from them. The blades run straight out to the tips: with Mode 2D
# the airfoils lie in planes perpendicular to the blade axis.

HUB_RADIUS = 15.0
TIP_RADIUS = 100.0
PITCH = 110.0
MAX_CHORD = 22.0
BLADES = 3


def naca4(m=0.04, p=0.4, t=0.12, n=40):
    """NACA 4 digit airfoil with chord 1: upper side from trailing to leading edge, lower side from leading to trailing edge"""
    upper = []
    lower = []
    for i in range(0, n + 1):
        x = (1 - math.cos(math.pi * i / n)) / 2
        yt = 5 * t * (0.2969 * math.sqrt(x) - 0.1260 * x - 0.3516 * x**2 + 0.2843 * x**3 - 0.1036 * x**4)
        if x < p:
            yc = m / p**2 * (2 * p * x - x * x)
            dyc = 2 * m / p**2 * (p - x)
        else:
            yc = m / (1 - p)**2 * ((1 - 2 * p) + 2 * p * x - x * x)
            dyc = 2 * m / (1 - p)**2 * (p - x)
        th = math.atan(dyc)
        upper.append(Vector(x - yt * math.sin(th), yc + yt * math.cos(th), 0))
        lower.append(Vector(x + yt * math.sin(th), yc - yt * math.cos(th), 0))

    upper.reverse()
    return upper, lower


def make_Airfoil_Sketch(doc, chord):
    sketch = doc.addObject('Sketcher::SketchObject', 'Airfoil')
    for points in naca4():
        bspline = Part.BSplineCurve()
        bspline.interpolate([p * chord for p in points])
        sketch.addGeometry(bspline)

    # at the hub: chord (sketch X) from leading to trailing edge along -Y, upper side (sketch Y) towards +Z
    sketch.Placement = Placement(Vector(HUB_RADIUS, 0, 0), Rotation(FreeCAD.Matrix(0, 0, -1, 0, -1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1)))
    sketch.ViewObject.Visibility = False
    return sketch


def make_Rails(doc, count=60):
    """Leading and trailing edge of a straight blade along the X axis, from the hub to the tip"""
    leading = []
    trailing = []
    for i in range(0, count + 1):
        f = i / count
        point = Vector(HUB_RADIUS + (TIP_RADIUS - HUB_RADIUS) * f, 0, 0)
        pitch_angle = math.atan(PITCH / (2 * math.pi * point.x))
        chord = MAX_CHORD * (0.7 + 0.9 * f * (1 - f)) * (1 - 0.6 * f**6)
        # chord direction from leading to trailing edge, in the plane perpendicular to the blade axis
        direction = Vector(0, -math.cos(pitch_angle), -math.sin(pitch_angle))
        leading.append(point - direction * (0.3 * chord))
        trailing.append(point + direction * (0.7 * chord))

    rails = []
    for name, points in (('LeadingEdge', leading), ('TrailingEdge', trailing)):
        bspline = Part.BSplineCurve()
        bspline.interpolate(points)
        rail = doc.addObject('Part::Spline', name)
        rail.Shape = bspline.toShape()
        rail.ViewObject.LineColor = (1.0, 0.0, 0.0, 0.0)
        rails.append(rail)

    return rails


def draw_Propeller():
    if FreeCAD.ActiveDocument is not None and FreeCAD.ActiveDocument.Name == "Propeller":
        FreeCAD.closeDocument(FreeCAD.ActiveDocument.Name)
        FreeCAD.setActiveDocument("")
        FreeCAD.ActiveDocument = None

    doc = FreeCAD.newDocument('Propeller')

    airfoil = make_Airfoil_Sketch(doc, MAX_CHORD)
    rails = make_Rails(doc)
    doc.recompute()

    blade = CurvedShapes.makeCurvedRailsArray(Base=airfoil, Rails=rails, Mode='2D', Items=24, Solid=True)
    blade.Label = 'Blade'

    for n in range(1, BLADES):
        link = doc.addObject('App::Link', 'Blade%d' % (n + 1))
        link.LinkedObject = blade
        link.Placement = Placement(Vector(0, 0, 0), Rotation(Vector(0, 0, 1), 360.0 * n / BLADES))

    hub = doc.addObject('Part::Cylinder', 'Hub')
    hub.Radius = HUB_RADIUS + 2
    hub.Height = 20
    hub.Placement = Placement(Vector(0, 0, -10), Rotation())

    doc.recompute()
    FreeCADGui.activeDocument().activeView().viewIsometric()
    FreeCADGui.SendMsgToActiveView("ViewFit")


class Propeller():
    def Activated(self):
        draw_Propeller()

    def GetResources(self):
        import os
        return {'Pixmap'  : os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "Propeller.svg"),
                'MenuText': QT_TRANSLATE_NOOP("Propeller", "Propeller"),
                'ToolTip' : QT_TRANSLATE_NOOP("Propeller", "Example propeller with twisted blades and straight tips, made with Curved Rails Array")}


FreeCADGui.addCommand('Propeller', Propeller())
