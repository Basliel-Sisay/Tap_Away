import math
import numpy as np
class Vec3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.v = np.array([x, y, z], dtype=np.float32)

    @property
    def x(self): return self.v[0]
    @property
    def y(self): return self.v[1]
    @property
    def z(self): return self.v[2]

    def normalize(self):
        norm = np.linalg.norm(self.v)
        if norm == 0: return self
        return Vec3(*(self.v / norm))

    def __add__(self, other): return Vec3(*(self.v + other.v))
    def __sub__(self, other): return Vec3(*(self.v - other.v))
    def __mul__(self, scalar): return Vec3(*(self.v * scalar))

class Matrix4:
    def __init__(self, data=None):
        if data is None:
            self.m = np.identity(4, dtype=np.float32)
        else:
            self.m = np.array(data, dtype=np.float32).reshape(4, 4)

    @staticmethod
    def identity():
        return Matrix4()

    @staticmethod
    def translation(x, y, z):
        m = Matrix4.identity()
        m.m[0, 3] = x
        m.m[1, 3] = y
        m.m[2, 3] = z
        return m

    @staticmethod
    def scale(x, y, z):
        m = Matrix4.identity()
        m.m[0, 0] = x
        m.m[1, 1] = y
        m.m[2, 2] = z
        return m

    @staticmethod
    def orthographic(left, right, bottom, top, near, far):
        m = Matrix4.identity()
        m.m[0, 0] = 2.0 / (right - left)
        m.m[1, 1] = 2.0 / (top - bottom)
        m.m[2, 2] = -2.0 / (far - near)
        m.m[0, 3] = -(right + left) / (right - left)
        m.m[1, 3] = -(top + bottom) / (top - bottom)
        m.m[2, 3] = -(far + near) / (far - near)
        return m
    def multiply(self, other):
        return Matrix4(np.dot(self.m, other.m))
    def __mul__(self, other):
        return self.multiply(other)
    def to_list(self):
        return self.m.transpose().flatten().tolist()

class Quaternion:
    def __init__(self, w=1.0, x=0.0, y=0.0, z=0.0):
        self.q = np.array([w, x, y, z], dtype=np.float32)
    @staticmethod
    def from_axis_angle(axis, angle_rad):
        s = math.sin(angle_rad / 2.0)
        return Quaternion(
            math.cos(angle_rad / 2.0),
            axis[0] * s,
            axis[1] * s,
            axis[2] * s
        )
    def multiply(self, other):
        w1, x1, y1, z1 = self.q
        w2, x2, y2, z2 = other.q
        return Quaternion(
            w1*w2 - x1*x2 - y1*y2 - z1*z2,
            w1*x2 + x1*w2 + y1*z2 - z1*y2,
            w1*y2 - x1*z2 + y1*w2 + z1*x2,
            w1*z2 + x1*y2 - y1*x2 + z1*w2
        )
    def normalize(self):
        norm = np.linalg.norm(self.q)
        if norm == 0: return self
        self.q /= norm
        return self
    def to_matrix(self):
        w, x, y, z = self.q
        return Matrix4([
            1 - 2*y*y - 2*z*z, 2*x*y - 2*z*w,     2*x*z + 2*y*w,     0,
            2*x*y + 2*z*w,     1 - 2*x*x - 2*z*z, 2*y*z - 2*x*w,     0,
            2*x*z - 2*y*w,     2*y*z + 2*x*w,     1 - 2*x*x - 2*y*y, 0,
            0,                 0,                 0,                 1
        ])
