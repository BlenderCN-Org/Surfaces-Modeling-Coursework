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

