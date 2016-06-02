'''
Copyright (C) 2015 Taylor University

Created by Dr. Jon Denning and Spring 2015 COS 424 class

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {
    "name":         "Curves Editor (COS424: Surfaces and Modeling, Spring 2015)",
    "description":  "This modal add-on will provide a mechanism for editing curve surfaces.",
    "author":       "Dr. Jon Denning, Spring 2015 COS 424 Class",
    "version":      (1, 0),
    "blender":      (2, 73, 0),
    "location":     "View3D > Add > Mesh",
    "warning":      "", # used for warning icon and text in addons panel
    "wiki_url":     "",
    "category":     "Add Mesh"
}

from bpy.utils import register_class, unregister_class

from .op_curveeditor import OP_CurveEditor
from .op_extrude_editor2 import OP_ExtrudeEditor2
from .op_routing import OP_Routing
from .op_cubic_bezier import OP_CubicBezier
from .op_patch_editor import OP_PatchEditor
from .op_extrude_editor import OP_ExtrudeEditor

def register():
    '''
    tell Blender what operators, menus, properties, etc. need to be registered
    '''
    
    register_class(OP_CurveEditor)
    register_class(OP_ExtrudeEditor2)
    register_class(OP_Routing)
    register_class(OP_CubicBezier)
    register_class(OP_PatchEditor)
    register_class(OP_ExtrudeEditor)

def unregister():
    '''
    unregister everything from register(), but in REVERSE order
                                                  ^^^^^^^
    '''
    unregister_class(OP_CubicBezier)
    unregister_class(OP_Routing)
    unregister_class(OP_CurveEditor)
    unregister_class(OP_ExtrudeEditor2)
    unregister_class(OP_PatchEditor)
    unregister_class(OP_ExtrudeEditor)
