import bpy
import bmesh
import bgl
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_vector_3d
from bpy_extras.view3d_utils import region_2d_to_location_3d, region_2d_to_origin_3d
from mathutils import Vector, Matrix
import math

from .common import bezier_cubic_eval_derivative, bezier_cubic_eval

from .modaloperator import ModalOperator

class OP_ExtrudeEditor2(ModalOperator):
    ''' Extruding '''
    bl_idname    = "cos424.extrudeeditor2"
    bl_label    = "COS424: Extrude Editor 2"
    bl_options     = {'REGISTER', 'UNDO'}

    def __init__(self):
        FSM = {}
        self.initialize(FSM)
        self.tesselate = 10

    def start(self, context):
        ''' Called when tool has been invoked '''
        self.cntrlList = [
            Vector((-1,-0.5,0)),Vector((-0.5,0.5,0)),Vector((0.5,0.5,0)),Vector((1,-0.5,0)),
            Vector((0,0,0)), Vector((0,0,1)), Vector((1,1,2)), Vector((1,1,3))
            ]
        self.curveA = [self.cntrlList[i] for i in [0,1,2,3]]
        self.curveB = [self.cntrlList[i] for i in [4,5,6,7]]
        self.stepsA = 5
        self.stepsB = 5
        self.lvs = []
        self.lfs = []
        self.tessellate()

    def end(self, context):
        ''' Called when tool is ending modal '''
        pass
    
    def tessellate(self):
        self.lvs = []
        self.lfs = []
        for i in range(self.stepsB+1):
            u = i / self.stepsB
            p = bezier_cubic_eval(self.curveB[0], self.curveB[1], self.curveB[2], self.curveB[3], u)
            Z = bezier_cubic_eval_derivative(self.curveB[0], self.curveB[1], self.curveB[2], self.curveB[3], u).normalized()
            Y = Z.cross(Vector((1,0,0))).normalized()
            X = Y.cross(Z).normalized()
            for j in range(self.stepsA+1):
                v = j / self.stepsA
                q = bezier_cubic_eval(self.curveA[0], self.curveA[1], self.curveA[2], self.curveA[3], v)
                self.lvs += [p + q.x * X + q.y * Y + q.z * Z]
        def getv(i,j):
            return self.lvs[j+i*(self.stepsA+1)]
        for i in range(self.stepsB):
            for j in range(self.stepsA):
                self.lfs += [[getv(i+0,j+0),getv(i+1,j+0),getv(i+1,j+1),getv(i+0,j+1)]]
    

    def end_commit(self, context):
        ''' Called when tool is committing '''
        bme = bmesh.new()
        bmv = {v.to_tuple():bme.verts.new(v) for v in self.lvs}
        bmf = [bme.faces.new(bmv[v.to_tuple()] for v in f) for f in self.lfs]

        me = bpy.data.meshes.new("Object")
        ob = bpy.data.objects.new("Object", me)
        bme.to_mesh(me)
        me.update()

        bpy.context.scene.objects.link(ob)
        ob.update_tag()
        bpy.context.scene.update()
        bpy.context.scene.objects.active = ob
        ob.select = True
        
        # verts = self.curvePoints[:]
        # faces = []

        # tessPlusOne = self.tesselate + 1
        # numCurves = len(self.curvePoints) // tessPlusOne

        # for x in range(numCurves):
        #     if x + 1 != numCurves:
        #         for i in range(tessPlusOne):
        #             if i+1 != tessPlusOne:
        #                 curSkip = x * tessPlusOne
        #                 nextCurSkip = (x + 1) * tessPlusOne
        #                 idx0 = i + curSkip
        #                 idx1 = (i + 1) + curSkip
        #                 idx2 = (i + 1) + nextCurSkip
        #                 idx3 = i + nextCurSkip
        #                 newFace = (idx0,idx1,idx2,idx3)
        #                 faces.append(newFace)
        # self.buildMesh(verts,faces)
        pass

    def end_cancel(self, context):
        ''' Called when tool is canceled '''
        pass

    def update(self, context):
        ''' Called when data is changed '''
        self.tessellate()

    def draw_postview(self, context):
        ''' Place drawing code in here '''
        
        bgl.glPointSize(3)
        bgl.glBegin(bgl.GL_POINTS)
        bgl.glColor3f(0.9,0.5,0)
        for v in self.curveA: bgl.glVertex3f(*v)
        bgl.glColor3f(0,0.5,0.9)
        for v in self.curveB: bgl.glVertex3f(*v)
        bgl.glEnd()
        
        bgl.glBegin(bgl.GL_LINES)
        bgl.glColor3f(0.5,0.25,0)
        for p0,p1 in zip(self.curveA[:-1],self.curveA[1:]):
            bgl.glVertex3f(*p0)
            bgl.glVertex3f(*p1)
        bgl.glColor3f(0,0.25,0.5)
        for p0,p1 in zip(self.curveB[:-1],self.curveB[1:]):
            bgl.glVertex3f(*p0)
            bgl.glVertex3f(*p1)
        bgl.glEnd()
        
        bgl.glPointSize(2)
        bgl.glColor3f(0,0,0)
        bgl.glBegin(bgl.GL_POINTS)
        for v in self.lvs:
            bgl.glVertex3f(*v)
        bgl.glEnd()
        
        bgl.glColor3f(0,0,0)
        bgl.glLineWidth(1)
        bgl.glBegin(bgl.GL_LINES)
        for f in self.lfs:
            for v0,v1 in zip(f[:-1],f[1:]):
                bgl.glVertex3f(*v0)
                bgl.glVertex3f(*v1)
        bgl.glEnd()
        
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glDisable(bgl.GL_DEPTH_TEST)
        bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE)
        bgl.glColor4f(0.5,0.5,0.5,0.5)
        bgl.glBegin(bgl.GL_QUADS)
        for f in self.lfs:
            for v in f:
                bgl.glVertex3f(*v)
        bgl.glEnd()
        bgl.glDisable(bgl.GL_BLEND)


    def modal_wait(self, eventd):
        if eventd['press'] == 'A':
            self.stepsA += 1
            self.tessellate()
        if eventd['press'] == 'SHIFT+A' and self.stepsA > 2:
            self.stepsA -= 1
            self.tessellate()
        if eventd['press'] == 'B':
            self.stepsB += 1
            self.tessellate()
        if eventd['press'] == 'SHIFT+B' and self.stepsB > 2:
            self.stepsB -= 1
            self.tessellate()
        return ''
