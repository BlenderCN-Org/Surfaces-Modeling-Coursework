# Project00-Curves: Curves Editor

In this project, we will develop a modal Blender add-on for the creation, manipulation, and committing of curve surfaces.

The project will involve many parts, many of which will be done individually but some may require small groups.
Each student will participate by being the "owner" of at least one particular feature.
Other students will assist the owner by reporting bugs, requesting features, or providing patches.



## Features


Below is a base list of features for the project.
In its current form, it is below the bare minimum.
Over the course of the project, this list will be expanded to describe a full-featured curve editor.

- manipulation of control points (hunter)
    - picking control point
    - translate wrt viewport
    - translate wrt major axes
    - more?
- cubic bezier curve (justin)
    - init: four control points
    - operations / properties:
        - manipulate
        - extend curve segment (creating spline)
        - add independent curve segment (not attached)
        - extend curve segment from middle (creating fork)
        - more?
    - draw
        - simple (points, lines between ctrl pts)
    - generate actual mesh
- extrude (bryant) -> sweep -> loft/tentacles
    - init: two curves (one is cross section, one is path of extrusion)
    - operations / properties:
        - manipulate
        - extend either curve segment (creating spline)
        - more?
    - draw
    - generate
- routing (ryan)
    - init: curve
    - operations / properties:
        - manipulate
        - extend curve segment (creating spline)
        - more?
    - draw
    - generate
- patches (david)
    - init: 16 control points
    - operations / properties:
        - manipulate
        - extend edge (creating adjacent patch)
        - more?
    - draw
    - generate

