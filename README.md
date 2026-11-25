# Curved Shapes Workbench

A FreeCAD External Workbench for creating 3D shapes from 2D curves

[> deutsch <](https://github.com/chbergmann/CurvedShapesWorkbench/blob/master/LIESMICH.md)  

## Installation

### Automatic Installation
[![FreeCAD Addon manager status](https://img.shields.io/badge/FreeCAD%20addon%20manager-available-brightgreen)](https://github.com/FreeCAD/FreeCAD-addons)  
**Note: This is the recommended way to install this workbench.**  
The Curved Shapes workbench is available through the builtin FreeCAD [Addon Manager](https://github.com/FreeCAD/FreeCAD-addons#1-builtin-addon-manager).
Once installed all that is needed is to restart FreeCAD and the workbench will be available in the [workbench dropdown list](https://freecadweb.org/wiki/Std_Workbench) menu.

### Manual Installation

```bash
cd ~/FreeCAD/Mod/ 
git clone https://github.com/chbergmann/CurvedShapesWorkbench.git
```
When you restart FreeCAD, "Curved Shapes" workbench should now show up in the [workbench dropdown list](https://freecadweb.org/wiki/Std_Workbench).
  
## Video Tutorial
JOKO engineering made a great tutorial

[!["FreeCAD Curved Shapes WB: Make Insane and Exact Surfaces Quick! |JOKO ENGINEERING|"](http://img.youtube.com/vi/Wls0cqhVCc4/0.jpg)](http://www.youtube.com/watch?v=Wls0cqhVCc4 "FreeCAD Curved Shapes WB: Make Insane and Exact Surfaces Quick! |JOKO ENGINEERING|")  
  
## Tools
### ![curvedArrayIcon](./Resources/icons/curvedArray.svg) Curved Array
Creates an array and resizes the items in the bounds of one or more hull curves.
In this example, the orange base shape is rescaled in the bounds of the red and violet hullcurves. The curves do not have to be connected.  
The hullcurves should lie on or parallel to the XY- XZ- or YZ- plane.  

![WingExample](Examples/WingExample.png)
  
The first curve that you select for CurvedArray creation will be the item that is swept and resized in the bounds of the other selected curves.

#### Parameters
- Base: The object to make an array from
- Hullcurves: List of one or more bounding curves
- PreserveAspectRatio: Useful when only one hullcurve exists. Will scale based on the ratio of your base object's height/width. See [Fishing Lure example](#-fishing-lure) for more info.
- Axis: Direction axis of the Base shape
- Items: Nr. of array items
- Positions: Array of position for each rib (as floats from 0.0 to 1.0) -- overrides Items
- OffsetStart: Offset of the first part in Axis direction
- OffsetEnd: Offset of the last part from the end in opposite Axis direction
- Twist: Applies a rotation around Axis to the array items. Only used if Twists is an empty array
- Twists: Array of rotation angles for each rib. If empty, parameter Twist is used.
- Surface: make a surface over the array items
- Solid: make a solid if Base is a closed shape
- Distribution: Algorithm for distance between array elements. Default is 'linear'. Also selectable: parabolic (x²), x³, sinusoidal, asinusoidal, elliptic
- DistributionReverse: Reverses the direction of the Distribution algorithm
- LoftMaxDegree: degree for surface or solid creation. Play with this parameter if your surface or solid looks distorted
- MaxLoftSize: Maximum size of a loft segment. The surface is created by creating a loft over many array items, however OpenCascade gets very slow and produces artefacts towards the end of the loft when the array gets too large. Therefore the array gets split up intp sub-arrays of up to MaxLoftSize items. Play with this value if a split between segements ends up in a inconvenient spot. Sensible values are between 10 and 50.
- KeepBase: use the Base object as one of the endpoints of the array

Distribution Linear  
![Linear](Examples/CurvedArrayLinear.jpg)  
  
Distribution parabolic  
![parabolic](Examples/CurvedArrayX2.jpg)  
  
Distribution x³  
![x³](Examples/CurvedArrayX3.jpg)  
  
Distribution sinusoidal  
![sinusoidal](Examples/CurvedArraySinus.jpg) 
   
Distribution asinusoidal  
![asinusoidal](Examples/CurvedArrayASinus.jpg) 

Distribution elliptic  
![elliptic](Examples/CurvedArrayElliptic.jpg)  
If you create a surface with the Curved Array, a different distribution may give you better results.

If you create an elliptic wing, distribution elliptic would be the best solution.
If you create the Curved Array inside a half circle, sinusoidal is best.
If the hullcurves are created from simple spline curves, parabolic or x³ may give you the best results.
If you are unsure, choose linear.

If you create a surface or solid and it looks weird, this may be caused by very small items at the start and end of the CurvedArray. In this case, enter values bigger than 0 for Start Offset and End Offset. This will create bigger start and end items located not at the very end.

To resolve a CurvedArray item to a compound of single objects, go to the Part workbench. In the [Part workbench](https://www.freecadweb.org/wiki/Part_Workbench), select **Part → Compound → [Explode compound](https://www.freecadweb.org/wiki/Part_ExplodeCompound)**
  

### ![curvedRailsArrayIcon](./Resources/icons/CurvedRailsArray.svg) Curved Rails Array
Creates an array of a profile that is stretched between two 3D rail curves, for example the leading and trailing edge of a twisted propeller blade.  
At every array item the rails give two points. The chord of the profile (for an airfoil: from the leading edge to the trailing edge) is scaled and rotated so that it spans exactly from the first rail to the second rail. Position, size and twist of the items therefore come from the rails. Unlike the hullcurves of Curved Array, the rails do not have to lie in the XY, XZ or YZ plane, and there is no Twist parameter.

Select the profile first, then the two rails (or one object that contains two separate curves). Then create the Curved Rails Array. To blend several profiles, select all of them first, see below.

The chord of the profile is found automatically. Starting with the X axis of the profile (the horizontal axis of a sketch), it is the line from the leftmost to the rightmost point of the profile. The leftmost point is attached to the first rail. If the profile ends up the wrong way round, toggle SwapRails. The profile does not have to be placed at the rails.

If the rails touch the profile where its item meets them, the item there is exactly the profile as it is placed, and SwapRails has no effect on it. In 2D mode this is the case when the leading and trailing edge points of the sketch lie on the rails and the sketch lies in a plane perpendicular to Axis. In 3D mode the two points must also be at the same fraction of the length of each rail - always true at the ends of the rails, usually not in between. The Report view tells whether the rails touch a profile.

#### Several profiles
A blade often needs different profiles along its span, e.g. a thick airfoil at the root and a thin one at the tip, or a round shank at the hub that turns into an airfoil. Select all profiles first, then the rails. The first profile becomes Base, the others go to Profiles. The items in between get a shape blended from the profiles next to them.

The position of a profile is taken from where it is placed: put the profiles across the rails where you want them along the blade, in any order. Profiles that are not placed at the rails (e.g. sketches left at the origin) are spaced evenly between their neighbours in the order Base, Profiles - if no profile is placed, from the start to the end of the array. A profile without room between its neighbours (e.g. one added after the tip profile) goes into the largest gap. A profile beyond the end of the array applies at the first or last item. The Report view lists the position of every profile in the order Base, Profiles - the order of ProfilePositions -, how it is used and whether the profiles are blended edge by edge or resampled. Use ProfilePositions to set the positions by hand.

How a profile is used:
- If the rails touch the profile where its item meets them (see above), the item at that position is exactly the profile as it is placed (resampled profiles, see below, up to the resampling).
- Otherwise the rails win: the profile is stretched between the rails like Base and only its shape is used, so the profiles do not have to be placed precisely. It is turned so that its thick end and its camber point the same way as those of the nearest profile that has them. A profile with neither (e.g. a round shank) cannot show the way: without a touched profile that has a thick end or camber, Base is attached as described above (SwapRails) and the other profiles follow Base.

Profiles that are copies of one sketch with other dimensions (same edges) are blended exactly, circles and arcs included. Profiles with different edges (e.g. a circle and an airfoil) are split at their leading and trailing edge and resampled with InterpolationPoints points per side, this slightly rounds sharp corners. When profiles are blended, a small gap, e.g. an open trailing edge, is closed with a straight line. All profiles must be either closed or open. Profiles with holes (e.g. for a spar) or of separate elements (e.g. an airfoil with a flap) can be blended if they all have the same edges; a solid then gets the holes cut out, separate elements become separate solids.

#### Modes
- 2D: like Curved Array, all items lie in planes perpendicular to Axis. Use this for propeller blades and wings whose sections are taken along a straight axis.
- 3D: the items follow the rails. Each item stands perpendicular to the rails and tilts where the rails bend, e.g. when both rails go up into a winglet.

#### Parameters
- Base: The profile to make an array from, the first profile if there are several
- Profiles: Further profiles, e.g. in the middle and at the tip. Each one applies where it is placed along the rails, the items in between are blended. To add a tip profile to an existing array, add it here.
- ProfilePositions: Position of every profile: Base first, then Profiles, on the same scale as Positions (0.0 = start, 1.0 = end of the array; without Positions the first and the last item). Empty: taken from where the profiles are placed, see the Report view
- ProfileBlend: How the shape changes between more than two profiles. smooth: smooth curves through all profiles, without overshooting between them. linear: straight from one profile to the next
- InterpolationPoints: Only for profiles that cannot be blended edge by edge (e.g. a circle and an airfoil): they are resampled with this number of points per side (at most 1000)
- Rails: Two curves the ends of the profile chord follow (e.g. leading and trailing edge). A rail may consist of several connected edges.
- Mode: 2D or 3D, see above
- Axis: Direction of the array, the first item is at the negative end. Computed automatically if 0,0,0: the normal of Base if the rails run roughly in that direction, otherwise the direction of the rails.
- Items: Nr. of array items
- Positions: Array of positions for each item (as floats from 0.0 to 1.0) -- overrides Items
- OffsetStart: Offset of the first item from the start of the rails (along Axis in 2D mode, along the rails in 3D mode)
- OffsetEnd: Offset of the last item from the end of the rails
- ScaleThickness: If true, the thickness of the profile scales with its chord, so an airfoil keeps its relative thickness. If false, only the chord is stretched and the thickness of Base is kept (with several profiles: their thickness, blended in between).
- SwapRails: Attach the other end of the profile chord to the first rail. No effect on profiles the rails touch, nor on profiles that follow a touched profile with a thick end or camber
- Surface: make a surface over the array items
- Solid: make a solid if Base is a closed shape
- Distribution: Algorithm for distance between array elements, see Curved Array
- DistributionReverse: Reverses the direction of the Distribution algorithm (the items still run from the start to the end of the rails)
- LoftMaxDegree: degree for surface or solid creation. Play with this parameter if your surface or solid looks distorted
- MaxLoftSize: Maximum size of a loft segment, see Curved Array
- KeepBase: use the unmodified Base object as the item at the start (First) or at the end (Last) of the rails (with several profiles: the profile at that end of the rails)

Where the rails touch each other (e.g. at a pointed blade tip) no item can be created. Use OffsetStart / OffsetEnd to stay away from such points.
  

### ![curvedPathArrayIcon](./Resources/icons/CurvedPathArray.svg) Curved Path Array
Creates an array, sweeps the elements around a path curve, and resizes the items in the bounds of optional hullcurves.  
The items created will be perpendicular to the sweep path.  
There is a twist parameter to let the items rotate around the sweep path.
If you do not use hullcurves and twist, this tool is similar to the Path Array tool in the Draft workbench.

![CurvedPathArray](Examples/CurvedPathArray.jpg)  

The first curve that you select for Curved Path Array creation will be the base item. The second selected curve will become the path. All curves selected after that will be the hullcurves.

#### Parameters
- Base: The object to make an array from
- Path: Sweep path
- Hullcurves: List of one or more bounding curves   
- Items: Nr. of array items
- OffsetStart: Offset of the first part from the beginning of the sweep path
- OffsetEnd: Offset of the last part from the end in opposite direction
- Twist: Rotate in degrees around the sweep path
- Surface: make a surface over the array items
- Solid: make a solid if Base is a closed shape
- ScaleX: Scale by hullcurves in X direction
- ScaleY: Scale by hullcurves in Y direction
- ScaleZ: Scale by hullcurves in Z direction
- LoftMaxDegree: degree for surface or solid creation. Play with this parameter if your surface or solid looks distorted
- MaxLoftSize: Maximum size of a loft segment. The surface is created by creating a loft over many array items, however OpenCascade gets very slow and produces artefacts towards the end of the loft when the array gets too large. Therefore the array gets split up intp sub-arrays of up to MaxLoftSize items. Play with this value if a split between segements ends up in a inconvenient spot. Sensible values are between 10 and 50.

The parameters ScaleX, ScaleY and ScaleZ have been added because you may want to rescale the items only in one direction, but the hullcurves normally cover 2 or three room directions.  
  
### ![curvedSegmentIcon](./Resources/icons/curvedSegment.svg) Curved Segment
Interpolates between two 2D curves. The interpolated curves can be resized in the bounds of some hullcurves.
This does not work for all kinds of shapes. The result may look distorted if the two shapes are too different. The parameters TwistReverse and ForceInterpolated may help to get better results.  

![CurvedSegment](Examples/CurvedSegment.jpg)
![CurvedSegment2](Examples/CurvedSegment2.jpg)

Select two 2D shapes first. The curved segment will be created between them. If you want to use hullcurves, select them also. Then create the Curved Segment.

#### Parameters
- Shape1: The first object of the segment
- Shape2: The last object of the segment
- Hullcurves: List of one or more bounding curves in XY, XZ or YZ plane (optional)
- NormalShape1: Direction axis of Shape1 (auto computed)
- NormalShape2: Direction axis of Shape2 (auto computed)
- Items: Nr. of items between the segments
- makeSurface: make a surface over the array items
- makeSolid: make a solid if Base is a closed shape
- InterpolationPoints: ignored if Shape1 and Shape2 have the same number of edges and poles. Otherwise all edges will be split (discretized) into this number of points
- Twist: twist into the shape around the profiles normal axis. Useful for example for threaded parts.
- TwistReverse: Reverses the rotation of one Shape. This is for correcting misalignment between the shapes, use this if the entire shape is inversed on itself (wasp-tail)
- Path: Sweep path - Only used for Curved Path Segment
- Distribution: Algorithm for distance between array elements. Default is 'linear'. Also selectable: parabolic (x²), x³, sinusoidal, elliptic
- DistributionReverse: Reverses the direction of the Distribution algorithm
- LoftMaxDegree: degree for surface or solid creation. Play with this parameter if your surface or solid looks distorted
- MaxLoftSize: Maximum size of a loft segment. The surface is created by creating a loft over many array items, however OpenCascade gets very slow and produces artefacts towards the end of the loft when the array gets too large. Therefore the array gets split up intp sub-arrays of up to MaxLoftSize items. Play with this value if a split between segements ends up in a inconvenient spot. Sensible values are between 10 and 50.
- ForceInterpolated: By default, CurvedSegment tries a more direct transition from the first to the second object if the objects have the same number of points and lines and interpolates intermediate shapes if they don't. In case the direct approach does not work because the type or order of lines does not match, interpolation can be forced with this parameter even if the number of points is equal. This should only be needed in rare cases.

### ![curvedSegmentIcon](./Resources/icons/CurvedPathSegment.svg) Curved Path Segment
Interpolates between two 2D curves and sweeps the elements around a path curve. The interpolated curves can be resized in the bounds of some hullcurves.  

Select two 2D shapes first, then a sweep path curve. The curved segment will be created between them. If you want to use hullcurves, select them also. Then create the Curved Segment.

#### Parameters
same as in Curved Segment
- Path: Sweep path - similar to "Path" in CurvedPathArray. If a path is specified, it supersedes the position and orientation of Shape1 and Shape2. CurvedSegment then behaves like CurvedPathArray but with a blend between a beginning and end profile.


### ![CornerShapeIcon](./Resources/icons/CornerShape.svg) Interpolated Middle
Interpolates a 2D shape into the middle between two 2D curves. The base shapes can be connected to a shape with a sharp corner.

![InterpolatedMiddle2](Examples/InterpolatedMiddle2.jpg)
![InterpolatedMiddle](Examples/InterpolatedMiddle.jpg)
 
#### Parameters
- Shape1: The first object of the segment
- Shape2: The last object of the segment     
- NormalShape1: Direction axis of Shape1 (auto computed)
- NormalShape2: Direction axis of Shape2 (auto computed)
- makeSurface: connect Shape1 and Shape2 with a surface over the interpolated middle
- makeSolid: make a solid if Shape1 and Shape2 are closed shapes
- InterpolationPoints: ignored if Shape1 and Shape2 have the same number of edges and poles. Otherwise all edges will be split (discretized) into this number of points  
- Twist: Compensates a rotation between Shape1 and Shape2
- TwistReverse: Reverses the rotation of one Shape
- LoftMaxDegree: degree for surface or solid creation. Play with this parameter if your surface or solid looks distorted
- MaxLoftSize: Maximum size of a loft segment. The surface is created by creating a loft over many array items, however OpenCascade gets very slow and produces artefacts towards the end of the loft when the array gets too large. Therefore the array gets split up intp sub-arrays of up to MaxLoftSize items. Play with this value if a split between segements ends up in a inconvenient spot. Sensible values are between 10 and 50.
  
  
### ![surfaceCutIcon](./Resources/icons/surfaceCut.svg) Surface Cut
Cuts a surface to get the outline curve or a face.  
This tool is similar to [Cross-Sections](https://www.freecadweb.org/wiki/Part_SectionCross) in the [Part workbench](https://www.freecadweb.org/wiki/Part_Workbench), but it is fully parametric and has an option to reduce the complexity of the output curve.
It tries to remove overlapping edges.

![SurfaceCut](Examples/SurfaceCut.jpg)

#### Parameters
- Surfaces: List of objects with a surface
- Normal:   Normal vector of the cut plane
- Position: Position of the cut plane relative to Surfaces
- Face:     create a face
- Simplify: reduce the number of poles in complex curves. If true, an approximation curve is calculated. This may drastically reduce the number of points in some curves. This speeds up the usage of the result curve. In special cases this may not work as expected.  
  
  
### ![NotchConnectorIcon](./Resources/icons/NotchConnector.svg) Notch Connector
Cuts notches into overlapping objects to make it connectable to each other.  
  
![NotchConnector](Examples/NotchConnector.jpg)  
  
Select two objects, then select Notch Connector. Two NotchConnector objects will be created.

#### Parameters
- Base:  		Object to cut
- Tools: 		The object that cuts Base   
- CutDirection: The direction of the cut (autocomputed)    
- CutDepth: 	The depth of the cut in percent
- ShiftLength:	Shift the tools by ShiftLength, then cut. If ShiftLength is not zero, it overrides CutDepth and uses another algorithm. 

#### Troubleshooting
If the notches are cut at the wrong place, edit the parameter CutDirection manually. Avoid the value `0,0,0` since this will autocompute new values.

### ![alt text](./Resources/icons/LasercutterTechdrawExport.svg) Lasercutter Techdraw Export

This tool has been moved to the macro [LasercutterSVGExport](https://forum.freecadweb.org/viewtopic.php?f=35&t=31869)  
Install it from the Macros tab in the resources manager.
  
  
## Examples
Example designs in script format for testing and presenting this workbench.  

### ![Horten_HIX_Icon](./Resources/icons/Horten_HIX.svg) Horten H IX
A python script that creates the shape of the [Horten Ho 229 (also called Horten H IX)](https://en.wikipedia.org/wiki/Horten_Ho_229), a stealth fighter that has been build in Germany in 1944.

### ![FlyingWingS800-sIcon](./Resources/icons/FlyingWingS800.svg) Flying Wing S800 
A python script that creates the shape of a flying wing RC model.  
  
![S800](Examples/S800.jpg)

### ![Propeller_Icon](./Resources/icons/Propeller.svg) Propeller
A three bladed propeller made with Curved Rails Array. The leading and trailing edge of a blade are 3D curves that give the twist of the blade. A thick airfoil sketch at the hub and a thin one at the tip are placed where the rails touch them, the airfoils in between are blended.

### Faster Better Corsair |JOKO ENGINEERING|
[!["FreeCAD Curved Surfaces Workbench in Action: Faster Better Corsair |JOKO ENGINEERING|"](http://img.youtube.com/vi/tjT9gt0dArQ/0.jpg)](http://www.youtube.com/watch?v=tjT9gt0dArQ "FreeCAD Curved Surfaces Workbench in Action: Faster Better Corsair |JOKO ENGINEERING|") 

### ![FishingLure_Icon](./Resources/icons/FishingLure.svg) Fishing Lure

This example demonstrates the PreserveAspectRatio property of CurvedArray. It creates 5 curved arrays for visual comparison and model inspection. 

You can see that when a circle is used as a base object, it remains a circle across all items when PreserveAspectRatio is set to True. With PreserveAspectRatio = False, a circle would become an ellipsis when the hullcurve geometry is non-parallel. Works for other geometry, not just a circle.

In this screenshot, the top two rows show the effect of PreserveAspectRatio being true and false for the same hullcurve and base object. (The fifth object uses two hullcurves to control top width.)

![FishingLure](Examples/FishingLure.jpg)


## Discussion
Please offer feedback or connect with the developer via the [dedicated FreeCAD forum thread](https://forum.freecad.org/viewtopic.php?f=8&t=36989).

## License
GNU Lesser General Public License v3.0
