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
import bmesh
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_vector_3d
from bpy_extras.view3d_utils import region_2d_to_location_3d, region_2d_to_origin_3d
from mathutils import Vector, Matrix
import math
import copy

from .modaloperator import ModalOperator

from .common import bezier_cubic_eval as curve_eval
from .common import bezier_cubic_eval_derivative as curve_der

from .mesh import Mesh, Vertex, Edge, Face

class OP_MeshEditor(ModalOperator):
    ''' Mesh Editor '''
    bl_idname  = "cos424.mesheditor"       # unique identifier for buttons and menu items to reference.
    bl_label   = "COS424: Mesh Editor"     # display name in the interface.
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
        self.mesh = Mesh()

    def end(self, context):
        ''' Called when tool is ending modal '''
        pass

    def end_commit(self, context):
        ''' Called when tool is committing '''
        if self.sublvl > 0:
            self.mesh = self.submesh
        self.buildMesh(self.mesh)
        pass

    def end_cancel(self, context):
        ''' Called when tool is canceled '''
        pass

    def mesh_update(self):
        ''' Called when the mesh is changed at all. '''
        if self.sublvl > 0:
            self.subdivide()
        pass

    def draw_postview(self, context, mesh, isBaseMesh):
        #mesh = self.mesh #temporary in case we decide it should be named differently
        a1 = 1.0
        a2 = 1.0
        if isBaseMesh and self.sublvl > 0:
            a1 = 0.5
            a2 = .75

        bgl.glEnable(bgl.GL_POINT_SMOOTH)
        bgl.glEnable(bgl.GL_BLEND)

        #draw the vertices
        for v in mesh.vertices:
            if v in self.selected:
                bgl.glColor4d(0.9,0.5,0, a2)
                bgl.glPointSize(4)
            else:
                bgl.glColor4d(1, 1, 0, a1)
                bgl.glPointSize(2)

            bgl.glBegin(bgl.GL_POINTS)
            bgl.glVertex3f(*v.co.to_tuple())
            bgl.glEnd()


        bgl.glDepthRange(0.0, 0.9999)
        #draw the edges
        for e in mesh.edges:
            if e in self.selected:
                bgl.glColor4d(0.9,0.5,0, a2)
                bgl.glLineWidth(2)
            else:
                bgl.glColor4d(0.5, 0.5, 0, a1)
                bgl.glLineWidth(1)

            bgl.glBegin(bgl.GL_LINES)
            bgl.glVertex3f(*e.v0.co.to_tuple())
            bgl.glVertex3f(*e.v1.co.to_tuple())
            bgl.glEnd()
        bgl.glDepthRange(0.0, 1.0)


        #draw the faces
        bgl.glBegin(bgl.GL_TRIANGLES)

        for f in mesh.faces:
            if f in self.selected:
                bgl.glColor4d(0.6,0.2,0, a2)
            else:
                bgl.glColor4d(0.3, 0.3, 0.3, a1)
            a = 0
            b = 1
            c = 2
            for i in range(len(f.lvertices)-2):
                bgl.glVertex3f(*f.lvertices[a].co.to_tuple())
                bgl.glVertex3f(*f.lvertices[b].co.to_tuple())
                bgl.glVertex3f(*f.lvertices[c].co.to_tuple())
                b += 1
                c += 1

        bgl.glEnd()

        if False:
            bgl.glColor3f(0,1,1)
            bgl.glBegin(bgl.GL_LINES)
            for f in mesh.faces:
                p0 = Vector()
                for v in f.lvertices:
                    p0 += v.co
                p0 /= len(f.lvertices)
                p1 = p0 + f.normal * 0.2
                bgl.glVertex3f(*p0)
                bgl.glVertex3f(*p1)
            bgl.glEnd()

    def buildMesh(self, mesh, obj_name = 'obj'):
        bm = bmesh.new()
        bmv = []
        vd = {}

        bme = []
        bmf = []

        for i in range(len(mesh.vertices)):
            vd[mesh.vertices[i]] = i
            bmv.append(bm.verts.new(mesh.vertices[i].co))

        for e in range(len(mesh.edges)):
            v0, v1 = mesh.edges[e].v0, mesh.edges[e].v1
            bme.append(bm.edges.new((bmv[vd[v0]], bmv[vd[v1]])))

        for f in range(len(mesh.faces)):
            vl = []
            for v in mesh.faces[f].lvertices:
                vl.append(bmv[vd[v]])
            bmf.append(bm.faces.new(vl))

        me = bpy.data.meshes.new(obj_name)
        ob = bpy.data.objects.new(obj_name, me)
        bm.to_mesh(me)
        me.update()

        bpy.context.scene.objects.link(ob)
        ob.update_tag()
        bpy.context.scene.update()
        ob.select = True
        bpy.context.scene.objects.active = ob;

        return ob

    def update(self, context):
        pass

    def modal_wait(self, eventd):
        '''
        Place code here to handle commands issued by user
        Return string that corresponds to FSM key, used to change states.  For example:
        - '':     do not change state
        - 'main': transition to main state
        - 'nav':  transition to a navigation state (passing events through to 3D view)
        '''
        if eventd['press'] in {'ONE','TWO','THREE','FOUR','FIVE','SIX','SEVEN','EIGHT','NINE','ZERO','SHIFT+ONE','SHIFT+TWO'}:
            self.mesh = Mesh()
            self.selected.clear() # Clear selected points data
            self.sublvl = 0
            self.submesh = ''
            if eventd['press'] == 'ONE':            self.mesh.add_planar_quad()
            if eventd['press'] == 'TWO':            self.mesh.add_planar_circle()
            if eventd['press'] == 'THREE':          self.mesh.add_cube()
            if eventd['press'] == 'FOUR':           self.mesh.add_tetrahedron()
            if eventd['press'] == 'FIVE':           self.mesh.add_capped_cylinder()
            if eventd['press'] == 'SIX':            self.mesh.add_cone()
            if eventd['press'] == 'SEVEN':          self.mesh.add_octahedron()
            if eventd['press'] == 'EIGHT':          self.mesh.add_dodecahedron()
            if eventd['press'] == 'NINE':           self.mesh.add_uv_sphere(25,25)
            if eventd['press'] == 'ZERO':           self.mesh.add_torus(25,25,1,1)

            faces = []
            #for face in self.mesh.faces:
            #    faces.append(face)
            #for face in faces:
            #    self.mesh.extrude_face(face)

        # Handle Picking
        if eventd['press'] in {'RIGHTMOUSE','SHIFT+RIGHTMOUSE'}: self.handlePicking(eventd)

        #Subdivision
        if eventd['press'] == "EQUAL":
            self.sublvl = self.sublvl + 1
            self.subdivide()
        if eventd['press'] == "MINUS":
            self.sublvl = self.sublvl - 1
            if self.sublvl < 0:
                self.sublvl = 0
            self.subdivide()

        # Decimation
        if eventd['press'] == "D": self.decimate()

        #handle extrusion
        if eventd["press"] == "E":
            new_faces = []
            old_faces = []
            for obj in self.selected:
                if type(obj) is Face:
                    old_faces.append(obj)
                    new_faces.append(self.mesh.extrude_face(obj))
            self.mesh_update()

            for old_face in old_faces:
                self.selected.discard(old_face)
                for v in old_face.lvertices:
                    self.selected.discard(v)
                for e in old_face.ledges:
                    self.selected.discard(e)

            for new_face in new_faces:
                self.selected.add(new_face)
                for v in new_face.lvertices:
                    self.selected.add(v)
                for e in new_face.ledges:
                    self.selected.add(e)

        if eventd['press'] == 'P':
            if self.selecting == 'points':
                self.selecting = 'edges'
            elif self.selecting == 'edges':
                self.selecting = 'faces'
            elif self.selecting == 'faces':
                self.selecting = 'points'

        if eventd['press'] == 'F':
            for face in self.selected:
                if type(face) is Face:
                    self.mesh.flip_face_normal(face)

        if eventd['press'] == 'N':
            x = False
            for face in self.selected:
                if type(face) is Face:
                    startface = face
                    x = True
            if x == False:
                visited = []
                tovisit = []
                self.mesh.make_normals_consistent(visited, tovisit)
            else:
                visited = []
                tovisit = [startface]
                self.mesh.make_normals_consistent(visited, tovisit)

        if eventd['press'] == 'V': self.rip(eventd)

        if eventd['press'] == 'BACK_SPACE' or eventd['press'] == 'DEL': self.delete()

        return ''

    def handlePicking(self, eventd):
        ''' handle picking '''
        # eventd['mouse'] contains x,y of mouse in region space
        # eventd['shift'] states if shift is being held
        # To convert 3D point to 2D location in region space:
        #   p3d = Vector((1,1,1))
        #   p2d = location_3d_to_region_2d(eventd['region'], eventd['r3d'], p3d)

        # get mouse location in region space (2D)
        m2d = Vector(eventd['mouse'])

        # Map mouse to 3d space to get z index
        m3d = region_2d_to_origin_3d(eventd['region'], eventd['context'].space_data.region_3d, m2d)

        # Reset picked value to nothing
        self.pickedObj = None

        # Reset remove boolean
        self.removeSelectedPoint = False

        if eventd['press'] == 'RIGHTMOUSE':
            self.selected.clear() # clear out current selection
            self.adjSelected.clear() # clear out adj selected

        if self.selecting == 'points':
            self.selectThreshold = 10
            for point in self.mesh.vertices:
                p3d = point.co
                p2d = location_3d_to_region_2d(eventd['region'], eventd['r3d'], p3d)
                self.manipObjectInSelect(eventd, (p2d-m2d).length, (p3d-m3d).length, m3d, point)
        elif self.selecting == 'edges':
            self.selectThreshold = 5
            for edge in self.mesh.edges:
                v0,v1 = edge.v0.co,edge.v1.co
                p3d0,p3d1 = v0,v1
                p2d0 = location_3d_to_region_2d(eventd['region'], eventd['r3d'], p3d0) # Endpoint of edge in 2d space
                p2d1 = location_3d_to_region_2d(eventd['region'], eventd['r3d'], p3d1) # Endpoint of edge in 2d space
                pDiff = p2d1-p2d0
                l = (pDiff/pDiff.length).dot(m2d-p2d0) # Length from one endpoint to point p
                if l < 0: l = 0
                if l > pDiff.length: l = pDiff.length
                p2d = p2d0 + l * (pDiff/pDiff.length) # Point on edge perpendicular to clicked point
                p3d = self.pickEdgeHelper(edge,m3d)
                self.manipObjectInSelect(eventd, (p2d-m2d).length, (p3d-m3d).length, m3d, edge)
        elif self.selecting == 'faces':
            self.selectThreshold = 10
            for face in self.mesh.faces:
                for i in range(len(face.lvertices)):
                    if i+2 != len(face.lvertices):
                        v3d0 = face.lvertices[0].co
                        v3d1 = face.lvertices[i+1].co
                        v3d2 = face.lvertices[i+2].co
                        v0 = location_3d_to_region_2d(eventd['region'], eventd['r3d'], v3d0)
                        v1 = location_3d_to_region_2d(eventd['region'], eventd['r3d'], v3d1)
                        v2 = location_3d_to_region_2d(eventd['region'], eventd['r3d'], v3d2)

                        if self.pointInTriangle(m2d,v0,v1,v2):
                            if self.pickedObj == None:
                                self.pickedObj = face
                            else:
                                if len(self.pickedObj.lvertices) == 3:
                                    p3d0 = self.pickedObj.lvertices[0].co
                                    p3d1 = self.pickedObj.lvertices[1].co
                                    p3d2 = self.pickedObj.lvertices[2].co
                                else:
                                    p3d0 = self.pickedObj.lvertices[0].co
                                    p3d1 = self.pickedObj.lvertices[i+1].co
                                    p3d2 = self.pickedObj.lvertices[i+2].co
                                d0 = self.pickFaceHelper(v3d0,v3d1,v3d2,m3d)
                                d1 = self.pickFaceHelper(p3d0,p3d1,p3d2,m3d)
                                newD = (d0-m3d).length
                                oldD = (d1-m3d).length
                                if newD < oldD:
                                    self.pickedObj = face
                    else:
                        break

        if self.pickedObj != None:
            if self.pickedObj in self.selected:
                self.selected.remove(self.pickedObj)
            else:
                self.selectObjAndAdj(self.pickedObj)

    ''' BEGIN: Picker helper functions '''
    def selectObjAndAdj(self, obj):
        if obj:
            self.selected.add(obj)
            if self.selecting != 'points':
                for adjObj in obj.adj:
                    if self.selecting == 'edges' and type(adjObj) is Vertex:
                        self.selected.add(adjObj)
                        self.adjSelected.add(adjObj)
                    elif self.selecting == 'faces' and (type(adjObj) is Vertex or type(adjObj) is Edge):
                        self.selected.add(adjObj)
                        self.adjSelected.add(adjObj)

    def manipObjectInSelect(self, eventd, dist_2d, dist_3d, mouse_3d, obj):
        if dist_2d < self.selectThreshold:
            if self.pickedObj == None:
                self.pickedObj = obj
            elif self.selecting == 'points' and dist_3d > (self.pickedObj.co-mouse_3d).length: # If point is closer, pick it.
                self.pickedObj = obj
            elif self.selecting == 'edges':
                p = self.pickEdgeHelper(self.pickedObj, mouse_3d)
                if dist_3d < (p - mouse_3d).length:
                    self.pickedObj = obj

    def pickEdgeHelper(self, edge, mouse_vector):
        pDiff = edge.v0.co - edge.v1.co
        l = (pDiff/pDiff.length).dot(mouse_vector - edge.v0.co)
        p = edge.v0.co + l * (pDiff/pDiff.length) # Closest point on edge to picked value
        return p

    def pickFaceHelper(self, v0, v1, v2, m3d):
        # From http://www.gamedev.net/topic/552906-closest-point-on-triangle/
        e0 = v1 - v0
        e1 = v2 - v0
        mV = v0 - m3d

        a = e0.dot(e0)
        b = e0.dot(e1)
        c = e1.dot(e1)
        d = e0.dot(mV)
        e = e1.dot(mV)

        det = a*c - b*b
        s = b*e - c*d
        t = b*d - a*e

        if s+t < det:
            if s < 0:
                if t < 0:
                    if d < 0:
                        s = self.clamp((-1*d)/a, 0, 1)
                        t = 0
                    else:
                        s = 0
                        t = self.clamp((-1*e)/c, 0, 1)
                else:
                    s = 0
                    t = self.clamp((-1*e)/c, 0 ,1)
            elif t < 0:
                s = self.clamp((-1*d)/a, 0, 1)
                t = 0
            else:
                invDet = 1 / det
                s *= invDet
                t *= invDet
        else:
            if s < 0:
                tmp0 = b+d
                tmp1 = c+e
                if tmp1 > tmp0:
                    numer = tmp1 - tmp0
                    denom = a-2*b+c
                    s = self.clamp(numer/denom, 0, 1)
                    t = 1-s
                else:
                    t = self.clamp((-1*e)/c, 0, 1)
                    s = 0
            elif t < 0:
                if a+d > b+e:
                    numer = c+e-b-d
                    denom = a-2*b+c
                    s = self.clamp(numer/denom, 0, 1)
                    t = 1-s
                else:
                    s = self.clamp((-1*e)/c, 0, 1)
                    t = 0
            else:
                numer = c+e-b-d
                denom = a-2*b+c
                s = self.clamp(numer/denom, 0, 1)
                t = 1 - s
        return v0 + s * e0 + t * e1

    def clamp(self, x, aMin, aMax):
        if x < aMin:
            x = aMin
        elif x > aMax:
            x = aMax
        return x

    def sign(self, p1, p2, p3):
        if p1 and p2 and p3:
            return (p1.x - p3.x) * (p2.y - p3.y) - (p2.x - p3.x) * (p1.y - p3.y)

    def pointInTriangle(self, p, a, b, c):
        # Found solution here http://www.blackpawn.com/texts/pointinpoly/
        b1 = self.sign(p,a,b) < 0
        b2 = self.sign(p,b,c) < 0
        b3 = self.sign(p,c,a) < 0
        return ((b1 == b2) and (b2 == b3))
    ''' END: Picker helper functions '''

    def decimate(self):
        self.mesh.decimate()

    def delete(self):
        selectedWithOutAdj = self.selected.difference(self.adjSelected)
        for obj in selectedWithOutAdj:
            self.mesh.delete(obj)

    def rip(self, eventd):
        currentSelected = self.selected.copy()
        self.selected.clear()
        for obj in currentSelected:
            rippedObj = self.mesh.rip(obj)
            self.selectObjAndAdj(rippedObj)
        self.mesh_update()

    def subdivide(self):
        self.submesh = self.mesh.clone()

        if self.sublvl > 0:
            for i in range(self.sublvl):
                self.submesh.subdivide()
