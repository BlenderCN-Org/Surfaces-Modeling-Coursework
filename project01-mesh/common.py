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
from math import pow



#####################################################################################
# Bezier functions

def bernstein_poly(n,i,t):
    """ Compute general Bernstein Polynomial: B_{n,i}(t) """
    t0,t1 = t,1-t
    if i < 0 or i > n:
        return 0
    if n == 0:
        return 1;
    if n == 1:
        if i == 0:
            return t1
        else:
            return t
    if n == 2:
        if i == 0:
            return t1*t1
        if i == 1:
            return 2*t0*t1
        else:
            return t0*t0
    if n == 3:
        if i == 0:
            return t1*t1*t1
        if i == 1:
            return 3*t0*t1*t1
        if i == 2:
            return 3*t0*t0*t1
        else:
            return t0*t0*t0
    return t1 * bernstein_poly(n-1, i, t) + t0 * bernstein_poly(n-1, i-1, t)

def bernstein_derivative(n,i,t):
    """ Compute derivative of general Bernstein Polynomial: B'_{n,i}(t) """
    return n * (bernstein_poly(n-1, i-1, t) - bernstein_poly(n-1, i, t))


def bernstein_quad(i, t):
    """ Compute quadratic Bernstein Polynomial (n=2) """
    t0,t1 = t,1-t
    if i < 0 or i > 2:
        return 0
    if i == 0:
        return t1*t1
    if i == 1:
        return 2*t0*t1
    else:
        return t0*t0

def bernstein_cubic(i, t):
    """ Compute cubic Bernstein Polynomial (n=3) """
    t0,t1 = t,1-t
    if i < 0 or i > 3:
        return 0
    if i == 0:
        return t1*t1*t1
    if i == 1:
        return 3*t0*t1*t1
    if i == 2:
        return 3*t0*t0*t1
    else:
        return t0*t0*t0


def bezier_cubic_eval(p0, p1, p2, p3, t):
    """ Evaluates a cubic bezier (control values: p0, p1, p2, p3) at t """
    """ Note: p0,p1,p2,p3 can all be vectors (Vector) or scalars (float) """
    b0,b1,b2,b3 = bernstein_cubic(0,t),bernstein_cubic(1,t),bernstein_cubic(2,t),bernstein_cubic(3,t)
    return p0*b0 + p1*b1 + p2*b2 + p3*b3

def bezier_cubic_eval_derivative(p0, p1, p2, p3, t):
    """ Evaluates derivative of cubic bezier (control values: p0, p1, p2, p3) at t """
    """ Note: p0,p1,p2,p3 can all be vectors (Vector) or scalars (float) """
    q0,q1,q2 = p1-p0,p2-p1,p3-p2
    b0,b1,b2 = bernstein_quad(0,t),bernstein_quad(1,t),bernstein_quad(2,t)
    return 2*q0*b0 + 2*q1*b1 + 2*q2*b2



#####################################################################################
# Other functions

def uvsphere(u, v, sphereRadius):
    circ = math.pi*2
    
    lp = []
    lf = []
    
    index = 0
    
    lp.append((0, 0, -sphereRadius))
    index += 1
    lastLayer = [0]
    
    for ui in range(1, u):
        phi = circ/u*ui
        radius = math.sin(phi/2) * sphereRadius
        layer = []
        for vi in range(v):
            theta = circ/v*vi
            x = math.cos(theta) * radius
            y = math.sin(theta) * radius
            z = -sphereRadius + sphereRadius*2/u*ui
            
            co = Vector((x, y, z))
            ce = Vector((0, 0, 0))
            dl = co - ce
            co = ce + dl.normalized() * sphereRadius
            
            lp.append(co.to_tuple())
            layer.append(index)
            index += 1
        if len(lastLayer) == len(layer):
            for i in range(v-1):
                lf.append((lastLayer[i], lastLayer[i+1], layer[i+1], layer[i]))
            lf.append((layer[0], layer[v-1], lastLayer[v-1], lastLayer[0]))
        else:
            for i in range(v-1):
                lf.append((0, layer[i+1], layer[i]))
            lf.append((0, layer[0], layer[v-1]))
        lastLayer = layer
        
    lp.append((0, 0, sphereRadius))
    index += 1
    for i in range(v-1):
        lf.append((layer[i], layer[i+1], index-1))
    lf.append((layer[0], index-1, layer[v-1]))
    
    return lp, lf

def torus(majSeg, minSeg, majRad, minRad):
    lp = []
    lf = []
    
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
            lp.append(co)
            minorRing.append(index)
            index += 1
        rings.append(minorRing)
    
    for ri in range(len(rings)-1):
        ring = rings[ri]
        nextRing = rings[ri+1]
        for i in range(len(ring)-1):
            lf.append((ring[i], nextRing[i], nextRing[i+1], ring[i+1]))
        lf.append((ring[0], ring[len(ring)-1], nextRing[len(nextRing)-1], nextRing[0]))
    ring = rings[len(rings)-1]
    nextRing = rings[0]
    for i in range(len(ring)-1):
        lf.append((ring[i], nextRing[i], nextRing[i+1], ring[i+1]))
    lf.append((ring[0], ring[len(ring)-1], nextRing[len(nextRing)-1], nextRing[0]))
    
    return lp, lf   

def centroid(vertlist):
    co = Vector((0, 0, 0))
    count = 0
    for v in vertlist:
        co = co+v.co
        count = count + 1
        
    return co/count