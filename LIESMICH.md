# Curved Shapes
[> english <](https://github.com/chbergmann/CurvedShapesWorkbench/blob/master/README.md)  
  
FreeCAD Arbeitsbereich zum Erstellen von 3D Körpern aus 2D Kurven
  
## Installation

Dieser Arbeitsbereich kann über den Addon manager in FreeCAD installiert werden.

**Manuelle Installation**
- `cd` in deinen FreeCAD Ordner (normalerweise `~/.FreeCAD` on Linux)
- `cd Mod/` (Ordner Mod anlegen, falls er nicht existiert)
- `git clone https://github.com/chbergmann/CurvedShapesWorkbench.git`
- Starte FreeCAD

"Curved Shapes" sollte nun in der Liste der Arbeitsbereiche auswählbar sein.
  
## Video Tutorial
Hier ein großartiges Tutorial von JOKO engineering (in englisch)

[!["FreeCAD Curved Shapes WB: Make Insane and Exact Surfaces Quick! |JOKO ENGINEERING|"](http://img.youtube.com/vi/Wls0cqhVCc4/0.jpg)](http://www.youtube.com/watch?v=Wls0cqhVCc4 "FreeCAD Curved Shapes WB: Make Insane and Exact Surfaces Quick! |JOKO ENGINEERING|")  
  
## Werkzeuge
### ![](./Resources/icons/curvedArray.svg) Curved Array
Erstellt mehrere Kopien von einem Basisobject (Base) und verschiebt diese und passt die Größe an innerhalb von einer oder mehreren Hüllkurven (Hullcurves)  
In dem Beispiel unten wird das rote Flügelprofil innerhalb der orangenen Hüllkurven vervielfacht.  
Base und Hullcurves brauchen nicht miteinanden verbunden sein und sollten in einer der Raumebenen XY, XZ, oder YZ liegen. 

![WingExample](Examples/WingExample.png)
  
Zuerst das Basisobjekt auswählen, danach die Hüllkurven. Dann ein Curved Array Objekt erstellen.

#### Parameters
- Base: Das Basisobjekt
- Hullcurves: Eine oder mehrere Hüllkurven        
- Axis: Richtung, in der die Array Elemente aufgebaut werden (wird automatisch berechnet)
- Items: Anzahl der Array Elemente
- OffsetStart: Abstand des ersten Array Elements vom Anfang der Hüllkurven
- OffsetEnd: Abstand des letzten Array Elements vom Ende der Hüllkurven
- Twist: (Winkel in Grad) Lässt die Array Elemente rotieren
- Surface: Eine Oberfläche erstellen
- Solid: Einen Festkörper erstellen (funktioniert nur, wenn Base eine geschlossene Form ist)
- Distribution: Algorithmus zur Berechnung der Distanz zwischen den Elementen. Default ist 'linear'. Weitere Möglichkeiten: parabolic (x²), x³, sinusoidal, asinusoidal, elliptic
- DistributionReverse: Kehrt die Richtung des Distrubution Algorithmus um
- LoftMaxDegree: Gradzahl für die Erstellung von Oberflächen und Festkörpern. 
- MaxLoftSize: Maximale Anzahl von Elementen für die Erstellung von Oberfächen und Festkörpern  
- KeepBase: Basisobjekt als erstes oder letztes Array Element benutzen
- PreserveAspectRatio: Das Verhältnis von Höhe/Breite von Base wird beibehalten. Nützlich falls nur eine hullcurve existiert. Siehe [Fishing Lure example](#-fishing-lure).

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

Wenn man eine Oberfläche erstellt (Surface = True), können mit Distribution evtl. bessere Ergebnisse erzielt werden.
Für elliptische Flügel kann elliptic die beste Lösung sein.
Bei einem CurvedArray in einem Halbkreis ist sinusoidal am Besten.
Parabolic oder x³ sind evtl. bei spline curves die beste Wahl.
Im Zweifelsfall linear wählen.

Möglichkeiten zur Verbesserung der generierten Form:  
Die erste Möglichkeit das Ergebnis zu verbessern ist den Parameter Items zu erhöhen auf z.B. 100. Das erhöht die Auflösung und macht die Rundungen runder, dauert aber länger bis es fertig berechnet ist.
Zwite Möglichkeit: Für Offset Start und/oder Offset End größere Werte eingeben, z.B. 0,1. Damit wird die erste bzw. die letzte Scheibe nicht am äußersten Punkt der Hüllkurven generiert, sondern 0,1mm davon entfernt.

Array Elemente aus Curved Array extrahieren (funktioniert nur, wenn Surface und Solid false sind): In der Part workbench, Menü Formteil -> Flächenverbund -> Verbundteile extrahieren 
  

### ![](./Resources/icons/CurvedRailsArray.svg) Curved Rails Array
Erstellt mehrere Kopien von einem Profil (Base), das zwischen zwei 3D Kurven (Rails) aufgespannt wird, z.B. zwischen der Vorder- und der Hinterkante eines verdrehten Propellerblatts.  
An jedem Array Element liefern die Rails zwei Punkte. Die Sehne des Profils (bei einem Flügelprofil von der Nase bis zur Endleiste) wird so skaliert und gedreht, dass sie genau von der ersten bis zur zweiten Rail reicht. Position, Größe und Verdrehung der Elemente ergeben sich dadurch aus den Rails. Anders als die Hüllkurven von Curved Array müssen die Rails nicht in der XY, XZ oder YZ Ebene liegen, und es gibt keinen Twist Parameter.

Zuerst das Profil auswählen, danach die beiden Rails (oder ein Objekt, das zwei getrennte Kurven enthält). Dann ein Curved Rails Array Objekt erstellen. Um mehrere Profile zu überblenden, zuerst alle Profile auswählen, siehe unten.

Die Sehne des Profils wird automatisch bestimmt: ausgehend von der X Achse des Profils (der Horizontalen einer Skizze) ist es die Linie vom äußersten linken bis zum äußersten rechten Punkt des Profils. Der linke Punkt liegt auf der ersten Rail. Liegt das Profil verkehrt herum, SwapRails umschalten. Das Profil muss nicht an den Rails liegen.

Berühren die Rails das Profil dort, wo sein Element auf sie trifft, ist das Element dort genau das Profil, so wie es platziert ist, und SwapRails hat darauf keine Wirkung. Im 2D Modus ist das der Fall, wenn die Punkte der Vorder- und Hinterkante der Skizze auf den Rails liegen und die Skizze in einer Ebene rechtwinklig zu Axis liegt. Im 3D Modus müssen die beiden Punkte zusätzlich beim selben Bruchteil der Länge jeder Rail liegen - an den Enden der Rails immer, dazwischen meist nicht. Das Ausgabefenster (Report view) zeigt, ob die Rails ein Profil berühren.

#### Mehrere Profile
Ein Blatt braucht oft verschiedene Profile entlang der Spannweite, z.B. ein dickes Flügelprofil an der Wurzel und ein dünnes an der Spitze, oder einen runden Schaft an der Nabe, der in ein Flügelprofil übergeht. Zuerst alle Profile auswählen, danach die Rails. Das erste Profil wird Base, die anderen kommen in Profiles. Die Elemente dazwischen erhalten eine Form, die aus den benachbarten Profilen überblendet wird.

Die Position eines Profils ergibt sich daraus, wo es platziert ist: die Profile quer zu den Rails dort hinlegen, wo sie entlang des Blatts sein sollen, in beliebiger Reihenfolge. Profile, die nicht an den Rails liegen (z.B. Skizzen im Ursprung), werden gleichmäßig zwischen ihren Nachbarn in der Reihenfolge Base, Profiles verteilt - liegt kein Profil an den Rails, vom Anfang bis zum Ende des Arrays. Ein Profil ohne Platz zwischen seinen Nachbarn (z.B. eines, das nach dem Spitzenprofil hinzugefügt wurde) kommt in die größte Lücke. Ein Profil jenseits des Endes des Arrays gilt am ersten bzw. letzten Element. Das Ausgabefenster (Report view) zeigt die Position jedes Profils in der Reihenfolge Base, Profiles - der Reihenfolge von ProfilePositions -, wie es verwendet wird und ob die Profile Kante für Kante überblendet oder neu abgetastet werden. Mit ProfilePositions lassen sich die Positionen von Hand festlegen.

So wird ein Profil verwendet:
- Berühren die Rails das Profil dort, wo sein Element auf sie trifft (siehe oben), ist das Element an dieser Position genau das Profil, so wie es platziert ist (neu abgetastete Profile, siehe unten, bis auf das Abtasten).
- Sonst gelten die Rails: das Profil wird wie Base zwischen die Rails gespannt, nur seine Form wird verwendet. Die Profile müssen also nicht genau platziert werden. Es wird so gedreht, dass sein dickes Ende und seine Wölbung in dieselbe Richtung zeigen wie beim nächstgelegenen Profil, das sie hat. Ein Profil ohne beides (z.B. ein runder Schaft) kann die Richtung nicht vorgeben: ohne ein berührtes Profil mit dickem Ende oder Wölbung wird Base wie oben beschrieben angelegt (SwapRails) und die anderen Profile folgen Base.

Profile, die Kopien einer Skizze mit anderen Maßen sind (gleiche Kanten), werden exakt überblendet, auch Kreise und Bögen. Profile mit verschiedenen Kanten (z.B. ein Kreis und ein Flügelprofil) werden an Vorder- und Hinterkante geteilt und mit InterpolationPoints Punkten pro Seite neu abgetastet, dadurch werden scharfe Ecken leicht abgerundet. Beim Überblenden wird eine kleine Lücke, z.B. eine offene Hinterkante, mit einer geraden Linie geschlossen. Alle Profile müssen entweder geschlossen oder offen sein. Profile mit Löchern (z.B. für einen Holm) oder aus getrennten Teilen (z.B. ein Flügelprofil mit Klappe) lassen sich überblenden, wenn alle dieselben Kanten haben; ein Festkörper bekommt dann die Löcher ausgeschnitten, getrennte Teile werden getrennte Festkörper.

#### Modi
- 2D: wie bei Curved Array liegen alle Elemente in Ebenen rechtwinklig zu Axis. Geeignet für Propellerblätter und Flügel, deren Schnitte entlang einer geraden Achse liegen.
- 3D: die Elemente folgen den Rails. Jedes Element steht rechtwinklig zu den Rails und kippt mit, wo die Rails sich biegen, z.B. wenn beide Rails zu einem Winglet nach oben gehen.

#### Parameters
- Base: Das Profil, bei mehreren Profilen das erste
- Profiles: Weitere Profile, z.B. in der Mitte und an der Spitze. Jedes gilt dort, wo es entlang der Rails platziert ist, die Elemente dazwischen werden überblendet. Um einem bestehenden Array ein Spitzenprofil hinzuzufügen, es hier eintragen.
- ProfilePositions: Position jedes Profils: zuerst Base, dann Profiles, auf derselben Skala wie Positions (0.0 = Anfang, 1.0 = Ende des Arrays; ohne Positions erstes und letztes Element). Leer: ergibt sich daraus, wo die Profile platziert sind, siehe Ausgabefenster (Report view)
- ProfileBlend: Wie sich die Form zwischen mehr als zwei Profilen ändert. smooth: glatte Kurven durch alle Profile, ohne Überschwingen zwischen ihnen. linear: gerade von einem Profil zum nächsten
- InterpolationPoints: Nur für Profile, die sich nicht Kante für Kante überblenden lassen (z.B. ein Kreis und ein Flügelprofil): sie werden mit dieser Anzahl Punkte pro Seite neu abgetastet (höchstens 1000)
- Rails: Zwei Kurven, an denen die Enden der Profilsehne entlang laufen (z.B. Vorder- und Hinterkante). Eine Rail darf aus mehreren verbundenen Kanten bestehen.
- Mode: 2D oder 3D, siehe oben
- Axis: Richtung des Arrays, das erste Element liegt am negativen Ende. Wird automatisch berechnet, wenn 0,0,0: die Normale von Base, wenn die Rails ungefähr in diese Richtung verlaufen, sonst die Richtung der Rails.
- Items: Anzahl der Array Elemente
- Positions: Position jedes Elements (Werte von 0.0 bis 1.0) -- ersetzt Items
- OffsetStart: Abstand des ersten Array Elements vom Anfang der Rails (entlang Axis im 2D Modus, entlang der Rails im 3D Modus)
- OffsetEnd: Abstand des letzten Array Elements vom Ende der Rails
- ScaleThickness: true: die Dicke des Profils wird mit der Sehne skaliert, ein Flügelprofil behält also seine relative Dicke. false: nur die Sehne wird gestreckt, die Dicke von Base bleibt erhalten (bei mehreren Profilen: deren Dicke, dazwischen überblendet).
- SwapRails: Das andere Ende der Profilsehne an die erste Rail legen. Keine Wirkung auf Profile, die die Rails berühren, und auf Profile, die einem berührten Profil mit dickem Ende oder Wölbung folgen
- Surface: Eine Oberfläche erstellen
- Solid: Einen Festkörper erstellen (funktioniert nur, wenn Base eine geschlossene Form ist)
- Distribution: Algorithmus zur Berechnung der Distanz zwischen den Elementen, siehe Curved Array
- DistributionReverse: Kehrt die Richtung des Distribution Algorithmus um (die Elemente laufen trotzdem vom Anfang zum Ende der Rails)
- LoftMaxDegree: Gradzahl für die Erstellung von Oberflächen und Festkörpern
- MaxLoftSize: Maximale Anzahl von Elementen für die Erstellung von Oberfächen und Festkörpern
- KeepBase: Basisobjekt unverändert als Element am Anfang (First) oder am Ende (Last) der Rails benutzen (bei mehreren Profilen: das Profil an diesem Ende der Rails)

Wo sich die Rails berühren (z.B. an einer spitzen Blattspitze), kann kein Element erzeugt werden. Mit OffsetStart / OffsetEnd kann man solche Stellen vermeiden.
  
### ![curvedPathArrayIcon](./Resources/icons/CurvedPathArray.svg) Curved Path Array
Erstellt mehrere Kopien von einem Basisobject (Base) und ordnet diese rechwinklig zu einer Kurve (Path) an. Optional können Größe und Position innerhalb von einer oder mehreren Hüllkurven (Hullcurves) ausgerichtet werden.  
Ein Twist Parameter lässt die Elemente um die Path Kurve rotieren.  
Ohne Hullcurves und Twist ist dieses Tool ähnlich dem Sweep Path Tool aus der Draft workbench.

![CurvedPathArray](Examples/CurvedPathArray.jpg) 

Zuerst das Basisobjekt auswählen, danach den Pfad, und zum Schluss die Hüllkurven. Dann ein Curved Path Array Objekt erstellen.

#### Parameters
- Base: Das Basisobjekt
- Path: Basisobjekte werden an dieser Kurve ausgerichtet
- Hullcurves: (optional) Eine oder mehrere Hüllkurven    
- Items: Anzahl der Array Elemente
- OffsetStart: Abstand des ersten Array Elements vom Anfang von Path
- OffsetEnd: Abstand des letzten Array Elements vom Ende von Path
- Twist: (Winkel in Grad) Lässt die Array Elemente um Path rotieren
- Surface: Eine Oberfläche erstellen
- Solid: Einen Festkörper erstellen (funktioniert nur, wenn Base eine geschlossene Form ist)
- ScaleX: Hullcurves können in X Richtung skalieren
- ScaleY: Hullcurves können in Y Richtung skalieren
- ScaleZ: Hullcurves können in Z Richtung skalieren
- LoftMaxDegree: Gradzahl für die Erstellung von Oberflächen und Festkörpern.
- MaxLoftSize: Maximale Anzahl von Elementen für die Erstellung von Oberfächen und Festkörpern  

Wenn Hullcurves verwendet werden und die Objekte nicht rechtwinklig zum Path angeordnet sind, muss evtl. die Skaliereng in eine Raumrichtung ausgeschaltet werden, in dem ScaleX, ScaleY oder ScaleZ auf false gesetzt wird.

  
### ![](./Resources/icons/curvedSegment.svg) Curved Segment
Interpoliert zwischen zwei 2D Kurven. Die interpolieren Kurven können innerhalb von Hüllkurven angeordnet werden.  
Dieses tool funktioniert nicht mit allen beliebigen Kurven. Die Parameter TwistReverse und ForceInterploate können das Ergebis evtl. verbessern.
 
![CurvedSegment](Examples/CurvedSegment.jpg)
![CurvedSegment2](Examples/CurvedSegment2.jpg)

Zuerst zwei 2D Kurven auswählen, dann optional noch eine oder mehrere Hüllkurven. Danach das Curved Segment Werkzeug verwenden. 

#### Parameters
- Shape1: Das erste Object des Segments
- Shape2: Das letzte Object des Segments
- Hullcurves: Keine, eine oder mehrere Hüllkurven. Alle Hüllkurven sollten in der XY, XZ oder YZ Raumebene liegen.   
- NormalShape1: Richtung, in der die Array Elemente von Shape1 aus aufgebaut werden (wird automatisch berechnet)
- NormalShape2: Richtung, in der die Array Elemente von Shape2 aus aufgebaut werden (wird automatisch berechnet)
- Items: Anzahl der Array Elemente
- makeSurface: Eine Oberfläche erstellen
- makeSolid: Einen Festkörper erstellen (funktioniert nur, wenn Base eine geschlossene Form ist)
- InterpolationPoints: Wenn Shape1 und Shape2 verschiedenartige Objekte sind, werden die Kurven in diese Anzahl von Einzelpunkten zerlegt  
- Twist: (Winkel in Grad) kann eine Rotation zwischen Shape1 unf Shape2 kompensieren
- TwistReverse: wenn True, wird die Drehrichtung geändert
- Distribution: Algorithmus zur Berechnung der Distanz zwischen den Elementen. Default ist 'linear'. Weitere Möglichkeiten: parabolic (x²), x³, sinusoidal, elliptic
- DistributionReverse: Kehrt die Richtung des Distrubution Algorithmus um
- LoftMaxDegree: Gradzahl für die Erstellung von Oberflächen und Festkörpern.
- MaxLoftSize: Maximale Anzahl von Elementen für die Erstellung von Oberfächen und Festkörpern
- Path: wird nur für Curved Path segment verwendet  


### ![](./Resources/icons/CurvedPathSegment.svg) Curved Path Segment
Interpoliert zwischen zwei 2D Kurven und ordnet diese rechwinklig zu einer Kurve (Path) an. Optional können Größe und Position innerhalb von einer oder mehreren Hüllkurven (Hullcurves) ausgerichtet werden. 

Zuerst zwei 2D Kurven auswählen, dann eine Kurve, die als Path verwendet wird, dann optional noch eine oder mehrere Hüllkurven. Danach das Curved Segment Werkzeug verwenden. 

#### Parameters
wie bei Curved Segment
- Path: Kurve, an der die Segmente rechtwinkling ausgerichtet werden.


### ![](./Resources/icons/CornerShape.svg) Interpolated Middle
Interpoliert eine 2D Kurve in der Mitte zwischen zwei 2D Kurven. Es kann ein Verbinder mit einem Knick zwischen den den Kurven generiert werden.

![InterpolatedMiddle2](Examples/InterpolatedMiddle2.jpg)
![InterpolatedMiddle](Examples/InterpolatedMiddle.jpg)
 
#### Parameters
- Shape1: Die erste 2D Kurve
- Shape2: Die zweite 2D Kurve     
- NormalShape1: Richtung, in der das Mittel Element von Shape1 aus aufgebaut wird (wird automatisch berechnet)
- NormalShape2: Richtung, in der das Mittel Element von Shape2 aus aufgebaut wird (wird automatisch berechnet)
- makeSurface: Eine Oberfläche erstellen
- makeSolid: Einen Festkörper erstellen (funktioniert nur, wenn Base eine geschlossene Form ist)
- InterpolationPoints: Wenn Shape1 und Shape2 verschiedenartige Objekte sind, werden die Kurven in diese Anzahl von Einzelpunkten zerlegt  
- Twist: (Winkel in Grad) kann eine Rotation zwischen Shape1 unf Shape2 kompensieren
- TwistReverse: wenn True, wird die Drehrichtung geändert
- Distribution: Algorithmus zur Berechnung der Distanz zwischen den Elementen. Default ist 'linear'. Weitere Möglichkeiten: parabolic (x²), x³, sinusoidal, elliptic
- DistributionReverse: Kehrt die Richtung des Distrubution Algorithmus um
- LoftMaxDegree: Gradzahl für die Erstellung von Oberflächen und Festkörpern. 
- MaxLoftSize: Maximale Anzahl von Elementen für die Erstellung von Oberfächen und Festkörpern  
  
  
### ![](./Resources/icons/surfaceCut.svg) Surface Cut
Generiert einen Schnitt durch eine oder mehrere Oberflächen. Das Tool versucht, sich überlappende Kanten zu entfernen.

![SurfaceCut](Examples/SurfaceCut.jpg)

#### Parameters
- Surfaces: Ein oder mehrere Oberflächenobjekte
- Normal:   Vector, der senkrecht auf der Schneidefläche steht
- Position: Position der Schneidefläche
- Face:     Den Oberflächenschnitt ausfüllen
- Simplify: Wenn > 0, wird eine Näherungskurve über die Oberfläche geleg. Dieser Wert bestimmt die Anzahl der Polstellen. Bei komplexen Oberflächen kann das die resultierende Schnittkurve drastisch vereinfachen und Rechenzeit reduzieren. In machen Fällen entsteht aber Murks.
  
  
### ![](./Resources/icons/NotchConnector.svg) Notch Connector
Schneidet Kerben in zwei sich überlagende Objekte, so dass diese zusammengesteckt werden können.
  
![NotchConnector](Examples/NotchConnector.jpg)  
  
Zuerst zwei sich überlagende Objekte in FreeCAD auswählen, dann Notch Connector auswählen. Es werden zwei NotchConnector Objekte erstellt.

#### Parameters
- Base:  		Erstes Objekt
- Tools: 		Zweites und optional noch mehrere Objekte 
- CutDirection: Schnittrichtung (wird automatisch berechnet). Bitte ändern, wenn der Schnitt in die falsche Richtung gemacht wird.
- CutDepth: 	Tiefe des Schnitts in Prozent
- ShiftLength:	Verschiebt Tools um ShiftLength und schneidet das von Base. Wenn ShiftLength ungleich 0, wird CutDepth ignoriert. 

## Beispiele
Beispiele zum Testen und zur Demonstration dieses Arbeitsbereichs. 

### ![](./Resources/icons/Horten_HIX.svg) Horten H IX
Ein Python Skript zum Generieren einer [Horten H IX (auch Horten Ho 229 genannt)](https://de.wikipedia.org/wiki/Horten_H_IX), ein Stealth Fighter aus dem 2. Weltkrieg, der seiner Zeit um Jahrzehnte voraus war.

### ![](./Resources/icons/FlyingWingS800.svg) Flying Wing S800 
Ein Python Skript, dass einen Nurflügler generiert. 
  
![S800](Examples/S800.jpg)

### ![FishingLure_Icon](./Resources/icons/FishingLure.svg) Fisch Köder

Dieses Beispiel demonstriert das PreserveAspectRatio property von CurvedArray. Es zeigt 5 curved arrays zum Vergleich.  
Als Basisobjekt wird ein Kreis verwendet. Mit PreservedAspectRatio = True bleibt der Kreis ein Kreis, mit False wird er zur Ellipse. 


![FishingLure](Examples/FishingLure.jpg)

### ![](./Resources/icons/Propeller.svg) Propeller
Ein dreiblättriger Propeller, erstellt mit Curved Rails Array. Vorder- und Hinterkante eines Blatts sind 3D Kurven, aus denen sich die Verdrehung des Blatts ergibt. Eine Skizze mit dickem Flügelprofil an der Nabe und eine mit dünnem an der Spitze liegen dort, wo die Rails sie berühren, die Profile dazwischen werden überblendet.

### Faster Better Corsair |JOKO ENGINEERING|
[!["FreeCAD Curved Surfaces Workbench in Action: Faster Better Corsair |JOKO ENGINEERING|"](http://img.youtube.com/vi/tjT9gt0dArQ/0.jpg)](http://www.youtube.com/watch?v=tjT9gt0dArQ "FreeCAD Curved Surfaces Workbench in Action: Faster Better Corsair |JOKO ENGINEERING|") 

## Diskussion
[offizeller Thread im FreeCAD Forum (englisch)](https://forum.freecadweb.org/viewtopic.php?f=8&t=36989)  
[Beitrag im FreeCAD Forum in Deutsch](https://forum.freecadweb.org/viewtopic.php?f=13&t=42684).

## Lizenz
GNU Lesser General Public License v3.0
