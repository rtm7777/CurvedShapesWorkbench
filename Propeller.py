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
# The blade has a thick airfoil at the hub and a thin one at the tip. Both sketches are placed in the blade where
# the rails touch them, the airfoils in between are blended.

HUB_RADIUS = 15.0
TIP_RADIUS = 100.0
PITCH = 110.0
MAX_CHORD = 22.0
BLADES = 3
ROOT_AIRFOIL = (0.04, 0.4, 0.15)    # NACA 4415
TIP_AIRFOIL = (0.02, 0.4, 0.09)     # NACA 2409


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


def blade_Station(radius):
    """Leading and trailing edge of the blade at the given radius"""
    f = (radius - HUB_RADIUS) / (TIP_RADIUS - HUB_RADIUS)
    point = Vector(radius, 0, 0)
    pitch_angle = math.atan(PITCH / (2 * math.pi * radius))
    chord = MAX_CHORD * (0.7 + 0.9 * f * (1 - f)) * (1 - 0.6 * f**6)
    # chord direction from leading to trailing edge, in the plane perpendicular to the blade axis
    direction = Vector(0, -math.cos(pitch_angle), -math.sin(pitch_angle))
    return point - direction * (0.3 * chord), point + direction * (0.7 * chord)


def make_Airfoil_Sketch(doc, name, airfoil, radius):
    """Airfoil sketch placed in the blade at the given radius: the rails touch its leading and trailing edge"""
    leading, trailing = blade_Station(radius)
    chord = (trailing - leading).Length
    sketch = doc.addObject('Sketcher::SketchObject', name)
    for points in naca4(*airfoil):
        bspline = Part.BSplineCurve()
        bspline.interpolate([p * chord for p in points])
        sketch.addGeometry(bspline)

    # sketch X from the leading to the trailing edge, sketch Y (upper side of the airfoil) roughly towards +Z,
    # the sketch plane perpendicular to the blade axis
    x = trailing - leading
    x.normalize()
    z = Vector(-1, 0, 0)
    y = z.cross(x)
    sketch.Placement = Placement(leading, Rotation(FreeCAD.Matrix(x.x, y.x, z.x, 0, x.y, y.y, z.y, 0, x.z, y.z, z.z, 0, 0, 0, 0, 1)))
    sketch.ViewObject.Visibility = False
    return sketch


def make_Rails(doc, count=60):
    """Leading and trailing edge of a straight blade along the X axis, from the hub to the tip"""
    leading = []
    trailing = []
    for i in range(0, count + 1):
        le, te = blade_Station(HUB_RADIUS + (TIP_RADIUS - HUB_RADIUS) * i / count)
        leading.append(le)
        trailing.append(te)

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

    root = make_Airfoil_Sketch(doc, 'RootAirfoil', ROOT_AIRFOIL, HUB_RADIUS)
    tip = make_Airfoil_Sketch(doc, 'TipAirfoil', TIP_AIRFOIL, TIP_RADIUS)
    rails = make_Rails(doc)
    doc.recompute()

    blade = CurvedShapes.makeCurvedRailsArray(Base=root, Profiles=[tip], Rails=rails, Mode='2D', Items=24, Solid=True)
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
                'ToolTip' : QT_TRANSLATE_NOOP("Propeller", "Example propeller with twisted blades and straight tips, made with Curved Rails Array. The airfoil is blended from a thick root to a thin tip profile")}


FreeCADGui.addCommand('Propeller', Propeller())
