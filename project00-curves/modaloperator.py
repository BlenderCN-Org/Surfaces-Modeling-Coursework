'''
Copyright (C) 2015 Taylor University, CG Cookie

Created by Dr. Jon Denning and Spring 2015 COS 424 class

Some code copied from CG Cookie Retopoflow project
https://github.com/CGCookie/retopoflow

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

import bpy
import bgl

from bpy.types import Operator
from bpy.types import SpaceView3D
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_vector_3d
from bpy_extras.view3d_utils import region_2d_to_location_3d, region_2d_to_origin_3d
from mathutils import Vector, Matrix

from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_vector_3d
from bpy_extras.view3d_utils import region_2d_to_location_3d, region_2d_to_origin_3d

from mathutils import Vector, Matrix

from .common import bezier_cubic_eval as curve_eval
from .common import bezier_cubic_eval_derivative as curve_der


class ModalOperator(Operator):
	events_numpad = {
		'NUMPAD_1',       'NUMPAD_2',       'NUMPAD_3',
		'NUMPAD_4',       'NUMPAD_5',       'NUMPAD_6',
		'NUMPAD_7',       'NUMPAD_8',       'NUMPAD_9',
		'CTRL+NUMPAD_1',  'CTRL+NUMPAD_2',  'CTRL+NUMPAD_3',
		'CTRL+NUMPAD_4',  'CTRL+NUMPAD_5',  'CTRL+NUMPAD_6',
		'CTRL+NUMPAD_7',  'CTRL+NUMPAD_8',  'CTRL+NUMPAD_9',
		'SHIFT+NUMPAD_1', 'SHIFT+NUMPAD_2', 'SHIFT+NUMPAD_3',
		'SHIFT+NUMPAD_4', 'SHIFT+NUMPAD_5', 'SHIFT+NUMPAD_6',
		'SHIFT+NUMPAD_7', 'SHIFT+NUMPAD_8', 'SHIFT+NUMPAD_9',
		'NUMPAD_PLUS', 'NUMPAD_MINUS', # CTRL+NUMPAD_PLUS and CTRL+NUMPAD_MINUS are used elsewhere
		'NUMPAD_PERIOD',
	}
	
	initialized = False
	
	def initialize(self, FSM=None):
		# make sure that the appropriate functions are defined!
		# note: not checking signature, though :(
		dself = dir(self)
		dfns = {
			'draw_postview':    'draw_postview(self,context)',
			'modal_wait':       'modal_wait(self,eventd)',
			'start':            'start(self,context)',
			'end':              'end(self,context)',
			'end_commit':       'end_commit(self,context)',
			'end_cancel':       'end_cancel(self,context)',
			'update':           'update(self,context)',
		}
		for fnname,fndef in dfns.items():
			assert fnname in dself, 'Must define %s function' % fndef
		
		self.cntrlList = []
		self.selectCntrl = []

		self.FSM = {} if not FSM else dict(FSM)
		self.FSM['main'] = self.modal_main
		self.FSM['nav']  = self.modal_nav
		self.FSM['manipulate'] = self.modal_manipulate
		self.FSM['scale'] = self.modal_scale
		self.FSM['wait'] = self.modal_wait
		
		self.initialized = True
		
		self.numExten = 1
	
	'''Call This ez to use function for all your basic bezier curve needs. Give this function 4 
	   control points and it will automagically calculate the curve for you. It will return the list of calculated points'''
	def makeBezier(self, ctrlList):
		self.setControlPoints(ctrlList)
		return self.calculateCurve()

	def setControlPoints(self, cntrlList):
		self.cntrlList = cntrlList

	def calculateCurve(self):
		curvePoints = []
		cp = self.cntrlList
		if (len(self.cntrlList) == 4):
			for i in range(self.tesselate+1):
				curvePoints.append(curve_eval(cp[0], cp[1], cp[2], cp[3], i*(1/self.tesselate)))
		else:
			for i in range(((len(self.cntrlList)+self.numExten)//4)):
				for j in range(self.tesselate+1):
					point = curve_eval(cp[0+(i*3)], cp[1+(i*3)], cp[2+(i*3)], cp[3+(i*3)], j*(1/self.tesselate))
					#print(0+(i*3), 1+(i*3), 2+(i*3), 3+(i*3))
					if point not in curvePoints:
						curvePoints.append(point)
		return curvePoints
		
	def extend(self):
		self.numExten = self.numExten + 1
		extension = []
		start = self.cntrlList[len(self.cntrlList)-1]
		for i in range(1,4):
			point = Vector((start[0], start[1]+(i*.5), start[2]))
			extension.append(point)
			
		self.cntrlList += extension
		self.curvePoints = self.calculateCurve()
	
	def removeExtension(self):
		if(self.numExten > 1):
			self.numExten = self.numExten - 1
			for i in range(3):
				self.cntrlList.pop()
			self.curvePoints = self.calculateCurve()

	def drawCurvePoints(self):
		#Draw Lines between Control Points

		bgl.glEnable(bgl.GL_POINT_SMOOTH)
		bgl.glColor3d(0,1,0)
		bgl.glPointSize(3)
		bgl.glBegin(bgl.GL_POINTS)

		for i in range(len(self.curvePoints)):
			tup = self.curvePoints[i].to_tuple()
			bgl.glVertex3f( *tup )
		bgl.glEnd()

		bgl.glLineWidth(1)
		bgl.glColor3f(0,.5,0)
		bgl.glBegin(bgl.GL_LINES)
		'''
		for i in range(0, len(self.curvePoints)-1):
			if i%(self.tesselate+1) != self.tesselate:
				tup = self.curvePoints[i]
				tup1 = self.curvePoints[i+1]
				bgl.glVertex3f( *tup )
				bgl.glVertex3f( *tup1 )
		'''
		for i in range(0, len(self.curvePoints)-1):
			tup = self.curvePoints[i].to_tuple()
			tup1 = self.curvePoints[i+1].to_tuple()
			bgl.glVertex3f(tup[0], tup[1], tup[2])
			bgl.glVertex3f(tup1[0], tup1[1], tup1[2])
		bgl.glEnd()

	def get_event_details(self, context, event):
		'''
		Construct an event dictionary that is *slightly* more
		convenient than stringing together a bunch of logical
		conditions
		'''

		event_ctrl  = 'CTRL+'  if event.ctrl  else ''
		event_shift = 'SHIFT+' if event.shift else ''
		event_alt   = 'ALT+'   if event.alt   else ''
		event_oskey = 'OSKEY+' if event.oskey else ''
		event_ftype = event_ctrl + event_shift + event_alt + event_oskey + event.type

		event_pressure = 1 if not hasattr(event, 'pressure') else event.pressure

		return {
			'context': context,
			'region':  context.region,
			'r3d':     context.space_data.region_3d,

			'ctrl':    event.ctrl,
			'shift':   event.shift,
			'alt':     event.alt,
			'value':   event.value,
			'type':    event.type,
			'ftype':   event_ftype,
			'press':   event_ftype if event.value=='PRESS'   else None,
			'release': event_ftype if event.value=='RELEASE' else None,

			'mouse':   (float(event.mouse_region_x), float(event.mouse_region_y)),
			'pressure': event_pressure,
			}

	####################################################################
	# Draw handler function

	def draw_callback_postview(self, context):
		bgl.glPushAttrib(bgl.GL_ALL_ATTRIB_BITS)    # save OpenGL attributes
		self.draw_postview(context)
		if len(self.selectCntrl):
			cntrlLength = len(self.selectCntrl)
			for x in range(0,cntrlLength):
				# assuming that we have only one control point, so if
				# anything is selected it would be the only point
				p111 = self.selectCntrl[x]
				t111 = p111.to_tuple()
				vrot = context.space_data.region_3d.view_rotation
				dx = (vrot * Vector((1,0,0))).normalized()          # compute right dir relative to view
				dy = (vrot * Vector((0,1,0))).normalized()          # compute up dir relative to view
				px = tuple(p111 + dx*0.5)
				py = tuple(p111 + dy*0.5)

				# highlight the point
				bgl.glColor3f(1,1,0)
				bgl.glBegin(bgl.GL_POINTS)
				bgl.glVertex3f(*t111)
				bgl.glEnd()

				# draw lines to indicate right (red) and up (green)
				bgl.glBegin(bgl.GL_LINES)
				bgl.glColor3f(1,0,0)
				bgl.glVertex3f(*t111)
				bgl.glVertex3f(*px)
				bgl.glColor3f(0,1,0)
				bgl.glVertex3f(*t111)
				bgl.glVertex3f(*py)
				bgl.glEnd()
		bgl.glPopAttrib()                           # restore OpenGL attributes


	####################################################################
	# FSM modal functions

	def modal_nav(self, eventd):
		'''
		Determine/handle navigation events.
		FSM passes control through to underlying panel if we're in 'nav' state
		'''

		handle_nav = False
		handle_nav |= eventd['type'] == 'MIDDLEMOUSE'
		handle_nav |= eventd['type'] == 'MOUSEMOVE' and self.is_navigating
		handle_nav |= eventd['type'].startswith('NDOF_')
		handle_nav |= eventd['type'].startswith('TRACKPAD')
		handle_nav |= eventd['ftype'] in self.events_numpad
		handle_nav |= eventd['ftype'] in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}

		if handle_nav:
			self.post_update   = True
			self.is_navigating = True
			return 'nav' if eventd['value']=='PRESS' else 'main'

		self.is_navigating = False
		return ''

	def modal_main(self, eventd):
		'''
		Main state of FSM.
		This state checks if navigation is occurring.
		This state calls auxiliary wait state to see into which state we transition.
		'''

		# handle general navigationvrot = context.space_data.region_3d.view_rotation
		nmode = self.FSM['nav'](eventd)
		if nmode:
			return nmode

		# accept / cancel
		if eventd['press'] in {'RET', 'NUMPAD_ENTER'}:
			# commit the operator
			# (e.g., create the mesh from internal data structure)
			return 'finish'
		if eventd['press'] in {'ESC'}:
			# cancel the operator
			return 'cancel'
		if eventd['press'] in {'RIGHTMOUSE'}:
			''' handle picking '''
			# eventd['mouse'] contains x,y of mouse in region space
			# eventd['shift'] states if shift is being held
			# To convert 3D point to 2D location in region space:
			#   p3d = Vector((1,1,1))
			#   p2d = location_3d_to_region_2d(eventd['region'], eventd['r3d'], p3d)

			# sample code to pick the (1,1,1) corner
			m2d = Vector(eventd['mouse'])

			while (len(self.selectCntrl) != 0):
				self.selectCntrl.pop()
			for pt in self.cntrlList:
				p3d = pt
				p2d = location_3d_to_region_2d(eventd['region'], eventd['r3d'], p3d)
				if ((p2d-m2d).length < 10):
					self.selectCntrl.append(pt)
			#print (self.selectCntrl)

			return ''

		if eventd['press'] in {'SHIFT+RIGHTMOUSE'}:
			''' handle picking '''
			# eventd['mouse'] contains x,y of mouse in region space
			# eventd['shift'] states if shift is being held
			# To convert 3D point to 2D location in region space:
			#   p3d = Vector((1,1,1))
			#   p2d = location_3d_to_region_2d(eventd['region'], eventd['r3d'], p3d)

			# sample code to pick the (1,1,1) corner
			m2d = Vector(eventd['mouse'])
			for pt in self.cntrlList:
				p3d = pt
				p2d = location_3d_to_region_2d(eventd['region'], eventd['r3d'], p3d)
				if ((p2d-m2d).length < 10):
					if(len(self.selectCntrl) != 0):
						double = False
						for test in self.selectCntrl:
							if (test == pt):
								double = True
						if(double == False):
							self.selectCntrl.append(pt)
						else:
							self.selectCntrl.remove(pt)
					else:
						self.selectCntrl.append(pt)
			#print (self.selectCntrl)
			return ''

		if self.selectCntrl and eventd['press'] in {'G'}:
			self.grabstart = Vector(eventd['mouse'])
			self.constraint = Vector((1,1,1))
			self.planeConstraint = 'A'
			self.orig = []
			for index in range(0,len(self.selectCntrl)):
				self.orig.append(Vector(self.selectCntrl[index]))
			return 'manipulate'

		if self.selectCntrl and eventd['press'] in {'S'}:
			self.scalestart = Vector(eventd['mouse'])
			self.sconstraint = Vector((1,1,1))
			self.splaneConstraint = 'A'
			self.orig = []
			tempx = 0
			tempy = 0
			tempz = 0
			for index in range(0,len(self.selectCntrl)):
				tempx += self.selectCntrl[index].x
				tempy += self.selectCntrl[index].y
				tempz += self.selectCntrl[index].z
				self.orig.append(Vector(self.selectCntrl[index]))
			self.center = Vector((tempx/len(self.selectCntrl),tempy/len(self.selectCntrl),tempz/len(self.selectCntrl)))
			return 'scale'

		if self.selectCntrl and eventd['press'] in {'X','SHIFT+X','Y','SHIFT+Y','Z','SHIFT+Z'}:
			v = 0.1
			if eventd['press'] == 'X':
				for ind in self.selectCntrl:
					p111 = ind
					p111.x += v
			if eventd['press'] == 'Y':
				for ind in self.selectCntrl:
					p111 = ind
					p111.y += v
			if eventd['press'] == 'Z':
				for ind in self.selectCntrl:
					p111 = ind
					p111.z += v
			if eventd['press'] == 'SHIFT+X':
				for ind in self.selectCntrl:
					p111 = ind
					p111.x -= v
			if eventd['press'] == 'SHIFT+Y':
				for ind in self.selectCntrl:
					p111 = ind
					p111.y -= v
			if eventd['press'] == 'SHIFT+Z':
				for ind in self.selectCntrl:
					p111 = ind
					p111.z -= v
			self.update(eventd['context'])
			return ''
		
		# handle general waiting
		nmode = self.FSM['wait'](eventd)
		if nmode:
			return nmode
		
		#Change Bezier tesselation
		if eventd['press'] in {'LEFT_ARROW', 'RIGHT_ARROW', 'R', 'SHIFT+R'}:
			if eventd['press'] == 'LEFT_ARROW':     self.tesselate -= 1
			if eventd['press'] == 'RIGHT_ARROW':    self.tesselate += 1
			if eventd['press'] == 'R': self.extend()
			if eventd['press'] == 'SHIFT+R': self.removeExtension()
			if self.tesselate < 3:
				self.tesselate = 3
			self.update(eventd['context'])
		return ''

	def modal_manipulate(self, eventd):
		grabend = Vector(eventd['mouse'])
		delta = grabend - self.grabstart
		vrot = eventd['context'].space_data.region_3d.view_rotation
		dx = (vrot * Vector((1,0,0))).normalized()
		dy = (vrot * Vector((0,1,0))).normalized()
		dg = (dx*delta.x+dy*delta.y)*.01
		if eventd['press']  == 'X':
			if self.planeConstraint != 'X':
				self.constraint = Vector((1,0,0))
				self.planeConstraint = 'X'
			else:
				self.constraint = Vector((1,1,1))
				self.planeConstraint ='A'
		if eventd['press']  == 'Y':
			if self.planeConstraint != 'Y':
				self.constraint = Vector((0,1,0))
				self.planeConstraint = 'Y'
			else:
				self.constraint = Vector((1,1,1))
				self.planeConstraint ='A'
		if eventd['press']  == 'Z':
			if self.planeConstraint != 'Z':
				self.constraint = Vector((0,0,1))
				self.planeConstraint = 'Z'
			else:
				self.constraint = Vector((1,1,1))
				self.planeConstraint ='A'
		if eventd['press']  == 'SHIFT+X':
			if self.planeConstraint != 'YZ':
				self.constraint = Vector((0,1,1))
				self.planeConstraint = 'YZ'
			else:
				self.constraint = Vector((1,1,1))
				self.planeConstraint ='A'
		if eventd['press']  == 'SHIFT+Y':
			if self.planeConstraint != 'XZ':
				self.constraint = Vector((1,0,1))
				self.planeConstraint = 'XZ'
			else:
				self.constraint = Vector((1,1,1))
				self.planeConstraint ='A'
		if eventd['press']  == 'SHIFT+Z':
			if self.planeConstraint != 'XY':
				self.constraint = Vector((1,1,0))
				self.planeConstraint = 'XY'
			else:
				self.constraint = Vector((1,1,1))
				self.planeConstraint ='A'
		for index in range(0,len(self.selectCntrl)):
			self.selectCntrl[index].x = self.orig[index].x + dg.x*self.constraint.x
			self.selectCntrl[index].y = self.orig[index].y + dg.y*self.constraint.y
			self.selectCntrl[index].z = self.orig[index].z + dg.z*self.constraint.z
		self.update(eventd['context'])
		if eventd['press'] == 'LEFTMOUSE':
			return 'wait'
		if eventd['press'] in {'ESC','RIGHTMOUSE'}:
			for index in range(0,len(self.selectCntrl)):
				self.selectCntrl[index].x = self.orig[index].x
				self.selectCntrl[index].y = self.orig[index].y
				self.selectCntrl[index].z = self.orig[index].z
			self.update(eventd['context'])
			return 'wait'
		return ''

	def modal_scale(self, eventd):
		scaleend = Vector(eventd['mouse'])
		scaverage = location_3d_to_region_2d(eventd['region'], eventd['r3d'], self.center)
		# vrot = eventd['context'].space_data.region_3d.view_rotation
		# dx = (vrot * Vector((1,0,0))).normalized()
		# dy = (vrot * Vector((0,1,0))).normalized()
		# dg = (dx*scaleend.x+dy*scaleend.y)*.01
		# dcg = (dx*self.scalestart.x+dy*self.scalestart.y)*.01
		# self.cdelta = dcg - self.center
		# delta = dg - self.center
		self.cdelta = (self.scalestart - scaverage).length
		delta = (scaleend - scaverage).length
		# dtg = Vector((delta.x/self.cdelta.x, delta.y/self.cdelta.y, delta.z/self.cdelta.z)).length
		scaleFactor = delta/self.cdelta
		if eventd['press']  == 'X':
			if self.splaneConstraint != 'X':
				self.sconstraint = Vector((1,0,0))
				self.splaneConstraint = 'X'
			else:
				self.sconstraint = Vector((1,1,1))
				self.splaneConstraint ='A'
		if eventd['press']  == 'Y':
			if self.splaneConstraint != 'Y':
				self.sconstraint = Vector((0,1,0))
				self.splaneConstraint = 'Y'
			else:
				self.sconstraint = Vector((1,1,1))
				self.splaneConstraint ='A'
		if eventd['press']  == 'Z':
			if self.splaneConstraint != 'Z':
				self.sconstraint = Vector((0,0,1))
				self.splaneConstraint = 'Z'
			else:
				self.sconstraint = Vector((1,1,1))
				self.splaneConstraint ='A'
		if eventd['press']  == 'SHIFT+X':
			if self.splaneConstraint != 'YZ':
				self.sconstraint = Vector((0,1,1))
				self.splaneConstraint = 'YZ'
			else:
				self.sconstraint = Vector((1,1,1))
				self.splaneConstraint ='A'
		if eventd['press']  == 'SHIFT+Y':
			if self.splaneConstraint != 'XZ':
				self.sconstraint = Vector((1,0,1))
				self.splaneConstraint = 'XZ'
			else:
				self.sconstraint = Vector((1,1,1))
				self.splaneConstraint ='A'
		if eventd['press']  == 'SHIFT+Z':
			if self.splaneConstraint != 'XY':
				self.sconstraint = Vector((1,1,0))
				self.splaneConstraint = 'XY'
			else:
				self.sconstraint = Vector((1,1,1))
				self.splaneConstraint ='A'
		for index in range(0,len(self.selectCntrl)):
			self.selectCntrl[index].x = (self.orig[index].x - self.center.x)*scaleFactor**self.sconstraint.x + self.center.x
			self.selectCntrl[index].y = (self.orig[index].y - self.center.y)*scaleFactor**self.sconstraint.y + self.center.y
			self.selectCntrl[index].z = (self.orig[index].z - self.center.z)*scaleFactor**self.sconstraint.z + self.center.z
		self.update(eventd['context'])
		if eventd['press'] == 'LEFTMOUSE':
			return 'wait'
		if eventd['press'] in {'ESC','RIGHTMOUSE'}:
			for index in range(0,len(self.selectCntrl)):
				self.selectCntrl[index].x = self.orig[index].x
				self.selectCntrl[index].y = self.orig[index].y
				self.selectCntrl[index].z = self.orig[index].z
			self.update(eventd['context'])
			return 'wait'
		return ''

	def modal_start(self, context):
		'''
		get everything ready to be run as modal tool
		'''
		self.mode          = 'main'
		self.mode_pos      = (0, 0)
		self.cur_pos       = (0, 0)
		self.is_navigating = False
		self.cb_pv_handle  = SpaceView3D.draw_handler_add(self.draw_callback_postview, (context, ), 'WINDOW', 'POST_VIEW')
		context.window_manager.modal_handler_add(self)
		context.area.header_text_set(self.bl_label)

		self.start(context)

	def modal_end(self, context):
		'''
		finish up stuff, as our tool is leaving modal mode
		'''
		self.end(context)
		SpaceView3D.draw_handler_remove(self.cb_pv_handle, "WINDOW")
		context.area.header_text_set()

	def modal(self, context, event):
		'''
		Called by Blender while our tool is running modal.
		This is the heart of the finite state machine.
		'''
		if not context.area: return {'RUNNING_MODAL'}

		context.area.tag_redraw()       # force redraw

		eventd = self.get_event_details(context, event)

		self.cur_pos  = eventd['mouse']
		nmode = self.FSM[self.mode](eventd)
		self.mode_pos = eventd['mouse']

		if nmode == 'wait': nmode = 'main'

		self.is_navigating = (nmode == 'nav')
		if nmode == 'nav':
			return {'PASS_THROUGH'}     # pass events (mouse,keyboard,etc.) on to region

		if nmode in {'finish','cancel'}:
			if nmode == 'finish':
				self.end_commit(context)
			else:
				self.end_cancel(context)
			self.modal_end(context)
			return {'FINISHED'} if nmode == 'finish' else {'CANCELLED'}

		if nmode: self.mode = nmode

		return {'RUNNING_MODAL'}    # tell Blender to continue running our tool in modal

	def invoke(self, context, event):
		'''
		called by Blender when the user invokes (calls/runs) our tool
		'''
		assert self.initialized, 'Must initialize operator before invoking'
		self.modal_start(context)
		return {'RUNNING_MODAL'}    # tell Blender to continue running our tool in modal