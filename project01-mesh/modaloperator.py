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

from mathutils import Vector, Matrix, Quaternion
import math

from bpy.types import Operator
from bpy.types import SpaceView3D

from .mesh import Vertex, Edge, Face

from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_vector_3d
from bpy_extras.view3d_utils import region_2d_to_location_3d, region_2d_to_origin_3d


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
        dfns = {
            'draw_postview':    'draw_postview(self,context, mesh, isBaseMesh)',
            'modal_wait':       'modal_wait(self,eventd)',
            'start':            'start(self,context)',
            'end':              'end(self,context)',
            'end_commit':       'end_commit(self,context)',
            'end_cancel':       'end_cancel(self,context)',
            'update':           'update(self,context)',
        }
        for fnname,fndef in dfns.items():
            assert fnname in dir(self), 'Must define %s function' % fndef

        self.FSM = {} if not FSM else dict(FSM)
        self.FSM['main'] = self.modal_main
        self.FSM['nav']  = self.modal_nav
        self.FSM['translate'] = self.modal_translate
        self.FSM['scale'] = self.modal_scale
        self.FSM['rotate'] = self.modal_rotate
        self.FSM['wait'] = self.modal_wait

        self.mesh = ''
        self.submesh = ''
        self.points = []
        self.selPts = []
        self.selected = set()
        self.adjSelected = set()
        self.selectThreshold = 10
        self.selecting = 'points'
        self.sublvl = 0

        self.initialized = True


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

        if self.sublvl > 0:
            self.draw_postview(context, self.submesh, False)
        self.draw_postview(context, self.mesh, True)

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

        if self.selected and eventd['press'] == 'G':
            ''' handle translating '''
            self.selPts = {g for g in self.selected if type(g) is Vertex}
            self.grabstart = Vector(eventd['mouse'])
            self.constraint = Vector((1,1,1))
            self.planeConstraint = 'A'
            for point in self.selPts:
                point.orig = Vector(point.co)
            return 'translate'

        if self.selected and eventd['press'] == 'S':
            ''' handle scaling '''
            self.selPts = {g for g in self.selected if type(g) is Vertex}
            self.scalestart = Vector(eventd['mouse'])
            self.sconstraint = Vector((1,1,1))
            self.splaneConstraint = 'A'
            tempx, tempy, tempz = 0,0,0
            for point in self.selPts:
                point.orig = Vector(point.co)
                tempx += point.co.x
                tempy += point.co.y
                tempz += point.co.z
            self.center = Vector((tempx/len(self.selPts),tempy/len(self.selPts),tempz/len(self.selPts)))
            return 'scale'

        if self.selected and eventd['press'] == 'R':
            ''' handle rotating '''
            self.selPts = {g for g in self.selected if type(g) is Vertex}
            self.rotatestart = Vector(eventd['mouse'])
            self.rconstraint = Vector((1,1,1))
            self.rplaneConstraint = 'A'
            tempx, tempy, tempz = 0,0,0
            for point in self.selPts:
                point.orig = Vector(point.co)
                tempx += point.co.x
                tempy += point.co.y
                tempz += point.co.z
            self.center = Vector((tempx/len(self.selPts),tempy/len(self.selPts),tempz/len(self.selPts)))
            return 'rotate'

        # handle general waiting
        nmode = self.FSM['wait'](eventd)
        if nmode:
            return nmode

        return ''

    def modal_translate(self, eventd):
        # current mouse position in region space (2D)
        m2d = Vector(eventd['mouse'])
        delta = m2d - self.grabstart
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

        for point in self.selPts:
            point.co.x = point.orig.x + dg.x*self.constraint.x
            point.co.y = point.orig.y + dg.y*self.constraint.y
            point.co.z = point.orig.z + dg.z*self.constraint.z

        # tell editor to update any auxiliary info (subdiv surf, bool op, etc.)
        self.custom_update(eventd)

        if eventd['press'] == 'LEFTMOUSE':
            # accept changes
            return 'wait'

        if eventd['press'] in {'ESC','RIGHTMOUSE'}:
            # undo changes
            for point in self.selPts:
                point.co.x = point.orig.x
                point.co.y = point.orig.y
                point.co.z = point.orig.z
            self.custom_update(eventd)
            return 'wait'
        return ''

    def modal_scale(self, eventd):
        # current mouse position in region space (2D)
        m2d = Vector(eventd['mouse'])
        scaverage = location_3d_to_region_2d(eventd['region'],eventd['r3d'],self.center)
        self.cdelta = (self.scalestart - scaverage).length
        delta = (m2d - scaverage).length
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
        
        for point in self.selPts:
            point.co.x = (point.orig.x - self.center.x)*scaleFactor**self.sconstraint.x + self.center.x
            point.co.y = (point.orig.y - self.center.y)*scaleFactor**self.sconstraint.y + self.center.y
            point.co.z = (point.orig.z - self.center.z)*scaleFactor**self.sconstraint.z + self.center.z

        # tell editor to update any auxiliary info (sudbiv surf, bool op, etc.)
        self.custom_update(eventd)

        if eventd['press'] == 'LEFTMOUSE':
            # accept changes
            return 'wait'

        if eventd['press'] in {'ESC','RIGHTMOUSE'}:
            # undo changes
            for point in self.selPts:
                point.co.x = point.orig.x
                point.co.y = point.orig.y
                point.co.z = point.orig.z
            self.custom_update(eventd)
            return 'wait'
        return ''

    def modal_rotate(self, eventd):
        # current mouse position in region space (2D)
        m2d = Vector(eventd['mouse'])
        roaverage = location_3d_to_region_2d(eventd['region'],eventd['r3d'],self.center)
        self.cdelta = (self.rotatestart - roaverage).length
        delta = (m2d - roaverage).length
        rotateFactor = delta/self.cdelta

        if eventd['press']  == 'X':
            if self.rplaneConstraint != 'X':
                self.rconstraint = Vector((1,0,0))
                self.rplaneConstraint = 'X'
            else:
                self.rconstraint = Vector((1,1,1))
                self.rplaneConstraint ='A'
        if eventd['press']  == 'Y':
            if self.rplaneConstraint != 'Y':
                self.rconstraint = Vector((0,1,0))
                self.rplaneConstraint = 'Y'
            else:
                self.rconstraint = Vector((1,1,1))
                self.rplaneConstraint ='A'
        if eventd['press']  == 'Z':
            if self.rplaneConstraint != 'Z':
                self.rconstraint = Vector((0,0,1))
                self.rplaneConstraint = 'Z'
            else:
                self.rconstraint = Vector((1,1,1))
                self.rplaneConstraint ='A'
        if eventd['press']  == 'SHIFT+X':
            if self.rplaneConstraint != 'YZ':
                self.rconstraint = Vector((0,1,1))
                self.rplaneConstraint = 'YZ'
            else:
                self.rconstraint = Vector((1,1,1))
                self.rplaneConstraint ='A'
        if eventd['press']  == 'SHIFT+Y':
            if self.rplaneConstraint != 'XZ':
                self.rconstraint = Vector((1,0,1))
                self.rplaneConstraint = 'XZ'
            else:
                self.rconstraint = Vector((1,1,1))
                self.rplaneConstraint ='A'
        if eventd['press']  == 'SHIFT+Z':
            if self.rplaneConstraint != 'XY':
                self.rconstraint = Vector((1,1,0))
                self.rplaneConstraint = 'XY'
            else:
                self.rconstraint = Vector((1,1,1))
                self.rplaneConstraint ='A'

        cursor_loc = bpy.context.scene.cursor_location

        for point in self.selPts:
            q = Quaternion(self.rconstraint, math.pi/2.0)
            v_new = q * (point.co - cursor_loc) + cursor_loc

            point.co.x = v_new.x
            point.co.y = v_new.y
            point.co.z = v_new.z

            #point.co.x = (point.orig.x - self.center.x)*rotateFactor**self.rconstraint.x + self.center.x
            #point.co.y = (point.orig.y - self.center.y)*rotateFactor**self.rconstraint.y + self.center.y
            #point.co.z = (point.orig.z - self.center.z)*rotateFactor**self.rconstraint.z + self.center.z

        # tell editor to update any auxiliary info (sudbiv surf, bool op, etc.)
        self.custom_update(eventd)

        if eventd['press'] == 'LEFTMOUSE':
            # accept changes
            return 'wait'

        if eventd['press'] in {'ESC','RIGHTMOUSE'}:
            # undo changes
            self.custom_update(eventd)
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

    def custom_update(self, eventd):
        for face in self.selected:
            if type(face) is Face:
                self.mesh.flip_face_normal(face)
                self.mesh.flip_face_normal(face)
        self.mesh_update()
        self.update(eventd['context'])