from mathutils import Vector
import math
import random
from .common import centroid as cent

class Geom:
    def __init__(self):
        self.adj = set()

    def addAdj(self, g):
        self.adj.add(g)

    def addAdjBoth(self, g):
        self.addAdj(g)
        g.addAdj(self)

    def removeAdj(self):
        lgeom = []
        for geom in self.adj:
            lgeom.append(geom)
        for geom in lgeom:
            geom.adj.discard(geom)

class Vertex(Geom):
    def __init__(self, co):
        super().__init__()
        self.co = co
        self.orig = Vector(co)

class Edge(Geom):
    def __init__(self, v0, v1):
        super().__init__()
        self.v0,self.v1 = v0,v1
        self.addAdjBoth(v0)
        self.addAdjBoth(v1)

    def length(self):
        return (self.v0.co - self.v1.co).length

class Face(Geom):
    def __init__(self, lvertices, ledges):
        super().__init__()
        self.lvertices = list(lvertices)
        self.ledges = list(ledges)
        for v in lvertices:
            self.addAdjBoth(v)
        for e in ledges:
            self.addAdjBoth(e)
        self.compute_normal()

    def compute_normal(self):
        a = self.lvertices[0].co
        b = self.lvertices[1].co
        c = self.lvertices[2].co

        ab = b - a
        ac = c - a

        self.normal = ab.cross(ac).normalized()

class Mesh:
    def __init__(self):
        self.vertices = list()
        self.edges = list()
        self.faces = list()

    def clone(self):
        new_mesh = Mesh()

        new_vertices_by_old = {}

        for v in self.vertices:
            new_vertices_by_old[v] = new_mesh.new_vertex(v.co)

        for f in self.faces:
            lvertices = []
            for v in f.lvertices:
                lvertices.append(new_vertices_by_old[v])
            new_mesh.new_face(lvertices)

        return new_mesh

    def get_other_edge_point(self, vertex, edge):
        if vertex == edge.v0:
            return edge.v1
        else:
            return edge.v0

    def new_vertex(self, co):
        self.vertices.append(Vertex(co))
        return self.vertices[-1]

    def new_edge(self, v0, v1):
        if v0 not in self.vertices:
            self.vertices.append(v0)
        if v1 not in self.vertices:
            self.vertices.append(v1)
        adjs = v0.adj.intersection(v1.adj)
        for a in adjs:
            if type(a) is Edge:
                return a
        self.edges.append(Edge(v0,v1))
        return self.edges[-1]

    def new_face(self, lv):
        for v in lv:
            if v not in self.vertices:
                self.vertices.append(v)
        le = []
        for v0,v1 in zip(lv,lv[1:]+lv[:1]):
            le += [self.new_edge(v0,v1)]
        self.faces.append(Face(lv, le))
        return self.faces[-1]

    def remove_vertex(self, vertex):
        if vertex not in self.vertices:
            return

        for geom in vertex.adj:
            if isinstance(geom, Edge):
                self.remove_edge(geom)
            if isinstance(geom, Face):
                self.remove_face(geom)
        vertex.removeAdj()
        self.vertices.remove(vertex)

    def remove_edge(self, edge):
        if edge not in self.edges:
            return

        for geom in edge.adj:
            if isinstance(geom, Face):
                self.remove_face(geom)
        edge.removeAdj()
        self.edges.remove(edge)

    def remove_face(self, face):
        if face not in self.faces:
            return

        face.removeAdj()
        self.faces.remove(face)

    def extrude_face(self, face):
        if face not in self.faces:
            return

        new_vertices = []
        new_vertices_by_old = {}
        new_edges_by_old = {}

        for vertex in face.lvertices:
            new_vertex = self.new_vertex(vertex.co + face.normal)
            new_vertices_by_old[vertex] = new_vertex
            new_vertices.append(new_vertex)

        for edge in face.ledges:
            v0 = new_vertices_by_old[edge.v0]
            v1 = new_vertices_by_old[edge.v1]
            new_edges_by_old[edge] = self.new_edge(v0, v1)

        new_face = self.new_face(new_vertices)

        c = len(new_vertices)
        for i in range(c):
            ov0 = face.lvertices[i]
            ov1 = face.lvertices[(i+1) % c]
            nv0 = new_vertices[i]
            nv1 = new_vertices[(i+1) % c]
            self.new_face([ov0,ov1,nv1,nv0])
        #for old_edge in new_edges_by_old:
        #    new_edge = new_edges_by_old[old_edge]
        #    self.new_face([new_edge.v0, old_edge.v0, old_edge.v1, new_edge.v1])

        self.remove_face(face)

        return new_face

    def flip_face_normal(self, face):
        face.lvertices.reverse()
        face.compute_normal()

    def make_normals_consistent(self, visited, tovisit):
        if len(visited) != len(self.faces) and len(tovisit) == 0:
            random.seed()
            ind = random.randint(0,len(self.faces)-1)
            startface = self.faces[ind]
            while startface in visited:
                #print(ind)
                # ind += 1
                # if ind >= len(self.faces):
                #     ind = 0
                ind = random.randint(0,len(self.faces)-1)
                startface = self.faces[ind]
            tovisit.append(startface)
        compareface = tovisit.pop(0)
        for edge in compareface.ledges:
            for face in edge.adj:
                if type(face) is Face and face != compareface:
                    if face not in visited and face not in tovisit:
                        tovisit.append(face)
        visited.append(compareface)
        if len(visited) != len(self.faces):
            self.make_normals_consistent(visited, tovisit)


    def add_triangle(self):
        lv = []
        lv.append(self.new_vertex(Vector((0,0,0))))
        lv.append(self.new_vertex(Vector((1,0,0))))
        lv.append(self.new_vertex(Vector((0,1,0))))
        self.new_face(lv)

    def add_triangulated_quad(self):
        lv = []
        lv.append(self.new_vertex(Vector((0,0,0))))
        lv.append(self.new_vertex(Vector((1,0,0))))
        lv.append(self.new_vertex(Vector((1,1,0))))
        lv.append(self.new_vertex(Vector((0,1,0))))
        self.new_face([lv[0],lv[1],lv[2]])
        self.new_face([lv[0],lv[2],lv[3]])

        # TODO: test by counting the number of edges added

    def add_planar_quad(self):
        lv = []
        lv.append(self.new_vertex(Vector((-1, 1, 0))))
        lv.append(self.new_vertex(Vector(( 1, 1, 0))))
        lv.append(self.new_vertex(Vector(( 1,-1, 0))))
        lv.append(self.new_vertex(Vector((-1,-1, 0))))
        self.new_face([lv[0],lv[3],lv[2],lv[1]])

    def add_planar_circle(self):
        seg = 6
        lv = []
        for i in range(0,seg):
            phi = math.pi * 2 * i / seg
            x = math.cos(phi)
            y = math.sin(phi)
            z = 0
            lv.append(self.new_vertex(Vector((x,y,0))))
        lv.append(self.new_vertex(Vector((0,0,0))))
        for i in range(0,seg):
            self.new_face([lv[i],lv[(i+1)%seg],lv[seg]])

    def add_cube(self):
        lv = []
        lv.append(self.new_vertex(Vector((-1, 1, 2))))
        lv.append(self.new_vertex(Vector(( 1, 1, 2))))
        lv.append(self.new_vertex(Vector(( 1,-1, 2))))
        lv.append(self.new_vertex(Vector((-1,-1, 2))))
        lv.append(self.new_vertex(Vector((-1, 1, 0))))
        lv.append(self.new_vertex(Vector(( 1, 1, 0))))
        lv.append(self.new_vertex(Vector(( 1,-1, 0))))
        lv.append(self.new_vertex(Vector((-1,-1, 0))))
        self.new_face([lv[0],lv[3],lv[2],lv[1]])
        self.new_face([lv[1],lv[2],lv[6],lv[5]])
        self.new_face([lv[2],lv[3],lv[7],lv[6]])
        self.new_face([lv[3],lv[0],lv[4],lv[7]])
        self.new_face([lv[1],lv[5],lv[4],lv[0]])
        self.new_face([lv[5],lv[6],lv[7],lv[4]])

    def add_tetrahedron(self):
        lv = []
        lv.append(self.new_vertex(Vector(( 1, 1, 0))))
        lv.append(self.new_vertex(Vector((-1, 1, 0))))
        lv.append(self.new_vertex(Vector((-1,-1, 0))))
        lv.append(self.new_vertex(Vector(( 1,-1, 0))))
        lv.append(self.new_vertex(Vector(( 0, 0, 1))))
        self.new_face([lv[0],lv[3],lv[2],lv[1]])
        self.new_face([lv[0],lv[1],lv[4]])
        self.new_face([lv[1],lv[2],lv[4]])
        self.new_face([lv[2],lv[3],lv[4]])
        self.new_face([lv[3],lv[0],lv[4]])

    def add_capped_cylinder(self):
        lv = []
        for i in range(0,25):
            phi = math.pi * 2 * i / 25
            x = math.cos(phi)
            y = math.sin(phi)
            lv.append(self.new_vertex(Vector((x,y,2))))
            lv.append(self.new_vertex(Vector((x,y,0))))
        lv.append(self.new_vertex(Vector((0,0,2))))
        lv.append(self.new_vertex(Vector((0,0,0))))
        for x in range(0,25):
            self.new_face([lv[x*2],lv[(x*2+2)%50],lv[50]])
            self.new_face([lv[(x*2+1)%50],lv[51],lv[(x*2+3)%50]])
            self.new_face([lv[(x*2)%50],lv[(x*2+1)%50],lv[(x*2+3)%50],lv[(x*2+2)%50]])

    def add_cone(self):
        lv = []
        for i in range(0,24):
            phi = math.pi * 2 * i / 24
            x = math.cos(phi)
            y = math.sin(phi)
            lv.append(self.new_vertex(Vector((x,y,0))))
        lv.append(self.new_vertex(Vector((0,0,1))))
#<<<<<<< HEAD
#        for i in range(0,25):
#            self.new_face([lv[i],lv[(i+1)%25],lv[25]])
#        
#        self.new_face(lv)
#=======
        for i in range(0,24):
            self.new_face([lv[i],lv[(i+1)%24],lv[24]])
#>>>>>>> e573b48ff935d1f7ba2ed48f75ab2168b78764d1

    def add_octahedron(self):
        lv = []
        lv.append(self.new_vertex(Vector(( 1, 1, 1))))
        lv.append(self.new_vertex(Vector((-1, 1, 1))))
        lv.append(self.new_vertex(Vector((-1,-1, 1))))
        lv.append(self.new_vertex(Vector(( 1,-1, 1))))
        lv.append(self.new_vertex(Vector(( 0, 0, 0))))
        lv.append(self.new_vertex(Vector(( 0, 0, 2))))
        self.new_face([lv[2],lv[3],lv[5]])
        self.new_face([lv[3],lv[0],lv[5]])
        self.new_face([lv[0],lv[1],lv[5]])
        self.new_face([lv[1],lv[2],lv[5]])
        self.new_face([lv[3],lv[2],lv[4]])
        self.new_face([lv[0],lv[3],lv[4]])
        self.new_face([lv[1],lv[0],lv[4]])
        self.new_face([lv[2],lv[1],lv[4]])

    def add_dodecahedron(self):
        lv = []
        phi = (1.0 + math.sqrt(5.0)) / 2.0
        phi2 = phi * phi
        phi3 = phi * phi * phi
        lv.append(self.new_vertex(Vector((0,phi,phi3))))
        lv.append(self.new_vertex(Vector((0,-phi,phi3))))
        lv.append(self.new_vertex(Vector((phi2,phi2,phi2))))
        lv.append(self.new_vertex(Vector((-phi2,phi2,phi2))))
        lv.append(self.new_vertex(Vector((-phi2,-phi2,phi2))))
        lv.append(self.new_vertex(Vector((phi2,-phi2,phi2))))
        lv.append(self.new_vertex(Vector((phi3,0,phi))))
        lv.append(self.new_vertex(Vector((-phi3,0,phi))))
        lv.append(self.new_vertex(Vector((phi,phi3,0))))
        lv.append(self.new_vertex(Vector((-phi,phi3,0))))
        lv.append(self.new_vertex(Vector((-phi,-phi3,0))))
        lv.append(self.new_vertex(Vector((phi,-phi3,0))))
        lv.append(self.new_vertex(Vector((phi3,0,-phi))))
        lv.append(self.new_vertex(Vector((-phi3,0,-phi))))
        lv.append(self.new_vertex(Vector((phi2,phi2,-phi2))))
        lv.append(self.new_vertex(Vector((-phi2,phi2,-phi2))))
        lv.append(self.new_vertex(Vector((-phi2,-phi2,-phi2))))
        lv.append(self.new_vertex(Vector((phi2,-phi2,-phi2))))
        lv.append(self.new_vertex(Vector((0,phi,-phi3))))
        lv.append(self.new_vertex(Vector((0,-phi,-phi3))))
        self.new_face([lv[0],lv[1],lv[2]])
        self.new_face([lv[1],lv[5],lv[2]])
        self.new_face([lv[5],lv[6],lv[2]])
        self.new_face([lv[0],lv[2],lv[3]])
        self.new_face([lv[2],lv[8],lv[3]])
        self.new_face([lv[8],lv[9],lv[3]])
        self.new_face([lv[1],lv[0],lv[4]])
        self.new_face([lv[0],lv[3],lv[4]])
        self.new_face([lv[3],lv[7],lv[4]])
        self.new_face([lv[1],lv[4],lv[5]])
        self.new_face([lv[4],lv[10],lv[5]])
        self.new_face([lv[10],lv[11],lv[5]])
        self.new_face([lv[5],lv[11],lv[6]])
        self.new_face([lv[11],lv[17],lv[6]])
        self.new_face([lv[17],lv[12],lv[6]])
        self.new_face([lv[3],lv[9],lv[7]])
        self.new_face([lv[9],lv[15],lv[7]])
        self.new_face([lv[15],lv[13],lv[7]])
        self.new_face([lv[2],lv[6],lv[8]])
        self.new_face([lv[6],lv[12],lv[8]])
        self.new_face([lv[12],lv[14],lv[8]])
        self.new_face([lv[4],lv[7],lv[10]])
        self.new_face([lv[7],lv[13],lv[10]])
        self.new_face([lv[13],lv[16],lv[10]])
        self.new_face([lv[12],lv[17],lv[14]])
        self.new_face([lv[17],lv[19],lv[14]])
        self.new_face([lv[19],lv[18],lv[14]])
        self.new_face([lv[9],lv[8],lv[15]])
        self.new_face([lv[8],lv[14],lv[15]])
        self.new_face([lv[14],lv[18],lv[15]])
        self.new_face([lv[13],lv[15],lv[16]])
        self.new_face([lv[15],lv[18],lv[16]])
        self.new_face([lv[18],lv[19],lv[16]])
        self.new_face([lv[11],lv[10],lv[17]])
        self.new_face([lv[10],lv[16],lv[17]])
        self.new_face([lv[16],lv[19],lv[17]])

    def add_uv_sphere(self, u, v):
        lv = []
        circ = math.pi*2
        index = 1
        lv.append(self.new_vertex(Vector((0,0,-1))))
        lastLayer = [0]
        for ui in range(1, u):
            phi = circ/u*ui
            radius = math.sin(phi/2)
            layer = []
            for vi in range(v):
                theta = circ/v*vi
                x = math.cos(theta) * radius
                y = math.sin(theta) * radius
                z = -1 + 1*2/u*ui
                co = Vector((x, y, z))
                ce = Vector((0, 0, 0))
                dl = co - ce
                co = ce + dl.normalized()
                lv.append(self.new_vertex(Vector((co.to_tuple()))))
                layer.append(index)
                index += 1
            if len(lastLayer) == len(layer):
                for i in range(v-1):
                    self.new_face([lv[lastLayer[i]], lv[lastLayer[i+1]], lv[layer[i+1]], lv[layer[i]]])
                self.new_face([lv[layer[0]], lv[layer[v-1]], lv[lastLayer[v-1]], lv[lastLayer[0]]])
            else:
                for i in range(v-1):
                    self.new_face([lv[0], lv[layer[i+1]], lv[layer[i]]])
                self.new_face([lv[0], lv[layer[0]], lv[layer[v-1]]])
            lastLayer = layer
        lv.append(self.new_vertex(Vector((0, 0, 1))))
        index += 1
        for i in range(v-1):
            self.new_face([lv[layer[i]], lv[layer[i+1]], lv[index-1]])
        self.new_face([lv[layer[0]], lv[index-1], lv[layer[v-1]]])

    def add_torus(self, majSeg, minSeg, majRad, minRad):
        lv = []
        circ = math.pi*2
        majCirc = circ/majSeg
        minCirc = circ/minSeg
        index = 0
        rings = []
        for maj in range(majSeg):
            majTheta = majCirc*maj
            dx = math.cos(majTheta) * majRad
            dy = math.sin(majTheta) * majRad
            n = Vector((dx, dy, 0))
            minorRing = []
            for min in range(minSeg):
                minTheta = minCirc*min
                dn = math.cos(minTheta) * minRad
                dz = math.sin(minTheta) * minRad
                co = n + n.normalized() * dn + Vector((0, 0, dz))
                co = co.to_tuple()
                lv.append(self.new_vertex((Vector((co)))))
                minorRing.append(index)
                index += 1
            rings.append(minorRing)
        for ri in range(len(rings)-1):
            ring = rings[ri]
            nextRing = rings[ri+1]
            for i in range(len(ring)-1):
                self.new_face([lv[ring[i]], lv[nextRing[i]], lv[nextRing[i+1]], lv[ring[i+1]]])
            self.new_face([lv[ring[0]], lv[ring[len(ring)-1]], lv[nextRing[len(nextRing)-1]], lv[nextRing[0]]])
        ring = rings[len(rings)-1]
        nextRing = rings[0]
        for i in range(len(ring)-1):
            self.new_face([lv[ring[i]], lv[nextRing[i]], lv[nextRing[i+1]], lv[ring[i+1]]])
        self.new_face([lv[ring[0]], lv[ring[len(ring)-1]], lv[nextRing[len(nextRing)-1]], lv[nextRing[0]]])

    def loop_cut(self):
        pass

    def decimate(self):
        if len(self.vertices) > 3:
            edgeToDecimate1 = None
            edgeToDecimate2 = None
            # Find shortest edge
            for edge in self.edges:
                if not edgeToDecimate1:
                    edgeToDecimate1 = edge
                elif edgeToDecimate1.length() < edge.length():
                    edgeToDecimate1 = edge

            # Find shortest edge's shortest adj edge
            for obj in edgeToDecimate1.v0.adj.union(edgeToDecimate1.v1.adj):
                if type(obj) is Edge:
                    if obj is edgeToDecimate1:
                        continue
                    elif not edgeToDecimate2:
                        edgeToDecimate2 = obj
                    elif edgeToDecimate2.length() < obj.length() and obj != edgeToDecimate1:
                        edgeToDecimate2 = obj

            # Remove old geo
            geoToRemove = edgeToDecimate1.adj.intersection(edgeToDecimate2.adj)
            removedFaces = []
            removedVerts = []
#            print(edgeToDecimate1)
#            print(edgeToDecimate2)
#            print('GeotoRemove')
#            print(geoToRemove)
            for obj in geoToRemove:
                if type(obj) is Vertex:
                    self.vertices.remove(obj)
                    removedVerts.append(obj)
                elif type(obj) is Face:
                    self.faces.remove(obj)
                    removedFaces.append(obj)

            # Add new geo
            newFaces = []
            for face in removedFaces:
                verts = []
                for adj in face.adj:
                    if type(adj) is Vertex and adj not in removedVerts:
                        verts.append(adj)
                newFaces.append(verts)

            for newFaceVerts in newFaces:
                self.new_face(newFaceVerts)

            self.edges.remove(edgeToDecimate1)
            self.edges.remove(edgeToDecimate2)

    def delete(self,obj):
        if type(obj) is Face:
            if obj in self.faces:
                self.faces.remove(obj)

        if type(obj) is Edge:
            if obj in self.edges:
                self.edges.remove(obj)
            for adjObj in obj.adj:
                if type(adjObj) is Face:
                    self.delete(adjObj)

        if type(obj) is Vertex:
            self.vertices.remove(obj)
            for adjObj in obj.adj:
                self.delete(adjObj)

    def rip(self, obj):
        if type(obj) is Face:
            new_vertices = []
            for vertex in obj.lvertices:
                new_vertex = self.new_vertex(vertex.co + obj.normal)
                new_vertices.append(new_vertex)
            rippedObj = self.new_face(new_vertices)
            self.delete(obj)
            return rippedObj

    def subdivide(self):
        old_faces = []
        old_edges = []
        edges = {}
        old_verts = []

        for v in self.vertices:
            old_verts.append(v)

        for f in self.faces:
            old_faces.append(f)

        for f in old_faces:
            lv = f.lvertices
            nv = list()

            for e in f.ledges:
                if e in edges:
                    cv = edges[e]
                else:
                    cv = Vertex(cent([e.v0, e.v1]))
                    edges[e] = cv
                nv.append(cv)

                old_edges.append(e)

            fcv = Vertex(cent(lv))

            for i in range(0, len(lv)):
                if i == 0:
                    self.new_face([lv[i], nv[i], fcv, nv[-1]])
                else:
                    self.new_face([lv[i], nv[i], fcv, nv[i-1]])

        for e in old_edges:
            self.remove_edge(e)
        for f in old_faces:
            self.remove_face(f)

        self.average_verts(old_verts)

    def average_verts(self, old_verts):
        avg_v = {}

        for v in self.vertices:
            avg_v[v] = [Vector((0, 0, 0)), 0]
            '''
            avg_v[v] = [Vector((0, 0, 0)),Vector((0, 0, 0)), 0, 0]
            for e in self.edges:
                if e in v.adj:
                    avg_v[v][1] = avg_v[v][1] + self.get_other_edge_point(v, e).co
                    avg_v[v][3] = avg_v[v][3] + 1
            '''
        for f in self.faces:
            fcv = cent(f.lvertices)

            #Add centroid to each vertex average for subdivision
            for v in f.lvertices:
                avg_v[v][0] = avg_v[v][0]+fcv
                avg_v[v][1] = avg_v[v][1] + 1
                #avg_v[v][2] = avg_v[v][2]+1
            #-------------------------------------------


        # Find average for each vertex
        # -------------------------------------
        for v in self.vertices:
            if avg_v[v][1] > 2:
                avg_v[v][0] = avg_v[v][0] / avg_v[v][1]
                avg_v[v][0] = v.co + ((avg_v[v][0] - v.co) * (4 / avg_v[v][1]))
                v.co = avg_v[v][0]
            else:
                if False:
                    #if v in old_verts:
                    e_avg = Vector((0, 0, 0))
                    n = 0
                    for e in self.edges:
                        if e in v.adj:
                            e_avg = e_avg + self.get_other_edge_point(v, e).co
                            n = n + 1
                    e_avg = (e_avg + v.co) / (n + 1)
                    v.co = e_avg
        #--------------------------------------
