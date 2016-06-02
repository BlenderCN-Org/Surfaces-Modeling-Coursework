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
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_vector_3d
from bpy_extras.view3d_utils import region_2d_to_location_3d, region_2d_to_origin_3d
from mathutils import Vector, Matrix
import math


from .modaloperator import ModalOperator

from .common import bezier_cubic_eval as curve_eval
from .common import bezier_cubic_eval_derivative as curve_der


class OP_CurveEditor(ModalOperator):
    ''' Modal Curve Editor '''
    bl_idname  = "cos424.curveeditor"       # unique identifier for buttons and menu items to reference.
    bl_label   = "COS424: Curve Editor"     # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}       # enable undo for the operator.
    
    def __init__(self):
        FSM = {}
        
        '''
        fill FSM with 'state':function(self, eventd) to add states to modal finite state machine
        FSM['example state'] = example_fn, where `def example_fn(self, context)`
        each state function returns a string to tell FSM into which state to transition.
        main, nav, and wait states are automatically added in initialize function, called below.
        '''
        
        self.initialize(FSM)

    def start(self, context):
        ''' Called when tool has been invoked '''
        
        # sample code to unselect (1,1,1) corner
        self.cntrlList += [Vector((1,1,1)),Vector((-1,1,1)),Vector((-1,-1,1)),Vector((1,-1,1)),Vector((1,1,-1)),Vector((1,-1,-1)),Vector((-1,1,-1)),Vector((-1,-1,-1))]
        self.selectCntrl += [self.cntrlList[0]]  # select first (and only) control pt
    
    def end(self, context):
        ''' Called when tool is ending modal '''
        pass
    
    def end_commit(self, context):
        ''' Called when tool is committing '''
        pass
    
    def end_cancel(self, context):
        ''' Called when tool is canceled '''
        pass
    
    def update(self, context):
        ''' Called when data is changed '''
        pass
    
    def draw_postview(self, context):
        ''' Place drawing code in here '''
        
        t111 = self.cntrlList[0].to_tuple()
        
        # sample code to draw corners of cube
        bgl.glEnable(bgl.GL_POINT_SMOOTH)
        bgl.glColor3d(0,0,0)
        bgl.glPointSize(3)
        bgl.glBegin(bgl.GL_POINTS)
        bgl.glVertex3f(*t111)       # Note: *t111 expands elements of tuple as individual parameters
        bgl.glVertex3f( 1,-1, 1)
        bgl.glVertex3f(-1,-1, 1)
        bgl.glVertex3f(-1, 1, 1)
        bgl.glVertex3f( 1, 1,-1)
        bgl.glVertex3f( 1,-1,-1)
        bgl.glVertex3f(-1,-1,-1)
        bgl.glVertex3f(-1, 1,-1)
        bgl.glEnd()
        
        # sample code to draw top and bottom edges of cube
        bgl.glLineWidth(1)
        bgl.glColor3f(0,0,0)
        bgl.glBegin(bgl.GL_LINES)
        bgl.glVertex3f(*t111)
        bgl.glVertex3f(-1, 1, 1)
        bgl.glVertex3f(-1, 1, 1)
        bgl.glVertex3f(-1,-1, 1)
        bgl.glVertex3f(-1,-1, 1)
        bgl.glVertex3f( 1,-1, 1)
        bgl.glVertex3f( 1,-1, 1)
        bgl.glVertex3f(*t111)
        
        bgl.glVertex3f( 1, 1,-1)
        bgl.glVertex3f(-1, 1,-1)
        bgl.glVertex3f(-1, 1,-1)
        bgl.glVertex3f(-1,-1,-1)
        bgl.glVertex3f(-1,-1,-1)
        bgl.glVertex3f( 1,-1,-1)
        bgl.glVertex3f( 1,-1,-1)
        bgl.glVertex3f( 1, 1,-1)
        
        bgl.glVertex3f(*t111)
        bgl.glVertex3f( 1, 1,-1)
        bgl.glEnd()
        
        # sample code to show highlighting picked geometry
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
        
    
    def modal_wait(self, eventd):
        '''
        Place code here to handle commands issued by user
        Return string that corresponds to FSM key, used to change states.  For example:
        - '':     do not change state
        - 'main': transition to main state
        - 'nav':  transition to a navigation state (passing events through to 3D view)
        '''
        
        # following code is now handled in modaloperator.py
        # if eventd['press'] in {'RIGHTMOUSE', 'SHIFT+RIGHTMOUSE'}:
        #     ''' handle picking '''
        #     # eventd['mouse'] contains x,y of mouse in region space
        #     # eventd['shift'] states if shift is being held
        #     # To convert 3D point to 2D location in region space:
        #     #   p3d = Vector((1,1,1))
        #     #   p2d = location_3d_to_region_2d(eventd['region'], eventd['r3d'], p3d)
            
        #     # sample code to pick the (1,1,1) corner
        #     p3d = self.p111
        #     p2d = location_3d_to_region_2d(eventd['region'], eventd['r3d'], p3d)
        #     m2d = Vector(eventd['mouse'])
        #     self.selected111 = ((p2d-m2d).length < 5)
            
        #     return ''
        
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
            return ''
        
        return ''
