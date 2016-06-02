#David Nurkkala

import bgl
import math
import bmesh
import bpy

from mathutils import Vector, Matrix
from .modaloperator import ModalOperator
from .common import bernstein_cubic
from bpy.props import IntProperty

class OP_PatchEditor(ModalOperator):
	bl_idname	= "cos424.patcheditor"
	bl_label	= "COS424: Patch Editor"
	bl_options	= {"REGISTER", "UNDO"}

	mesh_tesselation = IntProperty(name="Mesh Tesselation", default=32, min=0, max=256)

	def __init__(self):
		self.cntrlList = []

		self.visualization = []
		self.visualizationTesselation = 8

		self.matrix = []
		self.matrix.append([0, 1, 2, 3])
		self.matrix.append([4, 5, 6, 7])
		self.matrix.append([8, 9, 10, 11])
		self.matrix.append([12, 13, 14, 15])

		FSM = {}

		self.initialize(FSM)
	
	def create(self, data):
		lp, lf = data
		bme = bmesh.new()
		bmv = [bme.verts.new(p) for p in lp]
		bmf = [bme.faces.new(bmv[i] for i in f) for f in lf]

		me = bpy.data.meshes.new('obj')
		ob = bpy.data.objects.new('obj', me)
		bme.to_mesh(me)
		me.update()

		bpy.context.scene.objects.link(ob)
		ob.update_tag()
		bpy.context.scene.update()
		ob.select = True

		return ob
	
	def update(self, eventd):
		self.visualization = []
		tess = self.visualizationTesselation

		for x in range(tess+1):
			for y in range(tess+1):
				v = self.calculate(x/tess, y/tess).to_tuple()
				self.visualization.append(v)
	
	def calculate(self, x, y):
		point = Vector((0, 0, 0))
		for i in range(4):
			for j in range(4):
				point += bernstein_cubic(i, x) * bernstein_cubic(j, y) * self.cntrlList[i*4+j]

		return point
	
	def start(self, context):
		self.cntrlList = []

		minX = -1.5
		maxX = 1.5
		minY = -1.5
		x = minX
		y = minY
		for index in range(16):
			self.cntrlList.append(Vector((x, y, 0)))

			x = x + 1
			if x > maxX:
				x = minX
				y = y + 1

		self.update({})
	
	def end(self, context):
		pass
	
	def end_commit(self, context):
		lp = []
		lf = []
		index = 0
		
		tesselation = 32
		for x in range(tesselation+1):
			for y in range(tesselation+1):
				lp.append(self.calculate(x/tesselation, y/tesselation).to_tuple())
				index += 1

		#tesselation + 1 indices by tesselation + 1 indices
		
		for offset in range(tesselation):
			for i in range(tesselation):
				index = offset * (tesselation + 1) + i
				a = index
				b = index + 1
				c = index + tesselation + 2
				d = index + tesselation + 1
				lf.append((a, b, c, d))
		
		self.create((lp, lf))

		return {"FINISHED"}
	
	def end_cancel(self, context):
		pass
	
	def draw_postview(self, context):
		bgl.glEnable(bgl.GL_POINT_SMOOTH)
		bgl.glEnable(bgl.GL_BLEND)
		
		#draw the visualization lines
		bgl.glColor3d(0, 0.5, 0)
		bgl.glBegin(bgl.GL_LINES)

		tess = self.visualizationTesselation
		for offset in range(tess):
			for i in range(tess):
				index = offset * (tess + 1) + i
				a = self.visualization[index]
				b = self.visualization[index + 1]
				c = self.visualization[index + tess + 2]
				d = self.visualization[index + tess + 1]
				for point in [a, b, b, c, c, d, d, a]:
					x, y, z = point
					bgl.glVertex3f(x, y, z)

		bgl.glEnd()

		#draw points
		bgl.glPointSize(2)
		bgl.glColor3d(0, 1, 0)
		bgl.glBegin(bgl.GL_POINTS)

		#draw the visualization points
		for v in self.visualization:
			x, y, z = v
			bgl.glVertex3f(x, y, z)

		bgl.glEnd()
		

		bgl.glColor3d(1, 1, 0)
		bgl.glPointSize(5)
		bgl.glBegin(bgl.GL_POINTS)

		#draw the control points
		for index in range(16):
			x, y, z = self.cntrlList[index].to_tuple()
			bgl.glVertex3f(x, y, z)

		bgl.glEnd()

		#draw triangls
		bgl.glColor4f(0, 0, 1, 0.25)
		bgl.glBegin(bgl.GL_TRIANGLES)

		for offset in range(tess):
			for i in range(tess):
				index = offset * (tess + 1) + i
				a = self.visualization[index]
				b = self.visualization[index + 1]
				c = self.visualization[index + tess + 2]
				d = self.visualization[index + tess + 1]
				
				bgl.glVertex3f(*a)
				bgl.glVertex3f(*b)
				bgl.glVertex3f(*c)

				bgl.glVertex3f(*a)
				bgl.glVertex3f(*d)
				bgl.glVertex3f(*c)

		bgl.glEnd()

	
	def modal_wait(self, eventd):
		return ''
