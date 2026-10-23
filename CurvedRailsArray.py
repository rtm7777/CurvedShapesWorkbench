# -*- coding: utf-8 -*-
from PySide.QtCore import QT_TRANSLATE_NOOP

__title__ = "CurvedRailsArray"
__license__ = "LGPL 2.1"
__doc__ = QT_TRANSLATE_NOOP("CurvedRailsArray", "Creates an array of the Base profile stretched between two 3D rail curves (e.g. leading and trailing edge). The rails define position, size and twist of every item.")

import os
import FreeCAD
from FreeCAD import Vector
import Part
import CurvedShapes
if FreeCAD.GuiUp:
    import FreeCADGui


epsilon = CurvedShapes.epsilon
translate = FreeCAD.Qt.translate

class CurvedRailsArray:
    def __init__(self,
                 obj,
                 base=None,
                 rails=[],
                 mode='2D',
                 axis=Vector(0.0, 0.0, 0.0),
                 items=8,
                 Positions=[],
                 OffsetStart=0, OffsetEnd=0,
                 ScaleThickness=True,
                 SwapRails=False,
                 Surface=False,
                 Solid=False,
                 Distribution='linear',
                 DistributionReverse=False,
                 LoftMaxDegree=5,
                 MaxLoftSize=16,
                 KeepBase='None'):
        CurvedShapes.addObjectProperty(obj, "App::PropertyLink", "Base", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "The profile to make an array from")).Base = base
        CurvedShapes.addObjectProperty(obj, "App::PropertyLinkList", "Rails", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Two 3D curves the ends of the profile follow, e.g. leading and trailing edge")).Rails = rails
        CurvedShapes.addObjectProperty(obj, "App::PropertyEnumeration", "Mode", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "2D: items lie in planes perpendicular to Axis. 3D: items stay perpendicular to the rails and tilt where the rails bend"))
        CurvedShapes.addObjectProperty(obj, "App::PropertyVector", "Axis", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Direction of the array, the first item is at the negative end (computed automatically if 0,0,0)")).Axis = axis
        CurvedShapes.addObjectProperty(obj, "App::PropertyInteger", "Items", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Nr. of array items")).Items = items
        CurvedShapes.addObjectProperty(obj, "App::PropertyFloatList", "Positions", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Positions for ribs (as floats from 0.0 to 1.0) -- overrides Items")).Positions = Positions
        CurvedShapes.addObjectProperty(obj, "App::PropertyFloat", "OffsetStart", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Offset of the first item from the start of the rails (along Axis in 2D mode, along the rails in 3D mode)")).OffsetStart = OffsetStart
        CurvedShapes.addObjectProperty(obj, "App::PropertyFloat", "OffsetEnd", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Offset of the last item from the end of the rails (along Axis in 2D mode, along the rails in 3D mode)")).OffsetEnd = OffsetEnd
        CurvedShapes.addObjectProperty(obj, "App::PropertyBool", "ScaleThickness", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Scale the thickness of the profile together with its chord. If false, the profile keeps the thickness of Base")).ScaleThickness = ScaleThickness
        CurvedShapes.addObjectProperty(obj, "App::PropertyBool", "SwapRails", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Attach the other end of the profile chord to the first rail")).SwapRails = SwapRails
        CurvedShapes.addObjectProperty(obj, "App::PropertyEnumeration", "KeepBase", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Include the base shape unmodified and where"))
        CurvedShapes.addObjectProperty(obj, "App::PropertyBool", "Surface", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Make a surface")).Surface = Surface
        CurvedShapes.addObjectProperty(obj, "App::PropertyBool", "Solid", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Make a solid")).Solid = Solid
        CurvedShapes.addObjectProperty(obj, "App::PropertyEnumeration", "Distribution", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Algorithm for distance between elements"))
        CurvedShapes.addObjectProperty(obj, "App::PropertyBool", "DistributionReverse", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Reverses direction of Distribution algorithm")).DistributionReverse = DistributionReverse
        CurvedShapes.addObjectProperty(obj, "App::PropertyInteger", "LoftMaxDegree", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Max Degree for Surface or Solid")).LoftMaxDegree = LoftMaxDegree
        CurvedShapes.addObjectProperty(obj, "App::PropertyInteger", "MaxLoftSize", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Max Size of a Loft in Segments.")).MaxLoftSize = MaxLoftSize
        obj.Mode = ['2D', '3D']
        obj.Mode = mode
        obj.Distribution = ['linear', 'parabolic', 'x³', 'sinusoidal', 'asinusoidal', 'elliptic']
        obj.Distribution = Distribution
        obj.KeepBase = ['None', 'First', 'Last']
        obj.KeepBase = KeepBase
        obj.Proxy = self


    def execute(self, obj):
        if not obj.Base or not hasattr(obj.Base, "Shape") or len(obj.Base.Shape.Edges) == 0:
            return

        rails = getRails(obj.Rails)
        if not rails:
            return

        if obj.SwapRails:
            rails.reverse()

        base = obj.Base.Shape
        frame = profileFrame(base)
        if not frame:
            FreeCAD.Console.PrintError(translate("Curved Shapes", "CurvedRailsArray: cannot find the chord of the Base profile") + "\n")
            return

        axis = Vector(obj.Axis)
        if axis.Length < epsilon:
            axis = autoAxis(rails, frame[3], base.BoundBox.Center)
            obj.Axis = axis
        axis.normalize()

        fractions = self.fractions(obj)
        if obj.Mode == '3D':
            stations = self.stations3D(obj, rails, axis, fractions)
        else:
            stations = self.stations2D(obj, rails, axis, fractions)

        self.makeRibs(obj, base, frame, stations)


    def fractions(self, obj):
        if len(obj.Positions) > 0:
            return list(obj.Positions)

        items = int(obj.Items)
        if items < 2:
            return [0.0] * max(items, 0)

        return [CurvedShapes.distribute(x / (items - 1), obj.Distribution, obj.DistributionReverse) for x in range(0, items)]


    def stations2D(self, obj, rails, axis, fractions):
        """Stations in planes perpendicular to axis, where both rails exist. Returns [(P1, P2, normal)]"""
        ranges = [rail.projectionRange(axis) for rail in rails]
        t0 = max(r[0] for r in ranges) + obj.OffsetStart
        t1 = min(r[1] for r in ranges) - obj.OffsetEnd
        if t1 < t0:
            FreeCAD.Console.PrintError(translate("Curved Shapes", "CurvedRailsArray: the rails do not overlap in Axis direction") + "\n")
            return []

        planes = [t0 + f * (t1 - t0) for f in fractions]
        points = []
        for rail in rails:
            # follow the rail through the planes, if it crosses a plane more than once take the nearest point
            prev = rail.start if rail.start.dot(axis) <= rail.end.dot(axis) else rail.end
            railpoints = [None] * len(planes)
            for i in sorted(range(len(planes)), key=lambda i: planes[i]):
                hits = rail.intersectPlane(axis, planes[i])
                if hits:
                    hit = min(hits, key=lambda h: (h - prev).Length)
                    railpoints[i] = hit
                    prev = hit

            points.append(railpoints)

        stations = []
        for p1, p2 in zip(points[0], points[1]):
            if p1 is None or p2 is None:
                stations.append(None)
            else:
                stations.append((p1, p2, Vector(axis)))

        return stations


    def stations3D(self, obj, rails, axis, fractions):
        """Stations at the same relative length of both rails, perpendicular to the rails. Returns [(P1, P2, normal)]"""
        rail1, rail2 = rails
        if (rail1.start - rail2.start).Length + (rail1.end - rail2.end).Length > (rail1.start - rail2.end).Length + (rail1.end - rail2.start).Length:
            rail2.reverse()
        if ((rail1.end - rail1.start) + (rail2.end - rail2.start)).dot(axis) < 0:
            rail1.reverse()
            rail2.reverse()

        meanlength = (rail1.length + rail2.length) / 2
        s0 = obj.OffsetStart / meanlength
        s1 = 1.0 - obj.OffsetEnd / meanlength
        if s1 < s0:
            FreeCAD.Console.PrintError(translate("Curved Shapes", "CurvedRailsArray: OffsetStart and OffsetEnd are longer than the rails") + "\n")
            return []

        stations = []
        for f in fractions:
            s = s0 + f * (s1 - s0)
            p1, t1 = rail1.valueAtLength(s * rail1.length)
            p2, t2 = rail2.valueAtLength(s * rail2.length)
            stations.append((p1, p2, t1 + t2))

        return stations


    def makeRibs(self, obj, base, frame, stations):
        n0 = frame[3]
        valid = []
        for station in stations:
            if station is None:
                continue

            p1, p2, normal = station
            chord = p2 - p1
            if chord.Length < epsilon:
                continue

            chord.normalize()
            normal = normal - chord * normal.dot(chord)
            if normal.Length < epsilon:
                # rails running along the chord direction - use the axis instead
                normal = obj.Axis - chord * obj.Axis.dot(chord)
                if normal.Length < epsilon:
                    continue

            normal.normalize()
            valid.append((p1, p2, normal))

        if len(valid) < len(stations):
            FreeCAD.Console.PrintWarning(translate("Curved Shapes", "CurvedRailsArray: %d of %d items skipped, the rails are missing or touch each other there. Try OffsetStart / OffsetEnd.") % (len(stations) - len(valid), len(stations)) + "\n")

        if len(valid) == 0:
            return

        # keep the side of the profile that points in Base normal direction, decided where the items are most parallel to Base
        reference = max(valid, key=lambda st: abs(st[2].dot(n0)))
        if reference[2].dot(n0) < 0:
            valid = [(p1, p2, -normal) for p1, p2, normal in valid]

        ribs = [makeRib(base, frame, p1, p2, normal, obj.ScaleThickness) for p1, p2, normal in valid]

        if obj.KeepBase == 'First':
            ribs[0] = base.copy()
        elif obj.KeepBase == 'Last':
            ribs[-1] = base.copy()

        shape = None
        if (obj.Surface or obj.Solid) and len(ribs) > 1:
            shape = CurvedShapes.makeSurfaceSolid(ribs, obj.Solid, maxDegree=obj.LoftMaxDegree, maxLoftSize=obj.MaxLoftSize)
        if not shape:
            shape = Part.makeCompound(ribs)

        pl = obj.Placement
        obj.Shape = shape
        obj.Placement = pl


    def onChanged(self, fp, prop):
        if prop == "Positions" and hasattr(fp, "Items") and len(fp.Positions) != 0:
            if fp.Items != len(fp.Positions):
                fp.Items = len(fp.Positions)
            for p in fp.Positions:
                if p < 0.0 or p > 1.0:
                    FreeCAD.Console.PrintWarning(translate("Curved Shapes", "Some positions are out of bounds, should all be between 0.0 and 1.0, inclusive\n"))
                    break


    def dumps(self):
        return None


    def loads(self, state):
        return None


    def __getstate__(self):
        return None


    def __setstate__(self, state):
        return None


class Rail:
    """A chain of connected edges oriented from start to end. Can be evaluated by arc length and intersected with planes."""
    def __init__(self, edges):
        self.edges = []     # (edge, reversed)
        edges = [e for e in edges if e.Length > epsilon]
        end = None
        for edge in edges:
            a = edge.valueAt(edge.FirstParameter)
            b = edge.valueAt(edge.LastParameter)
            if end is None:
                reverse = False
                if len(edges) > 1:
                    nxt = [edges[1].valueAt(edges[1].FirstParameter), edges[1].valueAt(edges[1].LastParameter)]
                    reverse = min((a - p).Length for p in nxt) < min((b - p).Length for p in nxt)
            else:
                reverse = (b - end).Length < (a - end).Length

            self.edges.append((edge, reverse))
            end = a if reverse else b

        self.length = sum(edge.Length for edge, _ in self.edges)
        self.samples = None


    @property
    def start(self):
        edge, reverse = self.edges[0]
        return edge.valueAt(edge.LastParameter if reverse else edge.FirstParameter)


    @property
    def end(self):
        edge, reverse = self.edges[-1]
        return edge.valueAt(edge.FirstParameter if reverse else edge.LastParameter)


    def reverse(self):
        self.edges = [(edge, not reverse) for edge, reverse in reversed(self.edges)]
        if self.samples:
            self.samples.reverse()


    def valueAtLength(self, length):
        """Point and unit tangent in rail direction at the given arc length from the start"""
        length = min(max(length, 0.0), self.length)
        for n, (edge, reverse) in enumerate(self.edges):
            if length <= edge.Length or n == len(self.edges) - 1:
                if reverse:
                    length = edge.Length - length
                param = edge.getParameterByLength(min(max(length, 0.0), edge.Length))
                return edge.valueAt(param), edgeTangent(edge, param, reverse)

            length -= edge.Length


    def sample(self):
        """Points along every edge as [(params, points)], computed on first use"""
        if self.samples is None:
            self.samples = []
            for edge, _ in self.edges:
                if isinstance(edge.Curve, (Part.Line, Part.LineSegment)):
                    count = 1
                else:
                    count = 128
                params = [edge.FirstParameter + (edge.LastParameter - edge.FirstParameter) * i / count for i in range(0, count + 1)]
                self.samples.append((params, [edge.valueAt(p) for p in params]))

        return self.samples


    def projectionRange(self, axis):
        values = [p.dot(axis) for _, points in self.sample() for p in points]
        return min(values), max(values)


    def intersectPlane(self, axis, t):
        """All points of the rail on the plane {p | p.axis == t}"""
        tolerance = 1e-9 * (1 + self.length + abs(t))
        hits = []
        for (edge, _), (params, points) in zip(self.edges, self.sample()):
            values = [p.dot(axis) - t for p in points]
            for i in range(0, len(params)):
                if abs(values[i]) <= tolerance:
                    hits.append(points[i])
                elif i + 1 < len(params) and abs(values[i + 1]) > tolerance and (values[i] < 0) != (values[i + 1] < 0):
                    hits.append(edge.valueAt(bisectPlane(edge, axis, t, params[i], params[i + 1], values[i])))

        unique = []
        for h in hits:
            if all((h - u).Length > 1e-7 for u in unique):
                unique.append(h)

        return unique


def bisectPlane(edge, axis, t, a, b, fa):
    for _ in range(0, 64):
        m = (a + b) / 2
        fm = edge.valueAt(m).dot(axis) - t
        if fm == 0:
            return m
        if (fm < 0) == (fa < 0):
            a = m
            fa = fm
        else:
            b = m

    return (a + b) / 2


def edgeTangent(edge, param, reverse):
    """Unit tangent of the edge at param, pointing in rail direction"""
    h = (edge.LastParameter - edge.FirstParameter) * 1e-6
    secant = edge.valueAt(min(param + h, edge.LastParameter)) - edge.valueAt(max(param - h, edge.FirstParameter))
    try:
        tangent = Vector(edge.tangentAt(param))
        if tangent.dot(secant) < 0:
            tangent = -tangent
    except Exception:
        tangent = secant

    if tangent.Length > epsilon:
        tangent.normalize()
    if reverse:
        tangent = -tangent
    return tangent


def getRails(objects):
    """Two Rails: either from two objects or from one object containing two separate curves"""
    curves = []     # per object: list of connected pieces, each a list of edges
    for o in objects:
        if o is None or not hasattr(o, "Shape") or o.Shape.isNull() or len(o.Shape.Edges) == 0:
            continue

        pieces = [edges for edges in Part.sortEdges(o.Shape.Edges) if sum(e.Length for e in edges) > epsilon]
        if pieces:
            curves.append(pieces)

    if len(curves) == 1 and len(curves[0]) == 2:
        return [Rail(curves[0][0]), Rail(curves[0][1])]

    if len(curves) < 2:
        FreeCAD.Console.PrintError(translate("Curved Shapes", "CurvedRailsArray needs two rails: two curves, or one object containing two separate curves") + "\n")
        return None

    if len(curves) > 2:
        FreeCAD.Console.PrintWarning(translate("Curved Shapes", "CurvedRailsArray: more than two rails, only the first two are used") + "\n")

    rails = []
    for pieces in curves[0:2]:
        if len(pieces) > 1:
            FreeCAD.Console.PrintWarning(translate("Curved Shapes", "CurvedRailsArray: a rail consists of separate pieces, only the longest is used") + "\n")
        rails.append(Rail(max(pieces, key=lambda edges: sum(e.Length for e in edges))))

    return rails


def profilePoints(shape, count=1000):
    length = sum(e.Length for e in shape.Edges)
    if length < epsilon:
        return [v.Point for v in shape.Vertexes]

    points = []
    for e in shape.Edges:
        if e.Length > epsilon:
            points += e.discretize(Number=max(16, int(count * e.Length / length)))
        else:
            points += [v.Point for v in e.Vertexes]

    return points


def profileNormal(shape, points):
    """Normal of the plane the profile lies in, preferably the Z axis of its placement"""
    z = shape.Placement.Rotation.multVec(Vector(0, 0, 1))
    size = max(shape.BoundBox.DiagonalLength, epsilon)
    for tol in (-1, 1e-4 * size, 1e-2 * size):
        try:
            plane = shape.findPlane(tol)
        except Exception:
            plane = None

        if plane:
            normal = Vector(plane.Axis)
            normal.normalize()
            if abs(normal.dot(z)) > 1 - 1e-6:
                return z
            return normal

    # no plane - a straight line or not planar
    direction = max(points, key=lambda p: (p - points[0]).Length) - points[0]
    if direction.Length < epsilon:
        return z

    direction.normalize()
    if max((p - points[0]).cross(direction).Length for p in points) > 1e-6 * size:
        FreeCAD.Console.PrintWarning(translate("Curved Shapes", "CurvedRailsArray: the Base profile is not planar") + "\n")
        return z

    for candidate in (z, Vector(0, 0, 1), Vector(1, 0, 0), Vector(0, 1, 0)):
        normal = candidate - direction * candidate.dot(direction)
        if normal.Length > 0.5:
            normal.normalize()
            return normal

    return z


def extremePoint(points, direction, normal, tolerance):
    """The point farthest in direction. If the profile is flat there (e.g. blunt trailing edge), the middle of the flat part"""
    side = normal.cross(direction)
    depth = max(p.dot(direction) for p in points)
    near = [p for p in points if p.dot(direction) >= depth - tolerance]
    lateral = [p.dot(side) for p in near]
    height = sum(p.dot(normal) for p in near) / len(near)
    return direction * depth + side * ((min(lateral) + max(lateral)) / 2) + normal * height


def profileFrame(shape):
    """Chord of the profile: (leading point, chord direction u0, thickness direction v0, normal n0, chord length)"""
    points = profilePoints(shape)
    if len(points) < 2:
        return None

    normal = profileNormal(shape, points)
    size = max(shape.BoundBox.DiagonalLength, epsilon)
    tolerance = 1e-3 * size
    rot = shape.Placement.Rotation
    # start with the X axis of the profile (sketch horizontal) and iterate towards the longest extent
    for candidate in (rot.multVec(Vector(1, 0, 0)), rot.multVec(Vector(0, 1, 0)), Vector(1, 0, 0), Vector(0, 1, 0), Vector(0, 0, 1)):
        direction = candidate - normal * candidate.dot(normal)
        if direction.Length < 0.5:
            continue

        direction.normalize()
        chord = None
        for _ in range(0, 32):
            le = extremePoint(points, -direction, normal, tolerance)
            te = extremePoint(points, direction, normal, tolerance)
            chord = te - le
            chord = chord - normal * chord.dot(normal)
            if chord.Length < 1e-6 * size:
                break

            chord.normalize()
            converged = (chord - direction).Length < 1e-9
            direction = chord
            if converged:
                break

        if chord is None or chord.Length < 1e-6 * size:
            continue

        le = snapToProfile(shape, extremePoint(points, -direction, normal, tolerance), tolerance)
        te = snapToProfile(shape, extremePoint(points, direction, normal, tolerance), tolerance)
        chord = te - le
        chord = chord - normal * chord.dot(normal)
        length = chord.Length
        chord.normalize()
        return (le, chord, normal.cross(chord), normal, length)

    return None


def snapToProfile(shape, point, tolerance):
    """Move a point that is almost on the profile (e.g. the tip of a rounded nose) exactly onto it"""
    try:
        dist, pairs, _ = shape.distToShape(Part.Vertex(point))
        if dist < 2 * tolerance:
            return Vector(pairs[0][0])
    except Exception:
        pass

    return point


def autoAxis(rails, normal, basecenter):
    """The Base normal if the rails run roughly in that direction, else the mean direction of the rails.
    Oriented so that the array starts at the end of the rails next to Base."""
    d1 = rails[0].end - rails[0].start
    d2 = rails[1].end - rails[1].start
    if d1.dot(d2) < 0:
        d2 = -d2

    direction = d1 + d2
    if direction.Length < epsilon:
        axis = Vector(normal)
    else:
        direction.normalize()
        if abs(normal.dot(direction)) >= 0.5:
            axis = Vector(normal)
        else:
            axis = direction
            # rails roughly along a coordinate axis, e.g. a twisted blade along X
            for a in (Vector(1, 0, 0), Vector(0, 1, 0), Vector(0, 0, 1)):
                if abs(direction.dot(a)) > 0.985:
                    axis = a if direction.dot(a) > 0 else -a

    ends = [p.dot(axis) for rail in rails for p in (rail.start, rail.end)]
    b = basecenter.dot(axis)
    if abs(b - max(ends)) < abs(b - min(ends)):
        axis = -axis

    return axis


def makeRib(base, frame, p1, p2, normal, scaleThickness):
    """Copy of base with its chord mapped onto p1 -> p2, lying in the plane with the given normal"""
    le, u0, v0, n0, length = frame
    u = p2 - p1
    k = u.Length / length
    u.normalize()
    v = normal.cross(u)
    kt = k if scaleThickness else 1.0
    # X' = p1 + [u v normal] * diag(k, kt, k) * [u0 v0 n0]^T * (X - le)
    m = [[k * u[i] * u0[j] + kt * v[i] * v0[j] + k * normal[i] * n0[j] for j in range(0, 3)] for i in range(0, 3)]
    move = p1 - Vector(*[m[i][0] * le.x + m[i][1] * le.y + m[i][2] * le.z for i in range(0, 3)])
    matrix = FreeCAD.Matrix(m[0][0], m[0][1], m[0][2], move.x,
                            m[1][0], m[1][1], m[1][2], move.y,
                            m[2][0], m[2][1], m[2][2], move.z,
                            0, 0, 0, 1)
    if scaleThickness:
        # rotation and uniform scale keep circles and arcs
        rib = base.copy()
        rib.transformShape(matrix)
        return rib

    return base.transformGeometry(matrix)


class CurvedRailsArrayViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object


    def getIcon(self):
        return (os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "CurvedRailsArray.svg"))


    def attach(self, vobj):
        self.Object = vobj.Object
        self.onChanged(vobj, "Base")


    def claimChildren(self):
        return [o for o in [self.Object.Base] + self.Object.Rails if o]


    def onDelete(self, feature, subelements):
        return True


    def onChanged(self, fp, prop):
        pass


    def loads(self, state):
        return None


    def dumps(self):
        return None


    def __getstate__(self):
        return None


    def __setstate__(self, state):
        return None


if FreeCAD.GuiUp:
    class CurvedRailsArrayCommand():
        def Activated(self):
            FreeCADGui.doCommand("import CurvedShapes")

            selection = FreeCADGui.Selection.getSelectionEx()
            options = ""
            for n, sel in enumerate(selection):
                if n == 0:
                    options += "Base=base, "
                    FreeCADGui.doCommand("base = FreeCAD.ActiveDocument.getObject('%s')"%(sel.ObjectName))
                    FreeCADGui.doCommand("rails = []")
                    options += "Rails=rails, "
                else:
                    FreeCADGui.doCommand("rails.append(FreeCAD.ActiveDocument.getObject('%s'))"%(sel.ObjectName))

            FreeCADGui.doCommand("CurvedShapes.makeCurvedRailsArray(%sItems=8, Surface=False)"%(options))
            FreeCAD.ActiveDocument.recompute()


        def IsActive(self):
            return FreeCAD.ActiveDocument is not None


        def GetResources(self):
            return {'Pixmap'  : os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "CurvedRailsArray.svg"),
                    'Accel' : "", # a default shortcut (optional)
                    'MenuText': QT_TRANSLATE_NOOP("CurvedRailsArray", "Curved Rails Array"),
                    'ToolTip' : __doc__}


    FreeCADGui.addCommand('CurvedRailsArray', CurvedRailsArrayCommand())
