import bpy
import bmesh
import bgl
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_vector_3d
from bpy_extras.view3d_utils import region_2d_to_location_3d, region_2d_to_origin_3d
from mathutils import Vector, Matrix
import math

from .modaloperator import ModalOperator

class OP_ExtrudeEditor(ModalOperator):
    ''' Extruding '''
    bl_idname    = "cos424.extrudeeditor"
    bl_label    = "COS424: Extrude Editor"
    bl_options     = {'REGISTER', 'UNDO'}

    def __init__(self):
        FSM = {}
        self.initialize(FSM)
        self.tesselate = 10

    def start(self, context):
        ''' Called when tool has been invoked '''
        vList = [Vector((-1,-0.5,0)),Vector((-0.5,0,0)),Vector((0.5,0,0)),Vector((1,-0.5,0))]
        self.makeBezier(vList)
        self.extrudePoints = {0:vList}
        self.curvePoints = self.calculateCurve()
        self.extruding = False

    def end(self, context):
        ''' Called when tool is ending modal '''
        pass

    def buildMesh(self, points, faces):
        bme = bmesh.new()
        bmv = [bme.verts.new(p) for p in points]
        bmf = [bme.faces.new(bmv[i] for i in f) for f in faces]

        me = bpy.data.meshes.new("Object")
        ob = bpy.data.objects.new("Object", me)
        bme.to_mesh(me)
        me.update()

        bpy.context.scene.objects.link(ob)
        ob.update_tag()
        bpy.context.scene.update()
        bpy.context.scene.objects.active = ob
        ob.select = True

    def end_commit(self, context):
        ''' Called when tool is committing '''
        verts = self.curvePoints[:]
        faces = []

        tessPlusOne = self.tesselate + 1
        numCurves = len(self.curvePoints) // tessPlusOne

        for x in range(numCurves):
            if x + 1 != numCurves:
                for i in range(tessPlusOne):
                    if i+1 != tessPlusOne:
                        curSkip = x * tessPlusOne
                        nextCurSkip = (x + 1) * tessPlusOne
                        idx0 = i + curSkip
                        idx1 = (i + 1) + curSkip
                        idx2 = (i + 1) + nextCurSkip
                        idx3 = i + nextCurSkip
                        newFace = (idx0,idx1,idx2,idx3)
                        faces.append(newFace)
        self.buildMesh(verts,faces)

    def end_cancel(self, context):
        ''' Called when tool is canceled '''
        pass

    def update(self, context):
        ''' Called when data is changed '''
        self.curvePoints = self.calculateCurve()

    def draw_postview(self, context):
        ''' Place drawing code in here '''
        # Setup
        bgl.glEnable(bgl.GL_POINT_SMOOTH)
        bgl.glPointSize(5)

        # Setup control point lines
        for key in self.extrudePoints:
            aList = self.extrudePoints[key]
            self.linkPoints(aList[:2])
            self.linkPoints(aList[2:4])

        self.drawCurvePoints()

        self.calculateCurveExtrudeLines()

    def calculateCurveExtrudeLines(self):
        tessPlusOne = self.tesselate + 1
        numCurves = len(self.curvePoints) // tessPlusOne
        if numCurves > 1:
            for x in range(numCurves):
                if x + 1 != numCurves:
                    for i in range(tessPlusOne):
                        curSkip = x * tessPlusOne
                        nextCurSkip = (x + 1) * tessPlusOne
                        p0 = self.curvePoints[i+curSkip]
                        p1 = self.curvePoints[i+nextCurSkip]
                        self.createLine(p0,p1,(0,0.5,0))

    def linkPoints(self, pointsArray):
        for i in range(len(pointsArray)):
            p0 = pointsArray[i]
            self.createVert(p0)
            if i+1 != len(pointsArray):
                p1 = pointsArray[i+1]
                self.createVert(p1)
                self.createLine(p0,p1)

    def createVert(self, point, color=(1,0,0)):
        bgl.glColor3f( *color )
        bgl.glBegin(bgl.GL_POINTS)
        bgl.glVertex3f( *point )
        bgl.glEnd()

    def createLine(self, p0, p1, color=(0,0,0)):
        bgl.glColor3f( *color )
        bgl.glBegin(bgl.GL_LINES)
        bgl.glVertex3f( *p0 )
        bgl.glVertex3f( *p1 )
        bgl.glEnd

    def sortDictKeys(self,d):
        exKeys = list(d.keys())
        exKeys.sort()
        return exKeys

    def incVectInDict(self,d):
        # Copy last extruded set and move it up(z) by 1
        exKeys = self.sortDictKeys(d)
        k = exKeys[-1]
        newKey = k + 1
        d[newKey] = []
        for point in d[k]:
            myVect = point.copy()
            myVect.z += 1
            d[newKey].append(myVect)
        return newKey

    def extrude(self):
        # Copy last extruded set and move it up(z) by 1
        newKey = self.incVectInDict(self.extrudePoints)
        self.cntrlList += self.extrudePoints[newKey] # Inc ctrl points

        self.curvePoints = self.calculateCurve()

    def removeExtrude(self):
        exKeys = list(self.extrudePoints.keys())
        exKeys.sort()

        if len(exKeys) > 1:
            for point in self.extrudePoints[exKeys[-1]]:
                if point in self.cntrlList:
                    self.cntrlList.remove(point)

            del self.extrudePoints[exKeys[-1]]

    def modal_wait(self, eventd):
        if eventd['press'] == 'E': self.extrude()
        if eventd['press'] == 'SHIFT+E': self.removeExtrude()
        return ''
