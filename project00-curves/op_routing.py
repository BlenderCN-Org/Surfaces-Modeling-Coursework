''' Routing cubic bezier
  Ryan Klimt
  COS424: Surfaces and Modeling '''

import bpy
import bmesh
import bgl
import math
import numpy as np
from mathutils import Vector, Matrix
from .modaloperator import ModalOperator

class OP_Routing(ModalOperator):
  ''' Routing '''
  bl_idname   = 'cos424.routing'
  bl_label    = 'COS424: Routing'
  bl_options  = {'REGISTER', 'UNDO'}

  def __init__(self):
    FSM = {}
    self.initialize(FSM)

  def default_control_points(self):
    ''' Returns temp list of control points '''
    controlPoints = []
    controlPoints.append(Vector((0, 0.0, 0)))
    controlPoints.append(Vector((0, 1.0, 1)))
    controlPoints.append(Vector((0, 1.0, 2)))
    controlPoints.append(Vector((0, 0.0, 3)))
    return controlPoints

  def generate_vertices(self):
    ''' Generates routing points from given control points '''
    routingPoints = []
    for vert in self.bezierVertices:
      rotating = True
      if(vert == self.bezierVertices[0] or vert == self.bezierVertices[-1]):
        rotating = False
        if(vert[0] > 0.001 or vert[0] < -0.001 or vert[1] > 0.001 or vert[1] < -0.001):
          rotating = True
      if(rotating):
        for angle in range(0,self.numSegments):
          rad = math.pi * 2 * angle / self.numSegments
          cosa = math.cos(rad)
          sina = math.sin(rad)
          x = vert[0] * cosa - vert[1] * sina
          y = vert[0] * sina + vert[1] * cosa
          z = vert[2]
          routingPoints.append([x,y,z])
      else:           # Point is on axis
        routingPoints.append(vert)
    return routingPoints

  def generate_faces(self):
    ''' Generates the faces from given control points '''
    lf = []
    startPos = 1
    rotating = [False,False]

    if self.routedVertices[0][2] == self.routedVertices[1][2]:
      rotating[0] = True
      startPos = self.numSegments
    if self.routedVertices[-2][2] == self.routedVertices[-1][2]:
      rotating[1] = True

    if rotating[0]:   # Bottom is rotating
      for i in range(0,self.numSegments-1):
        a = i
        b = a+1
        c = b+self.numSegments
        d = c-1
        lf += [(a,b,c,d)]
      a = self.numSegments-1
      b = 0
      c = a+1
      d = self.numSegments*2-1
      lf += [(a,b,c,d)]
    else:             # Bottom is single vertice
      for i in range(1,self.numSegments):
        lf += [(0,i+1,i)]
      lf += [(0,1,self.numSegments)]

    if rotating[1]:   # Top is rotating
      for i in range(0,self.numSegments-1):
        a = len(self.routedVertices)-1-i
        b = a-1
        c = b-self.numSegments+1
        d = c-1
        lf += [(a,b,d,c)]
      a = len(self.routedVertices)-self.numSegments
      b = len(self.routedVertices)-1
      c = b-self.numSegments
      d = a-self.numSegments
      lf += [(a,b,c,d)]
    else:             # Top is single vertice
      for i in range(1,self.numSegments):
        a = len(self.routedVertices)-1
        b = a-self.numSegments+i-1
        c = b+1
        lf += [(a,b,c)]
      a = len(self.routedVertices)-1
      b = a-1
      c = a-self.numSegments
      lf += [(a,b,c)]

    ''' Everything in the middle '''
    for j in range(1,len(self.bezierVertices)-2):
      for i in range(0,self.numSegments-1):
        a = i+startPos
        b = a+1
        c = b+self.numSegments
        d = c-1
        lf += [(a,b,c,d)]
      a = self.numSegments-1+startPos
      b = startPos
      c = a+1
      d = self.numSegments*2-1+startPos
      lf += [(a,b,c,d)]
      startPos += self.numSegments

    return lf

  def create(self, lp, lf):
    ''' Creates mesh and faces object '''
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
    bpy.context.scene.objects.active = ob
    ob.select = True
    return ob

  def start(self, context):
    ''' Called when tool has been invoked '''
    self.numSegments = 32
    self.tesselate = 20
    self.cntrlList = self.default_control_points()
    self.selectCntrl += [self.cntrlList[0]]
    self.bezierVertices = self.calculateCurve()
    self.routedVertices = self.generate_vertices()

  def end(self, context):
    ''' Called when tool is ending modal '''
    pass

  def end_commit(self, context):
    ''' Called when tool is committing '''
    self.create(self.routedVertices,self.generate_faces())

  def end_cancel(self, context):
    ''' Called when tool is canceled '''
    pass

  def draw_postview(self, context):
    ''' Called every frame to draw during modal '''
    bgl.glEnable(bgl.GL_POINT_SMOOTH)
    bgl.glPointSize(1.5)
    bgl.glColor3d(0.1,0.1,0.1)
    bgl.glBegin(bgl.GL_POINTS)
    [bgl.glVertex3f(*v) for v in self.routedVertices]
    bgl.glPointSize(30)
    bgl.glColor3d(0,1,0)
    [bgl.glVertex3f(*v) for v in self.cntrlList]
    bgl.glEnd()
    bgl.glBegin(bgl.GL_LINES)
    bgl.glLineWidth(1)
    bgl.glColor3d(0.1,0.1,0.1)
    for i in range(1,len(self.routedVertices)-1):
      if(self.routedVertices[i][2] == self.routedVertices[i+1][2]):
        bgl.glVertex3f(*self.routedVertices[i])
        bgl.glVertex3f(*self.routedVertices[i+1])
      else:
        bgl.glVertex3f(*self.routedVertices[i])
        bgl.glVertex3f(*self.routedVertices[i-self.numSegments+1])

    startPos = 1
    rotating = [False,False]

    if self.routedVertices[0][2] == self.routedVertices[1][2]:
      rotating[0] = True
      startPos = self.numSegments
    if self.routedVertices[-2][2] == self.routedVertices[-1][2]:
      rotating[1] = True
    
    if rotating[0]:   # Bottom is rotating
      for i in range(0,self.numSegments):
        bgl.glVertex3f(*self.routedVertices[i])
        bgl.glVertex3f(*self.routedVertices[i+self.numSegments])
    else:             # Bottom is single vertice
      for i in range(0,self.numSegments+1):
        bgl.glVertex3f(*self.routedVertices[0])
        bgl.glVertex3f(*self.routedVertices[i])

    if rotating[1]:   # Top is rotating
      for i in range(0,self.numSegments):
        bgl.glVertex3f(*self.routedVertices[len(self.routedVertices)-i-1])
        bgl.glVertex3f(*self.routedVertices[len(self.routedVertices)-i-1-self.numSegments])
    else:             # Top is single vertice
      for i in range(0,self.numSegments):
        bgl.glVertex3f(*self.routedVertices[len(self.routedVertices)-1])
        bgl.glVertex3f(*self.routedVertices[len(self.routedVertices)-i-1])

    ''' Everything in the middle '''
    for j in range(1,len(self.bezierVertices)-2):
      for i in range(0,self.numSegments+1):
        a = i+startPos
        b = a+self.numSegments
        bgl.glVertex3f(*self.routedVertices[a])
        bgl.glVertex3f(*self.routedVertices[b])
      startPos += self.numSegments

    bgl.glEnd()
      
  def modal_wait(self, eventd):
    if eventd['press'] in {'UP_ARROW', 'DOWN_ARROW'}:
      if eventd['press'] == 'DOWN_ARROW':     self.numSegments -= 1
      if eventd['press'] == 'UP_ARROW':       self.numSegments += 1
      if self.numSegments < 3:                self.numSegments = 3
      self.update(eventd['context'])
    return ''

  def update(self, context):
    ''' Called when control points updated '''
    self.bezierVertices = self.calculateCurve()
    self.routedVertices = self.generate_vertices()