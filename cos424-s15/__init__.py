import bpy
from bpy.utils import register_class, unregister_class
from bpy.types import Operator, Panel
from bpy.props import IntProperty
from .shapes import *

bl_info = {
	"name":			"Surfaces and Modeling (COS 424, Spring 2015)",
	"description":	"This add-on will do some amazing things in Blender.",
	"author":		"Dr. Jon Denning, Spring 2015 COS 424 Class",
	"version":		(1, 0),
	"blender":		(2, 73, 0),
	"location":		"View3D > Add > Mesh",
	"warning":		"",
	"wiki_url":		"",
	"category":		"Add Mesh"
}

class OP_ObjectCursorArray(Operator):
	bl_idname = "cos424.cursor_array"
	bl_label = "COS424: Cursor Array"
	bl_options = {'REGISTER', 'UNDO'}

	total = IntProperty(name="Steps", default=2, min=1, max=100)

	@classmethod
	def poll(cls, context):
		return context.object and context.object.type == 'MESH'
	
	def execute(self, context):
		scene = context.scene
		cursor = scene.cursor_location
		obj = scene.objects.active

		for i in range(self.total):
			obj_new = obj.copy()
			scene.objects.link(obj_new)

			factor0 = i / self.total
			factor1 = 1.0 - factor0
			obj_new.location = (obj.location*factor0) + (cursor*factor1)
	
		return {'FINISHED'}
		
class OT_COS424Tools(Panel):
	bl_space_type = "VIEW_3D"
	bl_region_type = "TOOLS"
	bl_category = "COS 424"
	bl_label = "My Tools"
	
	def draw(self, context):
		layout = self.layout
		col = layout.column(align=True)
		col.operator("cos424.cursor_array")
		col.operator("cos424.cube")
		col.operator("cos424.cylinder")
		col.operator("cos424.tetrahedron")
		col.operator("cos424.octahedron")
		col.operator("cos424.ico_sphere")
		
class OP_COS424Cube(Operator):
	bl_idname = "cos424.cube"
	bl_label = "COS424: Cube"
	bl_options = {'REGISTER', 'UNDO'}
	
	size = IntProperty(name="Size", default=2, min=1, max=100)
	
	def execute(self, context):
		scene = context.scene
		cursor = scene.cursor_location
		
		shapes.spawn_obj(2, 'cube', cursor, self.size)
		
		return {'FINISHED'}

class OP_COS424Cylinder(Operator):
	bl_idname = "cos424.cylinder"
	bl_label = "COS424: Cylinder"
	bl_options = {'REGISTER', 'UNDO'}
	
	radius = IntProperty(name="Radius", default=1, min=1, max=100)
	height = IntProperty(name="Height", default=2, min=1, max=100)
	
	def execute(self, context):
		scene = context.scene
		cursor = scene.cursor_location
		
		shapes.spawn_obj(4, 'cylinder', cursor, self.radius, self.height)
		
		return {'FINISHED'}
		
class OP_COS424Tetrahedron(Operator):
	bl_idname = "cos424.tetrahedron"
	bl_label = "COS424: Tetrahedron"
	bl_options = {'REGISTER', 'UNDO'}
	
	radius = IntProperty(name="Radius", default=2, min=1, max=100)
	
	def execute(self, context):
		scene = context.scene
		cursor = scene.cursor_location
		
		shapes.spawn_obj(3, 'Tetrahedron', cursor, self.radius)
		
		return {'FINISHED'}
		
class OP_COS424Octahedron(Operator):
	bl_idname = "cos424.octahedron"
	bl_label = "COS424: Octahedron"
	bl_options = {'REGISTER', 'UNDO'}
	
	radius = IntProperty(name="Radius", default=2, min=1, max=100)
	
	def execute(self, context):
		scene = context.scene
		cursor = scene.cursor_location
		
		shapes.spawn_obj(6, 'Octahedron', cursor, self.radius)
		
		return {'FINISHED'}
		
class OP_COS424ICO_Sphere(Operator):
	bl_idname = "cos424.ico_sphere"
	bl_label = "COS424: ICO Sphere"
	bl_options = {'REGISTER', 'UNDO'}
	
	radius = IntProperty(name="Radius", default=2, min=1, max=100)
	
	def execute(self, context):
		scene = context.scene
		cursor = scene.cursor_location
		
		shapes.spawn_obj(9, 'ICO_Sphere', cursor, self.radius)
		
		return {'FINISHED'}

def register():
	register_class(OP_ObjectCursorArray)
	register_class(OT_COS424Tools)
	
	register_class(OP_COS424Cube)
	register_class(OP_COS424Cylinder)
	register_class(OP_COS424Tetrahedron)
	register_class(OP_COS424Octahedron)
	register_class(OP_COS424ICO_Sphere)

def unregister():
	unregister_class(OP_COS424ICO_Sphere)
	unregister_class(OP_COS424Octahedron)
	unregister_class(OP_COS424Tetrahedron)
	unregister_class(OP_COS424Cylinder)
	unregister_class(OP_COS424Cube)
	
	unregister_class(OT_COS424Tools)
	unregister_class(OP_ObjectCursorArray)
	
if __name__ == "__main__":
	register()
