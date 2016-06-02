#README: Justin Powell Shapes Homework
# 9 shapes completed
# To add a shape use the function spawn_obj(obj_type, name, location)


import bpy
import bmesh
import math
from mathutils import Vector

def create(lp, lf, obj_name = 'obj'):
    bme = bmesh.new()
    bmv = [bme.verts.new(p) for p in lp]
    bmf = [bme.faces.new(bmv[i] for i in f) for f in lf]

    me = bpy.data.meshes.new(obj_name)
    ob = bpy.data.objects.new(obj_name, me)
    bme.to_mesh(me)
    me.update()

    bpy.context.scene.objects.link(ob)
    ob.update_tag()
    bpy.context.scene.update()
    #bpy.context.scene.objects.active = ob
    ob.select = True
    
    
    return ob

def poly(num_sides = 3, radius = 1, loc = Vector((0, 0, 0)), rot = 0, fan = 0):
    a = loc[0]
    b = loc[1]
    r = radius

    p = []
    f = []

    for i in range(0, 360, int(360/num_sides)):
        x = a + (r*math.cos(math.radians(i+rot)))
        y = b + (r*math.sin(math.radians(i+rot)))
    
        p.append((x, y, loc[2]))
        
    if(fan == 1):
        p.append((loc[0], loc[1], loc[2]))
        for j in range(len(p)-2):
            f.append([j, j+1, len(p)-1])
        f.append([len(p)-2, 0, len(p)-1])
    else:
        l = []
        for v in range(len(p)):
            l.append(v)
        f.append(l)

    return p, f

def cube(side_len = 2):
    l = side_len/2
    p = [(-l, -l, l), (l, -l, l), (l, -l, -l), (-l, -l, -l), (-l, l, l), (-l, l, -l), (l, l, l), (l, l, -l)]
    f = [(0, 3, 2, 1), (0, 4, 5, 3), (0, 1, 6, 4), (1, 2, 7, 6), (6, 7, 5, 4), (2, 3, 5, 7)]
    return p, f

def tetra(radius = 1):
    l = radius
    p, f = poly(3, l)
    
    p.append((0, 0, -l))
    f = f + [(0, 2, 3), (0, 3, 1), (1, 3, 2)]
    return p, f

def cap_cylinder(num_sides = 8, radius = 1, height = 2, fan = 0):
    p0, f0 = poly(num_sides, radius, Vector((0, 0, height/2)), 0, fan)
    p1, f1 = poly(num_sides, radius, Vector((0, 0, -height/2)), 0, fan)
    
    if fan == 0:
        f2 = [[]]
        for f in range(len(f1)):
            for v in f1[f]:
                f2[f].append(v + len(p1))
        f2[0].reverse()
            
        f3 = []
    
        for i in range(len(p0)-1):
            f3.append([i,(i+len(p0)), (i+len(p0)+1), i+1])
        f3.append([len(p0)-1,(len(p0)*2)-1, (len(p0)), 0])
                
        p = p0 + p1
        f = f0 + f2 + f3
        
    #TODO: Make work with fanned circle.

    return p, f

def cone(num_sides = 8, radius = 1, height = 2):
    p, f = poly(num_sides, radius)
    p.append((0, 0, -height))
    
    for i in range(len(p)-2):
        f.append([i, len(p)-1, i+1])
    f.append([len(p)-2, len(p)-1, 0])
    
    print(p, '\n', f)
    
    return p, f

def octa(radius = 2):
    p = poly(4, radius)[0]
    f = []
    
    p.append((0, 0, radius))
    p.append((0, 0, -radius))
    
    for i in range(len(p)-3):
        f.append([i, len(p)-1, i+1])
        f.append([i, i+1, len(p)-2])
    f.append([len(p)-3, len(p)-1, 0])
    f.append([len(p)-3, 0, len(p)-2])
    
    return p, f

def dodec():
    pass

def uv_sphere(num_sides = 32, radius = 1):
    step = 1/num_sides
    p = []
    f = []
    i = float(-radius) + step
    factor = 10
    p1 = [(0, 0, (math.sin(radius))), (0, 0, -(math.sin(radius)))]
    
    while(i < radius):
        p.append(poly(num_sides, math.cos(i*(math.pi/2)), Vector((0, 0, math.sin(i))), 1, 0)[0])
        i = i + step
    
    for l in range(len(p)-1):
        for k in range(len(p[l])-1):
            f.append([k + (l*len(p[l])), k + (l*len(p[l]))+1,  k + ((l+1)*len(p[l])+1), k + ((l+1)*len(p[l]))])
           
            if(l == len(p)-2):
                f.append([k+((l+1)*len(p[l])), k+((l+1)*len(p[l]))+1, len(p)*len(p[len(p)-1])])
                
        f.append([((l+1)*len(p[l])), k + ((l+1)*len(p[l])+1), k+(l*len(p[l])+1), 0 + (l*len(p[l]))])
        
        
        if(l == 0):
            for y in range(len(p[l])-1):
                f.append([y+(l*len(p[l])), len(p)*len(p[l])+1, y+(l*len(p[l]))+1])
    
    f.append([(l+1)*len(p[l]), len(p)*len(p[len(p)-1]), (l+2)*len(p[l])-1])
    f.append([len(p[0])-1, len(p)*len(p[len(p)-1])+1, 0])
    
    p2 = []
    for j in range(len(p)):
        for v in p[j]:        
            p2.append(v)
            
    p2 = p2 + p1
    
    p_final= []
    for point in p2:
        pv = Vector(point).normalized()
        p_final.append((pv * radius).to_tuple())
    
    return p_final, f

def ico_sphere(radius = 1):
    p0 = poly(5, radius, (0, 0, radius/2))[0]
    p0.append((0, 0, radius))
    
    p1 = poly(5, radius, (0, 0, -radius/2), 36)[0]
    p1.append((0, 0, -radius))
    
    f = []
    
    for i in range(len(p0)-2):
        f.append([i, i+len(p0), i+1])
        f.append([i, i+1, len(p0)-1])
        
        f.append([i+len(p0), i+len(p0)+1, i+1])
        f.append([i+len(p0), len(p0)*2-1, i+len(p0)+1])
    
    f.append([len(p0)-2, i+len(p0)+1, 0])
    f.append([len(p0)-2, 0, len(p0)-1])
    
    f.append([len(p0)*2-2, len(p0), 0])
    f.append([len(p0)*2-2, len(p0)*2-1, len(p0)])
    
    p = p0 + p1
    
    return p, f

def trunc_ico():
    pass

def torus():
    pass

def spawn_obj(obj_type = 0, obj_name = 'obj', loc = Vector((0, 0, 0)), size = 2, height = 2):
    if obj_type == 0:
        p, f = poly(4)
        
    elif obj_type == 1:
        p, f = poly(15)
        #p, f = poly(16, 1, (0, 0, 0), 1)
        
    elif obj_type == 2:
        p, f = cube(size)
        
    elif obj_type == 3:
        p, f = tetra(size)
        
    elif obj_type == 4:
        p, f = cap_cylinder(8, size, height)
        
    elif obj_type == 5:
        p, f = cone(16)
        
    elif obj_type == 6:
        p, f = octa(size)
        
    elif obj_type == 7:
        p, f = dodec()
        
    elif obj_type == 8:
        p, f = uv_sphere()
        
    elif obj_type == 9:
        p, f = ico_sphere(size)
        
    elif obj_type == 10:
        p, f = trunc_ico()
        
    elif obj_type == 11:
        p, f = torus()
        
    ob = create(p, f, obj_name)
    ob.location = loc
	
def test():    
	spawn_obj(0, 'plane', (-2, -2, 0))
	spawn_obj(1, 'circle', (-2, 0, 0))
	spawn_obj(2, 'cube', (-2, 3, 0))
	spawn_obj(3, 'tetra', (0, 2, 0))
	spawn_obj(4, 'cylinder', (0, -2, 0))
	spawn_obj(5, 'cone', (0, 0, 1))
	spawn_obj(6, 'octa', (2, -2, 0))
	spawn_obj(8, 'uv_sphere', (2, 0, 0))
	spawn_obj(9, 'ico_sphere', (2, 2, 0))