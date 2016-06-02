""" Cubic Bezier curve generator
	Justin Powell
	COS424: Surfaces and Modeling """

import bpy
import bmesh
import bgl
import math
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_vector_3d
from bpy_extras.view3d_utils import region_2d_to_location_3d, region_2d_to_origin_3d
from mathutils import Vector, Matrix

from .modaloperator import ModalOperator

from .common import bezier_cubic_eval as curve_eval
from .common import bezier_cubic_eval_derivative as curve_der

class OP_CubicBezier(ModalOperator):
	bl_idname = 'cos424.cubicbezier'
	bl_label = 'COS424: Cubic Bezier'
	bl_options = {'REGISTER', 'UNDO'}

	def __init__(self):
		FSM = {}
		self.initialize(FSM)
		
		self.cntrlList = []
		self.curvePoints = []
		self.selectCntrl = []
		
		self.tesselate = 20
	
	def buildMesh(self, points, obj_name = 'obj'):
		bm = bmesh.new()
		bmv = [bm.verts.new(p) for p in points]
		bme = []
		for i in range(len(points)-1):
			bme.append(bm.edges.new((bmv[i], bmv[i+1])))

		me = bpy.data.meshes.new(obj_name)
		ob = bpy.data.objects.new(obj_name, me)
		bm.to_mesh(me)
		me.update()

		bpy.context.scene.objects.link(ob)
		ob.update_tag()
		bpy.context.scene.update()
		ob.select = True

		return ob

	def start(self, context):
		''' Called when tool has been invoked '''
		# Add initial points
		print(self.cntrlList)
		self.setControlPoints([Vector((0, -1, 0)), Vector((0, -.50, 1)), Vector((0, .50, 1)), Vector((0, 1, 0))])
		self.selectCntrl += [self.cntrlList[0]]

		# Calculate curve
		self.curvePoints = self.calculateCurve()
	
	def end(self, context):
		''' Called when tool is ending modal '''
		pass
		
	
	def end_commit(self, context):
		''' Called when tool is committing '''
		self.buildMesh(self.curvePoints)
	
	def end_cancel(self, context):
		''' Called when tool is canceled '''
		pass

	def update(self, context):
		''' Called when data is changed '''
		self.curvePoints = self.calculateCurve()
	
	def draw_postview(self, context):
		''' Place drawing code in here '''
		#--------------------------------------------------------------------#
		#Draw control Points

		bgl.glEnable(bgl.GL_POINT_SMOOTH)
		bgl.glColor3d(1, 0, 0)
		bgl.glPointSize(5)
		bgl.glBegin(bgl.GL_POINTS)
		
		for i in range(len(self.cntrlList)):
			tup = self.cntrlList[i].to_tuple()
			bgl.glVertex3f(tup[0], tup[1], tup[2])

		bgl.glEnd()
		'''
		bgl.glLineWidth(1)
		bgl.glColor3f(0,0,0)
		bgl.glBegin(bgl.GL_LINES)

		for i in range(len(self.cntrlList)):
			tup = self.cntrlList[i].to_tuple()
			bgl.glVertex3f(tup[0], tup[1], tup[2])

		bgl.glEnd()
		'''
		#--------------------------------------------------------------------#
		#Draw Lines between Control Points

		self.drawCurvePoints()
			
	def modal_wait(self, eventd):
		return ''
		
