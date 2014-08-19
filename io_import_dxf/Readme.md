_Development Repository of DXF importer for Blender including DXF and .blend testfiles. Help out making the importer more realiable by posting your errors in the [issue tracker](https://bitbucket.org/treyerl/io_import_scene_dxf/issues?status=new&status=open) or in the [BlenderArtists thread](http://blenderartists.org/forum/showthread.php?323358-DXF-Importer)._

# Features v0.8.4
* __Blocks__ are being imported and are reflected in Blender as linked objects or optionally as group instances. For linked objects sub-blocks get parented to the main block. If a block contains mixed curve / mesh / surface / text / light entities, the different types are being imported to different objects that are being parented to the main block.
* __Layers__ are being reflected with "Blender-groups". Select an object and type Shift-G to select all objects within the same "Blender-Group" (they should call it category, because that's what it is). Anyhow as Blender supports "only" 20 layers and DXF files can have virtually an infinite amount of layers I think it's best users would select grouped objects as described and move them themselves to layers as they wish.
* __Speed__: Using as many generators instead of lists as possible minimizes memory consumption. Parts of the the underlying dxf library "dxfgrabber" are written in cython and can be compiled to platform specific modules.
* __DXF Attributes__: DXF specific attributes (e.g. `thickness`, `width` and `extrusion`) are taken into account to import geometry as precise as possible.
* __Geo Referencing__: If the pyproj library is available, the scene center will be converted to lat/lon taking into account re-centering of geometry. The origin/DXF coordinate system (SRID) must be specified. If you have a DXF file from QGIS or ArcGIS this option should be most likely set to WGS84. The destination/scene SRID is by default the same as the DXF SRID, but of course you can set it to your local coordinate system. If a scene has a SRID already, this option is not available and the DXF SRID MUST be specified, so that the DXF geometry can be aligned to the scene geometry. For the installation of pyproj see "Installation".

    ### [Options](https://bitbucket.org/repo/5M8eeg/images/616018241-0.8.4.jpg):
* import `TEXT` entities (`TEXT`, `MTEXT`)
* import `LIGHT` entity, incl. support for AutoCAD colors
* merge all entities of a layer into one object per a) Blender geometry type b) DXF geometry type
* export NURBS 3D geometry (`BODY`, `REGION`, `PLANESURFACE`, `SURFACE`, `3DSOLID`) to ACIS-Sat files, since this is the format AutoCAD stores to DXF. The user is being notified about the amount of stored .sat/.sab files (any comments on experience with other 3D packages than AutoCAD are very welcome).
* combine `Line` entities to Blender "POLY"-curves (= remove doubles)
* switch outliner display mode to GROUPS
* display BLOCK entities with bounding boxes (instead parenting them only to Empties)
* import BLOCK entities as linked objects or group instances (default = linked objects)
* import DXF file to a new scene
* center the imported geometry to the center of the scene; the offset information is stored as a custom property to the scene

    ### DXF entities being mapped to BLENDER CURVES:
* `LINE` as "POLYLINE"-curve
* `(LW)POLYLINE`, `(LW)POLYGON` as "POLYLINE"-curve if they have no bulges else as "BEZIER"-curve
* conversion to Blender's cubic "BEZIER"-curve of
    * quadratic `SPLINE`s and `(LW)POLYLINE`s
    * splines with degree > 3 are imported as polylines (so far).
    * `ARC`s, `CIRCLE`s and `ELLIPSE`s
    * polys with bulges (`(LW)POLYLINE`, `POLYGON`)
    * `HELIX`es (__3D__)

	### DXF entities being mapped to BLENDER MESHES:
* `MESH` is mapped to an mesh object with a SubD modifier, incl. edge crease
* `POLYFACE`s and `POLYMESH`es are imported to a mesh object
* `3DFACE`s, `SOLID`s, `POINT`s are imported into one combined mesh object per layer called _layername_3Dfaces_.

# Installation (User)
* download the latest `io_import_scene_dxf.zip` file from the [download section](https://bitbucket.org/treyerl/io_import_scene_dxf/downloads)
* in Blender go to File -> User Preferences -> Addons and click `Install from file` at the bottom and choose the downloaded zip file.
* optional 'pyproj': Download ([WIN](https://code.google.com/p/pyproj/downloads/list), [MAC](http://www.ia.arch.ethz.ch/wp-content/uploads/2013/11/pyproj.zip)) pyproj and copy it to *your AppData/ApplicationSupport Folder*/Blender/2.70/scripts/modules/

# Roadmap / Release Info

_version 1.0.0 should be able to import `ALL` DXF/AutoCAD information translatable in some way to Blender._

##0.9.x: Materials
_(surfaces attributes like color, hatches etc.)_

    * color to material map
    * hatches: dynamic generation of hatch-textures? procedural textures?
    * line colors and width to freestyle?

##0.8.x: Geometry:
    * blocks not reference by `INSERT`-entity but name starting with `*` (Dimensions)
    * text alignment attributes
    * bsplines with degree > 3? any test-files are welcome!
    * update option (?):
        * named entities (blocks) are imported but don't replace existing Blender objects with the same name
          but only update their geometry if it changed

###0.8.4
    * proper knot insertion: bsplines are now properly converted to cubic bezier splines
    * geo-referencing: if pyproj is available, the scene center will be converted to lat/lon taking
      into account re-centering of geometry. The origin/DXF coordinate system (SRID) must be specified. If you have a
      DXF file from QGIS or ArcGIS this option should be most likely set to WGS84. The destination/scene SRID
      is by default the same as the DXF SRID, but of course you can set it to your local coordinate system.
      If a scene has a SRID already, this option is not available and the DXF SRID MUST be specified, so that the DXF
      geometry can be aligned to the scene geometry.

###0.8.3
    * many bug fixes (better testing with test-script)
    * new option: switch display mode to "GROUPS" in outliner
    * new option: BLOCK entities with bounding boxes
    * new option: BLOCK representation as group instances (for INSERTs with sub-inserts and rows and cols)
    * new option: import dxf to a new scene
    * new option: center the imported geometry and set the offset information as custom properties in the scene
       The offset is stored as a custom property to the scene. The key of the property is called like
       "*name of the dxf file*_recenter" and the value is a [x,y,z] array. "lat"/"lon" georeferencing is not possible
       since DXF does not store a EPSG coordinate system reference. But if the users know the coordinate system of the
       DXF file they can convert the x,y,z offset to lat/lon/altitude ([duck it](https://duckduckgo.com)).
      DXF does not store any information about the projection of x,y to lat,lon = the user needs to convert x, y to lat, lon.
    * dxf file filter in the file browser
    * POINT entities get imported as Empties if the merge option is turned off
    * display errors as pop up message (for known errors)
    * block objects get copied with obj.copy() = not only the geometry is being cached, but the whole object
      = skips unnecessary calculation (especially for bounding boxes)

###0.8.2
    * added support for "width" attribute on curve types.
    * improved thickness attribute handling on curve types; tilt option is Z_UP (--> check for Blender bug), for better shading a Edge Split Modifier is being added if the curve has width AND thickness
    * added thickness on solids and traces
    * improved solids: upon self intersection two faces are created
    * added support for TRACE entity
    * better yet not perfect extrusion handling
    * added option to merge connecting LINE entities into polygons
    * INSERT col and row attributes are handled with array modifier (needs improvement on BLOCK entities: instead of Empty the parent should be a bounding box)
    * TEXT entity now uses plain_text() filter (no %%u and %%d symbols anymore)

###0.8.1 (Start of version_info:):
    * GUI options (for already existing functionality):
        * import text `True/False`
        * import lights `True/False`
        * export ACIS code for NURB types `True/False`
        * merge entities to Blender objects `True/False`
            * by layer
            * by layer and then by DXF entity type
    * extrusion z-value for 2D types and `INSERT` to x-mirror the entity (which will be excluded from merged entities)
    * using bmesh-layers/loops for crease information of `MESH`
    * more clear code structure and doc strings



###0.8.0:
    version of APR2014:
    * Added 3D, text (including attributes, no style), light types. Code restructuring since it grew and grew.
    * Much improved dxfgrabber library incl. some parts in Cython for speedup. Text, Style, Light, and some 3D types, especially ACIS geometry became feasible only because of the extended capabilities of dxfgrabber.
    * Tackled DXF Sample Files from [CADKit](http://www.cadkit.net/2012/01/sample-dxf-files.html):
        * introducing some hacks and bug-fixes; bsplines with order higher > 4 will be most likely be imported as straight polylines
        * introduced merged entities; especially with `3DFACE`s this lead to massive speed improvements.
    * added License information: GPL


###0.1.0:
    version of JAN2014 was only able to import 2D curves. no 3D information. But Blocks got mapped to linked objects already and layers to groups.

# Installation (Development)
* copy/clone this repository to [Blender's addon folder](https://www.google.ch/search?client=safari&rls=en&q=blender+python+modules&ie=UTF-8&oe=UTF-8&gfe_rd=cr&ei=cvJpU6yAI6LC8gfB7IDICA#q=Configuration+%26+Data+Paths+-+Blender+Wiki&rls=en)
* download the latest version of [dxfgrabber](https://bitbucket.org/mozman/dxfgrabber) and copy its dxfgrabber folder into the this repository.
* in Blender go to File -> User Preferences -> Addons and search for "dxf" and activate the dxf import addon (there might be an old addon with an exlamation mark, don't activate that one)
* test it with the supplied testfiles and the [DXF sample files from cadkit.net](http://www.mediafire.com/?pcq6a8pbsiz6paw)

### Development on a mac
It helps to start Blender from the Terminal because that’s where the python print statements go.

1. right-click on the Blender-icon and select show package contents 
2. navigate to Contents/MacOS/ 
3. either double-click on "blender" or drag and drop it to a Terminal window