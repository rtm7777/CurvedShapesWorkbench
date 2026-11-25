# -*- coding: utf-8 -*-
from PySide.QtCore import QT_TRANSLATE_NOOP

__title__ = "CurvedRailsArray"
__license__ = "LGPL 2.1"
__doc__ = QT_TRANSLATE_NOOP("CurvedRailsArray", "Creates an array of a profile stretched between two 3D rail curves (e.g. leading and trailing edge). The rails define position, size and twist of every item. Select the profile first, then the two rails. Select several profiles (e.g. root and tip) to blend them along the rails.")

import os
import math
import FreeCAD
from FreeCAD import Vector
import Part
import CurvedShapes
if FreeCAD.GuiUp:
    import FreeCADGui


epsilon = CurvedShapes.epsilon
translate = FreeCAD.Qt.translate

# frame of a normalized profile: chord from (0,0,0) to (1,0,0), thickness in Y direction
UNIT_FRAME = (Vector(0, 0, 0), Vector(1, 0, 0), Vector(0, 1, 0), Vector(0, 0, 1), 1.0)


class ProfileError(Exception):
    pass


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
                 KeepBase='None',
                 Profiles=[],
                 ProfilePositions=[],
                 ProfileBlend='smooth',
                 InterpolationPoints=64):
        CurvedShapes.addObjectProperty(obj, "App::PropertyLink", "Base", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "The profile to make an array from. With further Profiles: the first profile")).Base = base
        CurvedShapes.addObjectProperty(obj, "App::PropertyLinkList", "Rails", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Two 3D curves the ends of the profile follow, e.g. leading and trailing edge")).Rails = rails
        CurvedShapes.addObjectProperty(obj, "App::PropertyEnumeration", "Mode", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "2D: items lie in planes perpendicular to Axis. 3D: items stay perpendicular to the rails and tilt where the rails bend"))
        CurvedShapes.addObjectProperty(obj, "App::PropertyVector", "Axis", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Direction of the array, the first item is at the negative end (computed automatically if 0,0,0)")).Axis = axis
        CurvedShapes.addObjectProperty(obj, "App::PropertyInteger", "Items", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Nr. of array items")).Items = items
        CurvedShapes.addObjectProperty(obj, "App::PropertyFloatList", "Positions", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Positions for ribs (as floats from 0.0 to 1.0) -- overrides Items")).Positions = Positions
        CurvedShapes.addObjectProperty(obj, "App::PropertyFloat", "OffsetStart", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Offset of the first item from the start of the rails (along Axis in 2D mode, along the rails in 3D mode)")).OffsetStart = OffsetStart
        CurvedShapes.addObjectProperty(obj, "App::PropertyFloat", "OffsetEnd", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Offset of the last item from the end of the rails (along Axis in 2D mode, along the rails in 3D mode)")).OffsetEnd = OffsetEnd
        CurvedShapes.addObjectProperty(obj, "App::PropertyBool", "ScaleThickness", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Scale the thickness of the profile together with its chord. If false, the profile keeps its thickness in mm (with several profiles: blended between their thicknesses)")).ScaleThickness = ScaleThickness
        CurvedShapes.addObjectProperty(obj, "App::PropertyBool", "SwapRails", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Attach the other end of the profile chord to the first rail. Not for profiles the rails touch, nor for profiles that follow a touched profile with a thick end or camber")).SwapRails = SwapRails
        CurvedShapes.addObjectProperty(obj, "App::PropertyEnumeration", "KeepBase", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Include a profile unmodified as the item at the start (First) or at the end (Last) of the rails: Base, or with several profiles the profile at that end"))
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
        self.addProfileProperties(obj)
        obj.Profiles = Profiles
        obj.ProfilePositions = ProfilePositions
        obj.ProfileBlend = ProfileBlend
        obj.InterpolationPoints = InterpolationPoints
        obj.Proxy = self


    def addProfileProperties(self, obj):
        """Properties for blending several profiles"""
        CurvedShapes.addObjectProperty(obj, "App::PropertyLinkList", "Profiles", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Further profiles, e.g. in the middle and at the tip. Each one applies where it is placed along the rails, the items in between are blended"), init_val=[])
        CurvedShapes.addObjectProperty(obj, "App::PropertyFloatList", "ProfilePositions", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Position of every profile: Base first, then Profiles, on the same scale as Positions (0.0 = start, 1.0 = end of the array). Empty: taken from where the profiles are placed, the Report view shows them"), init_val=[])
        CurvedShapes.addObjectProperty(obj, "App::PropertyEnumeration", "ProfileBlend", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "How the shape changes between more than two profiles: smooth curves through all profiles, or linear from one profile to the next"), init_val=['smooth', 'linear'])
        CurvedShapes.addObjectProperty(obj, "App::PropertyInteger", "InterpolationPoints", "CurvedRailsArray", QT_TRANSLATE_NOOP("App::Property", "Only for profiles that cannot be blended edge by edge (e.g. a circle and an airfoil): they are resampled with this number of points per side (at most 1000). More points follow the profiles more closely"), init_val=64)


    def execute(self, obj):
        profiles = profileObjects(obj)
        rails = getRails(obj.Rails) if profiles else None
        if not rails:
            clearShape(obj)
            return

        if obj.SwapRails:
            rails.reverse()

        base = profiles[0].Shape
        frame = profileFrame(base, profiles[0].Label)
        if not frame:
            FreeCAD.Console.PrintError(translate("Curved Shapes", "CurvedRailsArray: cannot find the chord of profile %s") % profiles[0].Label + "\n")
            clearShape(obj)
            return

        axis = Vector(obj.Axis)
        if axis.Length < epsilon:
            axis = autoAxis(rails, frame[3], base.BoundBox.Center)
            obj.Axis = axis
        axis.normalize()

        span = Span(obj, rails, axis)
        if not span.valid:
            clearShape(obj)
            return

        # from the start to the end of the rails, whatever the Distribution
        fractions = sorted(self.fractions(obj))
        items = []
        for fraction, station in zip(fractions, span.stations(fractions)):
            station = ribStation(station, axis)
            if station:
                items.append((fraction, station))

        if len(items) < len(fractions):
            FreeCAD.Console.PrintWarning(translate("Curved Shapes", "CurvedRailsArray: %d of %d items skipped, the rails are missing or touch each other there. Try OffsetStart / OffsetEnd.") % (len(fractions) - len(items), len(fractions)) + "\n")

        if len(items) == 0:
            clearShape(obj)
            return

        try:
            if len(profiles) == 1:
                ribs = makeRibs(profiles[0], frame, span, items, obj.ScaleThickness)
                first = last = base
            else:
                ribs, first, last = makeBlendedRibs(obj, profiles, span, items)
        except ProfileError as ex:
            FreeCAD.Console.PrintError(str(ex) + "\n")
            clearShape(obj)
            return

        if obj.KeepBase == 'First':
            ribs[0] = first.copy()
        elif obj.KeepBase == 'Last':
            ribs[-1] = last.copy()

        shape = None
        if (obj.Surface or obj.Solid) and len(ribs) > 1:
            shape = loftRibs(ribs, obj.Solid, obj.LoftMaxDegree, obj.MaxLoftSize)
        if not shape:
            shape = Part.makeCompound(ribs)

        pl = obj.Placement
        obj.Shape = shape
        obj.Placement = pl


    def fractions(self, obj):
        if len(obj.Positions) > 0:
            return list(obj.Positions)

        items = int(obj.Items)
        if items < 2:
            return [0.0] * max(items, 0)

        return [CurvedShapes.distribute(x / (items - 1), obj.Distribution, obj.DistributionReverse) for x in range(0, items)]


    def onChanged(self, fp, prop):
        if not hasattr(fp, 'InterpolationPoints'):
            self.addProfileProperties(fp) # backwards compatibility - this upgrades older documents

        if prop == "Positions" and hasattr(fp, "Items") and len(fp.Positions) != 0:
            if fp.Items != len(fp.Positions):
                fp.Items = len(fp.Positions)
            for p in fp.Positions:
                if p < 0.0 or p > 1.0:
                    FreeCAD.Console.PrintWarning(translate("Curved Shapes", "Some positions are out of bounds, should all be between 0.0 and 1.0, inclusive\n"))
                    break

        if prop == "ProfilePositions" and any(p < 0.0 or p > 1.0 for p in fp.ProfilePositions):
            FreeCAD.Console.PrintWarning(translate("Curved Shapes", "CurvedRailsArray: some ProfilePositions are out of bounds, should all be between 0.0 and 1.0, inclusive") + "\n")


    def dumps(self):
        return None


    def loads(self, state):
        return None


    def __getstate__(self):
        return None


    def __setstate__(self, state):
        return None


class Span:
    """The part of the rails the items are made on. Maps fractions (0.0 = first item, 1.0 = last item) to stations
    (P1, P2, normal) and points in space back to fractions."""
    def __init__(self, obj, rails, axis):
        self.rails = rails
        self.axis = axis
        self.mode = obj.Mode
        self.valid = False
        if self.mode == '3D':
            # stations at the same relative length of both rails, perpendicular to the rails
            rail1, rail2 = rails
            if (rail1.start - rail2.start).Length + (rail1.end - rail2.end).Length > (rail1.start - rail2.end).Length + (rail1.end - rail2.start).Length:
                rail2.reverse()
            if ((rail1.end - rail1.start) + (rail2.end - rail2.start)).dot(axis) < 0:
                rail1.reverse()
                rail2.reverse()

            meanlength = (rail1.length + rail2.length) / 2
            self.s0 = obj.OffsetStart / meanlength
            self.s1 = 1.0 - obj.OffsetEnd / meanlength
            if self.s1 < self.s0:
                FreeCAD.Console.PrintError(translate("Curved Shapes", "CurvedRailsArray: OffsetStart and OffsetEnd are longer than the rails") + "\n")
                return
        else:
            # stations in planes perpendicular to axis, where both rails exist
            ranges = [rail.projectionRange(axis) for rail in rails]
            self.t0 = max(r[0] for r in ranges) + obj.OffsetStart
            self.t1 = min(r[1] for r in ranges) - obj.OffsetEnd
            if self.t1 < self.t0:
                FreeCAD.Console.PrintError(translate("Curved Shapes", "CurvedRailsArray: the rails do not overlap in Axis direction") + "\n")
                return

        self.valid = True


    def stations(self, fractions):
        """[(P1, P2, normal)] for the fractions, None where the rails are missing"""
        if self.mode == '3D':
            return self.stations3D(fractions)
        return self.stations2D(fractions)


    def stations2D(self, fractions):
        axis = self.axis
        planes = [self.t0 + f * (self.t1 - self.t0) for f in fractions]
        points = []
        for rail in self.rails:
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


    def stations3D(self, fractions):
        rail1, rail2 = self.rails
        stations = []
        for f in fractions:
            s = self.s0 + f * (self.s1 - self.s0)
            p1, t1 = rail1.valueAtLength(s * rail1.length)
            p2, t2 = rail2.valueAtLength(s * rail2.length)
            stations.append((p1, p2, t1 + t2))

        return stations


    def locate(self, point, plane=None):
        """Fraction of the item next to point. In 3D mode a plane (origin, normal) through point refines it:
        for a profile at the rails, where the rails go through the plane of the profile."""
        if self.mode == '3D':
            rail1, rail2 = self.rails
            ends = lambda s: (rail1.pointAtLength(s * rail1.length), rail2.pointAtLength(s * rail2.length))
            def distance(s):
                p1, p2 = ends(s)
                return ((p1 + p2) * 0.5 - point).Length

            # the item whose middle between the rails is nearest to point
            count = 128
            values = [distance(i / count) for i in range(0, count + 1)]
            i = min(range(0, count + 1), key=lambda i: values[i])
            s = goldenMinimum(distance, max(i - 1, 0) / count, min(i + 1, count) / count)
            p1, p2 = ends(s)
            if plane and distance(s) < (p2 - p1).Length:
                origin, normal = plane
                def offset(s):
                    p1, p2 = ends(s)
                    return (p1 - origin).dot(normal) ** 2 + (p2 - origin).dot(normal) ** 2
                s = goldenMinimum(offset, max(s - 0.05, 0.0), min(s + 0.05, 1.0))

            if self.s1 - self.s0 < epsilon:
                return 0.0
            return (s - self.s0) / (self.s1 - self.s0)

        if self.t1 - self.t0 < epsilon:
            return 0.0
        return (point.dot(self.axis) - self.t0) / (self.t1 - self.t0)


def ribStation(station, axis):
    """The station with its normal perpendicular to the chord, None if no item can be made there"""
    if station is None:
        return None

    p1, p2, normal = station
    chord = p2 - p1
    if chord.Length < epsilon:
        return None

    chord.normalize()
    normal = normal - chord * normal.dot(chord)
    if normal.Length < epsilon:
        # rails running along the chord direction - use the axis instead
        normal = axis - chord * axis.dot(chord)
        if normal.Length < epsilon:
            return None

    normal.normalize()
    return (p1, p2, normal)


def clearShape(obj):
    """No result, e.g. after an error - so that no outdated shape stays"""
    if not obj.Shape.isNull():
        pl = obj.Placement
        obj.Shape = Part.Shape()
        obj.Placement = pl


def profileObjects(obj):
    """Base and the further profiles, all that have edges"""
    objects = [obj.Base] + list(getattr(obj, "Profiles", []))
    return [o for o in objects if o and o != obj and hasattr(o, "Shape") and not o.Shape.isNull() and len(o.Shape.Edges) > 0]


def makeRibs(profile, frame, span, items, scaleThickness):
    """One profile: copies of it mapped onto the stations"""
    _, station = profileStation(frame, span)
    frame = touchFrame(profile.Shape, station, span.mode == '2D') or baseFrame(frame, [station[2] for _, station in items])
    return [makeRib(profile.Shape, frame, p1, p2, normal, scaleThickness) for _, (p1, p2, normal) in items]


def profileStation(frame, span):
    """(position, station) of the item next to a profile. The position is limited to the array (0.0 to 1.0),
    the station is where the profile is, also beyond the ends of the array if the rails go on there"""
    le, u0, _, n0, length = frame
    located = span.locate(le + u0 * (length / 2), (le, n0))
    position = min(max(located, 0.0), 1.0)
    station = ribStation(span.stations([located])[0], span.axis) if located != position else None
    return position, station or ribStation(span.stations([position])[0], span.axis)


def makeBlendedRibs(obj, profiles, span, items):
    """Several profiles: every item gets a shape blended from the profiles next to it.
    Returns the ribs and the profiles at the first and the last position"""
    frames = []
    for o in profiles:
        frame = profileFrame(o.Shape, o.Label)
        if not frame:
            raise ProfileError(translate("Curved Shapes", "CurvedRailsArray: cannot find the chord of profile %s") % o.Label)
        frames.append(frame)

    positions, sources, stations = profilePositions(obj, profiles, frames, span)
    normals = [station[2] for _, station in items]
    planar = span.mode == '2D'
    sections = []
    for o, frame, position, source, station in zip(profiles, frames, positions, sources, stations):
        here = ribStation(span.stations([position])[0], span.axis)
        touch = touchFrame(o.Shape, station or here, planar)
        section = Section(o, position, source, touch or baseFrame(frame, normals), touch is not None)
        # touched beyond the end of the array: the item at the end gets its shape, but is not at the profile
        section.beyond = touch is not None and touchFrame(o.Shape, here, planar) is None
        sections.append(section)

    orientSections(sections)
    ordered = sorted(sections, key=lambda section: section.position)
    try:
        blend = ShapeBlend([s.shape for s in ordered], [s.frame for s in ordered], [s.position for s in ordered], [s.label for s in ordered],
                           obj.ScaleThickness, obj.ProfileBlend == 'smooth', obj.InterpolationPoints)
        reportProfiles(obj, sections, blend)
        ribs = []
        for f, (p1, p2, normal) in items:
            shape, frame = blend.shapeAt(f)
            ribs.append(makeRib(shape, frame, p1, p2, normal, obj.ScaleThickness))
    except Part.OCCError as ex:
        raise ProfileError(translate("Curved Shapes", "CurvedRailsArray: the profiles cannot be blended (%s)") % str(ex).strip())

    return ribs, ordered[0].shape, ordered[-1].shape


class Section:
    """A profile, where it applies along the rails and how it is mapped onto them"""
    def __init__(self, obj, position, source, frame, touching):
        self.label = obj.Label
        self.shape = obj.Shape
        self.position = position
        self.source = source            # how the position was found: 'placed', 'order', 'gap' or 'explicit'
        self.frame = frame
        self.touching = touching        # the rails touch the profile, it is used exactly as it is placed
        self.beyond = False             # ... but beyond the end of the array
        self.centre = None


    def centroid(self):
        if self.centre is None:
            self.centre = profileCentre(self.shape, self.frame)
        return self.centre


    def match(self, others):
        """Turn the profile so that its thick end and its camber are on the same side as those of the other profiles:
        for each, the nearest one that has it (others: nearest first) - a circle, for example, has neither"""
        c = self.centroid()
        rx = next((r.centroid() for r in others if abs(r.centroid().x - 0.5) > 0.01), None)
        ry = next((r.centroid() for r in others if abs(r.centroid().y) > 0.002), None)
        flipx = rx is not None and abs(c.x - 0.5) > 0.01 and (c.x - 0.5) * (rx.x - 0.5) < 0
        flipy = ry is not None and abs(c.y) > 0.002 and c.y * ry.y < 0
        if not (flipx or flipy):
            return

        le, u0, _, n0, length = self.frame
        if flipx:
            # mirrored along the chord
            le = le + u0 * length
            u0 = -u0
            n0 = -n0
        if flipy:
            # mirrored across the chord
            n0 = -n0

        self.frame = (le, u0, n0.cross(u0), n0, length)
        self.centre = None


def orientSections(sections):
    """The profiles the rails touch keep their orientation, without such profiles Base keeps the orientation of a single profile.
    All other profiles, beginning with the nearest, are turned like the profiles already oriented."""
    done = [s for s in sections if s.touching] or [sections[0]]
    todo = [s for s in sections if s not in done]
    while todo:
        section = min(todo, key=lambda s: min(abs(s.position - d.position) for d in done))
        section.match(sorted(done, key=lambda d: abs(d.position - section.position)))
        todo.remove(section)
        done.append(section)


def reportProfiles(obj, sections, blend):
    """Tells in the Report view where every profile applies and how it is used - once, not on every recompute"""
    sources = {'placed': translate("Curved Shapes", "placed at the rails"),
               'order': translate("Curved Shapes", "spaced evenly in the order of Base and Profiles"),
               'gap': translate("Curved Shapes", "not placed at the rails, put into the largest gap"),
               'explicit': translate("Curved Shapes", "from ProfilePositions")}
    usages = {'touched': translate("Curved Shapes", "touched by the rails: used exactly as placed"),
              'beyond': translate("Curved Shapes", "touched by the rails beyond the end of the array: the item at the end gets its shape"),
              'shape': translate("Curved Shapes", "only its shape is used")}
    lines = [translate("Curved Shapes", "CurvedRailsArray: profiles of %s (in the order of ProfilePositions: Base, Profiles)") % obj.Label]
    for s in sections:
        usage = 'beyond' if s.beyond else ('touched' if s.touching else 'shape')
        lines.append(translate("Curved Shapes", "%s at %.3f: %s; %s") % (s.label, s.position, sources[s.source], usages[usage]))
    if blend.exact:
        lines.append(translate("Curved Shapes", "The profiles are blended edge by edge."))
    else:
        lines.append(translate("Curved Shapes", "The profiles are resampled with %d points per side (InterpolationPoints).") % blend.points)

    text = "\n    ".join(lines)
    if getattr(obj.Proxy, "report", None) != text:
        obj.Proxy.report = text
        FreeCAD.Console.PrintMessage(text + "\n")


def profilePositions(obj, profiles, frames, span):
    """Where every profile applies (0.0 = first item, 1.0 = last item), how that was found (ProfilePositions,
    where the profile is placed at the rails, or the order of the profiles) and the station where a placed profile is"""
    count = len(frames)
    positions = list(obj.ProfilePositions)
    stations = [None] * count
    if positions and len(positions) != count:
        FreeCAD.Console.PrintWarning(translate("Curved Shapes", "CurvedRailsArray: ProfilePositions needs %d values (Base and Profiles) but has %d, it is ignored") % (count, len(positions)) + "\n")
        positions = []

    if positions:
        positions = [min(max(p, 0.0), 1.0) for p in positions]
        sources = ['explicit'] * count
        hint = translate("Curved Shapes", "Give them different values in ProfilePositions.")
    else:
        located = [placedPosition(o.Shape, frame, span) for o, frame in zip(profiles, frames)]
        positions, homeless = fillPositions([p[0] if p else None for p in located])
        sources = ['placed' if p else ('gap' if i in homeless else 'order') for i, p in enumerate(located)]
        stations = [p[1] if p else None for p in located]
        hint = translate("Curved Shapes", "Place them at different positions along the rails or set ProfilePositions.")

    same = [o.Label for i, o in enumerate(profiles) if any(i != j and abs(positions[i] - positions[j]) < 1e-6 for j in range(0, count))]
    if same:
        FreeCAD.Console.PrintWarning(translate("Curved Shapes", "CurvedRailsArray: %s share a position with another profile, all profiles are spaced evenly in the order of Base and Profiles instead.") % ", ".join(same) + " " + hint + "\n")
        positions = [i / (count - 1) for i in range(0, count)]
        sources = ['order'] * count
        stations = [None] * count

    return positions, sources, stations


def placedPosition(shape, frame, span):
    """(position, station) of a profile placed at the rails, None if it is not placed there (e.g. a sketch left at the origin)"""
    position, station = profileStation(frame, span)
    if station is None:
        return None

    if touchFrame(shape, station, False):
        return position, station

    # across the rails and next to them
    le, u0, _, n0, length = frame
    p1, p2, normal = station
    if abs(n0.dot(normal)) < 0.3 or (le + u0 * (length / 2) - (p1 + p2) * 0.5).Length > (p2 - p1).Length:
        return None

    return position, station


def fillPositions(located):
    """Positions for the profiles that are not placed at the rails (None): spaced evenly in list order between the placed ones.
    Returns the positions and the profiles that had no room there and went into the largest gap"""
    count = len(located)
    known = [i for i, p in enumerate(located) if p is not None]
    if not known:
        return [i / (count - 1) for i in range(0, count)], []

    positions = list(located)
    first = known[0]
    for i in range(0, first):
        positions[i] = located[first] * i / first

    last = known[-1]
    for i in range(last + 1, count):
        positions[i] = located[last] + (1.0 - located[last]) * (i - last) / (count - 1 - last)

    for a, b in zip(known, known[1:]):
        for i in range(a + 1, b):
            positions[i] = located[a] + (located[b] - located[a]) * (i - a) / (b - a)

    # no room between the neighbours (e.g. a profile added after the one at the tip): into the largest gap instead
    homeless = [i for i in range(0, count) if located[i] is None and any(j != i and abs(positions[i] - positions[j]) < 1e-6 for j in range(0, count))]
    if homeless:
        taken = sorted(set([0.0, 1.0] + [positions[i] for i in range(0, count) if i not in homeless]))
        a, b = max(zip(taken, taken[1:]), key=lambda gap: gap[1] - gap[0])
        for k, i in enumerate(homeless):
            positions[i] = a + (b - a) * (k + 1) / (len(homeless) + 1)

    return positions, homeless


def touchFrame(shape, station, planar):
    """If both rails touch the profile at the station: the frame along the chord between the rails, so that the item
    there is exactly the profile as it is placed. Else None. Planar (2D mode): the profile must also lie in the plane
    of the item, a tilted one would tilt all items"""
    if station is None:
        return None

    p1, p2, normal = station
    chord = p2 - p1
    tolerance = 1e-5 * chord.Length
    if not (touches(shape, p1, tolerance) and touches(shape, p2, tolerance)):
        return None

    if planar and any(abs((p - p1).dot(normal)) > tolerance for p in profilePoints(shape, 200)):
        return None

    chord.normalize()
    return (p1, chord, normal.cross(chord), normal, (p2 - p1).Length)


def touches(shape, point, tolerance):
    """The point lies on the outline of the profile (for a face: not just somewhere inside it)"""
    try:
        return Part.Compound(shape.Edges).distToShape(Part.Vertex(point))[0] <= tolerance
    except Exception:
        return False


def baseFrame(frame, normals):
    """The frame of a profile as a single Base uses it: the side of the profile that points in its normal direction
    stays on that side, decided where the items are most parallel to the profile"""
    le, u0, _, n0, length = frame
    reference = max(normals, key=lambda normal: abs(normal.dot(n0)))
    if reference.dot(n0) < 0:
        n0 = -n0

    return (le, u0, n0.cross(u0), n0, length)


def profileCentre(shape, frame):
    """Centre of the area of a closed profile (else of its curve) relative to its frame - tells the thick end and the camber side"""
    faces = shape.Faces
    if not faces:
        closed = [w for w in shape.Wires if w.isClosed()]
        if closed:
            try:
                faces = Part.makeFace(closed, "Part::FaceMakerBullseye").Faces
            except Exception:
                faces = []

    area = sum(f.Area for f in faces)
    if area > epsilon:
        centre = Vector()
        for f in faces:
            centre += f.CenterOfMass * (f.Area / area)
    else:
        points = profilePoints(shape)
        centre = Vector()
        for p in points:
            centre += p * (1.0 / len(points))

    return normalizer(frame)(centre)


class ShapeBlend:
    """Blends profiles of different shape. Every profile is reduced to its shape: the chord runs from (0,0,0) to (1,0,0),
    the thickness lies in Y direction (in mm if the thickness does not scale with the chord)."""
    def __init__(self, shapes, frames, positions, labels, scaleThickness, smooth, points):
        shapes = [closedProfile(shape) for shape in shapes]
        normalizers = [normalizer(frame) for frame in frames]
        heights = [1.0 if scaleThickness else frame[4] for frame in frames]
        curves = [exactCurves(shape, normalize) for shape, normalize in zip(shapes, normalizers)]
        self.exact = sameStructure(curves)
        self.points = min(max(int(points), 4), 1000)
        if self.exact:
            # same edges in all profiles (e.g. copies of one sketch with other dimensions): blend the poles, exact
            self.curves = curves[0]
            values = [flattenPoints([p for c in profile for p in c['poles']], height) + [w for c in profile for w in c['weights']] for profile, height in zip(curves, heights)]
            self.build = self.buildExact
        else:
            # resample every profile with the same number of points, from the leading to the trailing edge
            points = self.points
            self.params = [(1 - math.cos(math.pi * i / (points - 1))) / 2 for i in range(0, points)]
            sides = [sampleSides(shape, normalize, self.params, label) for shape, normalize, label in zip(shapes, normalizers, labels)]
            if len(set(len(s) for s in sides)) > 1:
                closed = ", ".join(label for label, s in zip(labels, sides) if len(s) == 2)
                opened = ", ".join(label for label, s in zip(labels, sides) if len(s) == 1)
                raise ProfileError(translate("Curved Shapes", "CurvedRailsArray: open and closed profiles cannot be blended (closed: %s; open: %s)") % (closed, opened))
            self.sides = len(sides[0])
            values = [flattenPoints([p for side in s for p in side], height) for s, height in zip(sides, heights)]
            self.build = self.buildSampled

        self.blend = Blend(positions, values, smooth)


    def shapeAt(self, fraction):
        """(blended profile, its frame) at the fraction"""
        return self.build(self.blend.at(fraction))


    def buildExact(self, values):
        count = sum(len(c['poles']) for c in self.curves)
        weights = values[3 * count:]
        edges = []
        i = 0
        for c in self.curves:
            n = len(c['poles'])
            bspline = Part.BSplineCurve()
            bspline.buildFromPolesMultsKnots(unflattenPoints(values, 3 * i, n), c['mults'], c['knots'], c['periodic'], c['degree'], weights[i:i + n], c['rational'])
            edges.append(bspline.toShape())
            i += n

        # blended poles move the leading and trailing edge a bit, attach the points next to them to the rails
        shape = profileWires(edges)
        return shape, attachFrame(shape)


    def buildSampled(self, values):
        edges = []
        n = len(self.params)
        for s in range(0, self.sides):
            bspline = Part.BSplineCurve()
            # points next to the leading and trailing edge are very close together on a chord of 1
            bspline.interpolate(Points=unflattenPoints(values, 3 * n * s, n), Parameters=self.params, Tolerance=1e-9)
            edges.append(bspline.toShape())

        return profileWires(edges), UNIT_FRAME


def normalizer(frame):
    """Function mapping a point of the profile to coordinates relative to its chord"""
    le, u0, v0, n0, length = frame
    def normalize(point):
        d = Vector(point) - le
        return Vector(d.dot(u0) / length, d.dot(v0) / length, d.dot(n0) / length)
    return normalize


def attachFrame(shape):
    """Frame of a normalized profile through its points next to (0,0,0) and (1,0,0)"""
    try:
        q0 = Vector(shape.distToShape(Part.Vertex(Vector(0, 0, 0)))[1][0][0])
        q1 = Vector(shape.distToShape(Part.Vertex(Vector(1, 0, 0)))[1][0][0])
    except Exception:
        return UNIT_FRAME

    chord = q1 - q0
    chord.z = 0
    if chord.Length < 0.5:
        return UNIT_FRAME

    length = chord.Length
    chord.normalize()
    return (q0, chord, Vector(0, 0, 1).cross(chord), Vector(0, 0, 1), length)


def exactCurves(shape, normalize):
    """The edges of shape as B-splines in normalized coordinates (circles and arcs exact, as rational B-splines), None if that is not possible"""
    try:
        edges = shape.toNurbs().Edges
    except Exception:
        return None

    if len(edges) != len(shape.Edges):
        return None

    curves = []
    for edge in edges:
        try:
            bspline = edge.Curve.toBSpline(edge.FirstParameter, edge.LastParameter)
        except Exception:
            return None

        knots = bspline.getKnots()
        width = knots[-1] - knots[0]
        if width < epsilon:
            return None

        curves.append({'degree': bspline.Degree,
                       'periodic': bspline.isPeriodic(),
                       'rational': bspline.isRational(),
                       'mults': list(bspline.getMultiplicities()),
                       'knots': [(k - knots[0]) / width for k in knots],
                       'poles': [normalize(p) for p in bspline.getPoles()],
                       'weights': list(bspline.getWeights()),
                       'points': [normalize(p) for p in edge.discretize(Number=17)]})

    return curves


def sameStructure(profiles):
    """True if all profiles consist of the same kind of B-splines at the same places, so their poles can be blended"""
    if any(curves is None for curves in profiles):
        return False

    first = profiles[0]
    turn = turning(first)
    for curves in profiles[1:]:
        if len(curves) != len(first):
            return False

        # a profile turned over runs the other way round
        other = turning(curves)
        if turn * other < 0 and min(abs(turn), abs(other)) > 1e-3:
            return False

        for a, b in zip(first, curves):
            if any(a[key] != b[key] for key in ('degree', 'periodic', 'rational', 'mults')) or len(a['poles']) != len(b['poles']):
                return False
            if any(abs(x - y) > 1e-9 for x, y in zip(a['knots'], b['knots'])):
                return False
            # the edges must be in the same order, run in the same direction and lie on the same side of the chord
            if any((a['points'][i] - b['points'][i]).Length > 0.5 for i in (0, -1)):
                return False
            m, n = a['points'][8], b['points'][8]
            if m.y * n.y < 0 and min(abs(m.y), abs(n.y)) > 0.02:
                return False

    return True


def turning(curves):
    """Signed area swept by the edges in their direction"""
    return sum(p.x * q.y - q.x * p.y for c in curves for p, q in zip(c['points'], c['points'][1:]))


def flattenPoints(points, height):
    """x, y * height and z of all points in one list"""
    values = []
    for p in points:
        values += [p.x, p.y * height, p.z]

    return values


def unflattenPoints(values, start, count):
    """count points from a list made by flattenPoints, beginning at index start"""
    return [Vector(*values[start + 3 * k:start + 3 * k + 3]) for k in range(0, count)]


def closedProfile(shape):
    """The profile with a small gap (e.g. an open trailing edge) closed by a straight line, else unchanged"""
    chains = edgeChains(shape)
    if len(chains) != 1:
        return shape

    chain = Rail(chains[0])
    gap = (chain.start - chain.end).Length
    if gap <= 1e-4 * chain.length or gap > 0.02 * chain.length:
        return shape

    try:
        return Part.Wire(chains[0] + [Part.LineSegment(chain.end, chain.start).toShape()])
    except Exception:
        return shape


def sampleSides(shape, normalize, params, label):
    """Points of a profile in normalized coordinates at the relative lengths params (0.0 to 1.0).
    Closed profile: [upper side, lower side], both from the leading to the trailing edge.
    Open profile: [the curve, from the end next to the leading edge]"""
    chains = edgeChains(shape)
    if len(chains) != 1:
        raise ProfileError(translate("Curved Shapes", "CurvedRailsArray: profile %s has %d separate curves (e.g. a hole). Profiles with holes can only be blended if all profiles have the same edges, e.g. copies of one sketch") % (label, len(chains)))

    chain = Rail(chains[0])
    length = chain.length
    gap = (chain.start - chain.end).Length
    if gap > 0.02 * length:
        # open, e.g. a thin curved plate
        forward = normalize(chain.start).x <= normalize(chain.end).x
        return [[normalize(chain.pointAtLength((p if forward else 1.0 - p) * length)) for p in params]]

    if gap > 1e-4 * length:
        # a small gap, e.g. an open trailing edge: closed with a straight line
        chain = Rail(chains[0] + [Part.LineSegment(chain.end, chain.start).toShape()])
        length = chain.length

    def at(l):
        return normalize(chain.pointAtLength(l % length))

    def nearest(target):
        """Length along the profile of the point nearest to target"""
        count = 512
        i = min(range(0, count + 1), key=lambda i: (at(length * i / count) - target).Length)
        return goldenMinimum(lambda l: (at(l) - target).Length, length * (i - 1) / count, length * (i + 1) / count) % length

    # split at the leading and the trailing edge
    le = nearest(Vector(0, 0, 0))
    te = (nearest(Vector(1, 0, 0)) - le) % length
    a = [at(le + p * te) for p in params]
    b = [at(le - p * (length - te)) for p in params]
    a[0] = b[0] = (a[0] + b[0]) * 0.5
    a[-1] = b[-1] = (a[-1] + b[-1]) * 0.5
    # upper side first: going along a and back along b runs counterclockwise if a is the lower side
    polygon = a + b[-2:0:-1]
    area = sum(p.x * q.y - q.x * p.y for p, q in zip(polygon, polygon[1:] + polygon[:1]))
    return [b, a] if area > 0 else [a, b]


def profileWires(edges):
    """The edges joined to wires"""
    wires = []
    for chain in Part.sortEdges(edges):
        try:
            wires.append(Part.Wire(chain))
        except Exception:
            return Part.makeCompound(edges)

    if len(wires) == 1:
        return wires[0]
    return Part.makeCompound(wires)


def loftRibs(ribs, solid, maxDegree, maxLoftSize):
    """Surface or solid through the ribs. Ribs with several wires (a profile with holes, or of separate elements like
    an airfoil with a flap) are lofted wire by wire, holes are cut out of the solid"""
    counts = set(len(rib.Wires) for rib in ribs)
    if len(counts) == 1 and counts.pop() > 1:
        parts = [loftWires(layer, solid, maxDegree, maxLoftSize) for layer in matchWires(ribs)]
        if any(part is None or part.isNull() for part in parts):
            return None

        if solid and all(part.ShapeType == 'Solid' and part.isValid() for part in parts):
            try:
                shape, separate = parts[0], []
                for part in parts[1:]:
                    if shape.common(part).Volume > 0.5 * part.Volume:
                        shape = shape.cut(part)     # a hole
                    else:
                        separate.append(part)       # a separate element
                if len(shape.Solids) == 1 and shape.Solids[0].isValid():
                    return Part.makeCompound([shape.Solids[0]] + separate) if separate else shape.Solids[0]
            except Exception:
                pass
            FreeCAD.Console.PrintError(translate("Curved Shapes", "CurvedRailsArray: cannot cut the holes out of the solid") + "\n")
        elif solid:
            FreeCAD.Console.PrintError(translate("Curved Shapes", "CurvedRailsArray: cannot make a valid solid of the profile with several curves") + "\n")

        return Part.makeCompound(parts)

    return loftWires(ribs, solid, maxDegree, maxLoftSize)


def matchWires(ribs):
    """Per wire of the profile the list of its wires in all ribs: the outer wire first, then the holes, matched by their centres"""
    def ordered(rib):
        return sorted(rib.Wires, key=lambda w: w.BoundBox.DiagonalLength, reverse=True)

    layers = [ordered(ribs[0])]
    for rib in ribs[1:]:
        wires = ordered(rib)
        holes = wires[1:]
        layer = [wires[0]]
        for prev in layers[-1][1:]:
            hole = min(holes, key=lambda w: (w.CenterOfMass - prev.CenterOfMass).Length)
            holes.remove(hole)
            layer.append(hole)
        layers.append(layer)

    return [list(wires) for wires in zip(*layers)]


def loftWires(ribs, solid, maxDegree, maxLoftSize):
    """Surface or solid through ribs of one wire each"""
    if solid and (maxLoftSize <= 0 or len(ribs) - 1 <= maxLoftSize):
        # a single loft: OCC makes the solid itself - more robust than closing the surface, e.g. with only two items
        try:
            shape = Part.makeLoft([rib.Wires[0] if rib.Wires else Part.Wire(Part.__sortEdges__(rib.Edges)) for rib in ribs], True, False, False, maxDegree)
            if shape.isValid() and abs(shape.Volume) > epsilon:
                return outward(shape)
        except Exception:
            pass

    shape = CurvedShapes.makeSurfaceSolid(ribs, solid, maxDegree=maxDegree, maxLoftSize=maxLoftSize)
    if shape and shape.ShapeType == 'Solid':
        shape = outward(shape)
    return shape


def outward(solid):
    """The solid with its faces pointing outwards (a positive volume)"""
    if solid.ShapeType == 'Solid' and solid.Volume < 0:
        solid.reverse()
    return solid


class Blend:
    """Interpolates lists of numbers given at increasing positions, before the first and after the last position they stay constant.
    Smooth: monotone cubic curves (PCHIP) through all positions, they do not overshoot. Linear: straight from one position to the next."""
    def __init__(self, positions, values, smooth):
        self.x = positions
        self.y = values
        self.slopes = None
        n = len(positions)
        if smooth and n > 2:
            h = [positions[k + 1] - positions[k] for k in range(0, n - 1)]
            self.slopes = [[0.0] * len(values[0]) for _ in range(0, n)]
            for i in range(0, len(values[0])):
                delta = [(values[k + 1][i] - values[k][i]) / h[k] for k in range(0, n - 1)]
                for k in range(1, n - 1):
                    if delta[k - 1] * delta[k] > 0:
                        w1 = 2 * h[k] + h[k - 1]
                        w2 = h[k] + 2 * h[k - 1]
                        self.slopes[k][i] = (w1 + w2) / (w1 / delta[k - 1] + w2 / delta[k])

                self.slopes[0][i] = endSlope(h[0], h[1], delta[0], delta[1])
                self.slopes[-1][i] = endSlope(h[-1], h[-2], delta[-1], delta[-2])


    def at(self, f):
        x = self.x
        if f <= x[0]:
            return self.y[0]
        if f >= x[-1]:
            return self.y[-1]

        k = max(i for i in range(0, len(x) - 1) if x[i] <= f)
        h = x[k + 1] - x[k]
        t = (f - x[k]) / h
        y0 = self.y[k]
        y1 = self.y[k + 1]
        if self.slopes is None:
            return [a + t * (b - a) for a, b in zip(y0, y1)]

        h00 = (1 + 2 * t) * (1 - t) ** 2
        h10 = t * (1 - t) ** 2
        h01 = t * t * (3 - 2 * t)
        h11 = t * t * (t - 1)
        return [h00 * a + h10 * h * da + h01 * b + h11 * h * db for a, b, da, db in zip(y0, y1, self.slopes[k], self.slopes[k + 1])]


def endSlope(h0, h1, m0, m1):
    """Slope at the first or last position of a monotone cubic"""
    d = ((2 * h0 + h1) * m0 - h0 * m1) / (h0 + h1)
    if d * m0 <= 0:
        return 0.0
    if m0 * m1 <= 0 and abs(d) > abs(3 * m0):
        return 3 * m0
    return d


def goldenMinimum(function, a, b, iterations=60):
    """x in [a, b] where function has its minimum"""
    g = (math.sqrt(5) - 1) / 2
    c = b - g * (b - a)
    d = a + g * (b - a)
    fc = function(c)
    fd = function(d)
    for _ in range(0, iterations):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - g * (b - a)
            fc = function(c)
        else:
            a, c, fc = c, d, fd
            d = a + g * (b - a)
            fd = function(d)

    return (a + b) / 2


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

        self.lengths = [edge.Length for edge, _ in self.edges]
        self.length = sum(self.lengths)
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
        self.lengths.reverse()
        if self.samples:
            self.samples.reverse()


    def parameterAtLength(self, length):
        """(edge, reversed, parameter) at the given arc length from the start"""
        length = min(max(length, 0.0), self.length)
        for n, (edge, reverse) in enumerate(self.edges):
            if length <= self.lengths[n] or n == len(self.edges) - 1:
                if reverse:
                    length = self.lengths[n] - length
                return edge, reverse, edge.getParameterByLength(min(max(length, 0.0), self.lengths[n]))

            length -= self.lengths[n]


    def valueAtLength(self, length):
        """Point and unit tangent in rail direction at the given arc length from the start"""
        edge, reverse, param = self.parameterAtLength(length)
        return edge.valueAt(param), edgeTangent(edge, param, reverse)


    def pointAtLength(self, length):
        edge, _, param = self.parameterAtLength(length)
        return edge.valueAt(param)


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


def edgeChains(shape):
    """Separate curves of a shape, each a list of connected edges"""
    return [edges for edges in Part.sortEdges(shape.Edges) if sum(e.Length for e in edges) > epsilon]


def curvePieces(o):
    """Separate curves of an object, each a list of connected edges"""
    if o is None or not hasattr(o, "Shape") or o.Shape.isNull() or len(o.Shape.Edges) == 0:
        return []

    return edgeChains(o.Shape)


def getRails(objects):
    """Two Rails: either from two objects or from one object containing two separate curves"""
    curves = []     # per object: list of connected pieces, each a list of edges
    for o in objects:
        pieces = curvePieces(o)
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


def profileNormal(shape, points, label):
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
        FreeCAD.Console.PrintWarning(translate("Curved Shapes", "CurvedRailsArray: profile %s is not planar") % label + "\n")
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


def profileFrame(shape, label="Base"):
    """Chord of the profile: (leading point, chord direction u0, thickness direction v0, normal n0, chord length)"""
    points = profilePoints(shape)
    if len(points) < 2:
        return None

    normal = profileNormal(shape, points, label)
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
    """Move a point that is almost on the profile (e.g. the tip of a rounded nose) exactly onto its outline"""
    try:
        dist, pairs, _ = Part.Compound(shape.Edges).distToShape(Part.Vertex(point))
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


def splitSelection(selection):
    """(profiles, rails) from selected objects: the profiles first, the rails last - two objects, or one object containing two separate curves"""
    if not selection:
        return [], []

    railcount = 1 if len(curvePieces(selection[-1])) == 2 else 2
    railcount = max(min(railcount, len(selection) - 1), 0)
    profiles = selection[0:len(selection) - railcount]
    rails = selection[len(selection) - railcount:]
    # rails are open curves - a closed one (or almost closed, like an airfoil with an open trailing edge) is probably a profile
    for o in rails:
        for edges in curvePieces(o):
            rail = Rail(edges)
            if (rail.start - rail.end).Length < 0.02 * rail.length:
                FreeCAD.Console.PrintWarning(translate("Curved Shapes", "CurvedRailsArray: rail %s is a closed curve. Select the profiles first and the two rails last") % o.Label + "\n")
                return profiles, rails

    return profiles, rails


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
        return [o for o in [self.Object.Base] + list(getattr(self.Object, "Profiles", [])) + self.Object.Rails if o]


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

            profiles, rails = splitSelection([sel.Object for sel in FreeCADGui.Selection.getSelectionEx()])
            get = lambda o: "FreeCAD.ActiveDocument.getObject('%s')" % o.Name
            FreeCADGui.doCommand("base = %s" % (get(profiles[0]) if profiles else "None"))
            FreeCADGui.doCommand("profiles = [%s]" % ", ".join(get(o) for o in profiles[1:]))
            FreeCADGui.doCommand("rails = [%s]" % ", ".join(get(o) for o in rails))
            FreeCADGui.doCommand("CurvedShapes.makeCurvedRailsArray(Base=base, Profiles=profiles, Rails=rails, Items=8, Surface=False)")
            FreeCAD.ActiveDocument.recompute()


        def IsActive(self):
            return FreeCAD.ActiveDocument is not None


        def GetResources(self):
            return {'Pixmap'  : os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "CurvedRailsArray.svg"),
                    'Accel' : "", # a default shortcut (optional)
                    'MenuText': QT_TRANSLATE_NOOP("CurvedRailsArray", "Curved Rails Array"),
                    'ToolTip' : __doc__}


    FreeCADGui.addCommand('CurvedRailsArray', CurvedRailsArrayCommand())
