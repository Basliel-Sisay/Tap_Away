from OpenGL.GL import *
from OpenGL.platform import PLATFORM
import numpy as np
import ctypes

raw_glVertexAttribPointer = PLATFORM.GL.glVertexAttribPointer

def create_cube_vao():
    vertices = np.array([
        -0.5, -0.5, -0.5,  0.0,  0.0, -1.0,
         0.5, -0.5, -0.5,  0.0,  0.0, -1.0,
         0.5,  0.5, -0.5,  0.0,  0.0, -1.0,
         0.5,  0.5, -0.5,  0.0,  0.0, -1.0,
        -0.5,  0.5, -0.5,  0.0,  0.0, -1.0,
        -0.5, -0.5, -0.5,  0.0,  0.0, -1.0,

        -0.5, -0.5,  0.5,  0.0,  0.0,  1.0,
         0.5, -0.5,  0.5,  0.0,  0.0,  1.0,
         0.5,  0.5,  0.5,  0.0,  0.0,  1.0,
         0.5,  0.5,  0.5,  0.0,  0.0,  1.0,
        -0.5,  0.5,  0.5,  0.0,  0.0,  1.0,
        -0.5, -0.5,  0.5,  0.0,  0.0,  1.0,

        -0.5,  0.5,  0.5, -1.0,  0.0,  0.0,
        -0.5,  0.5, -0.5, -1.0,  0.0,  0.0,
        -0.5, -0.5, -0.5, -1.0,  0.0,  0.0,
        -0.5, -0.5, -0.5, -1.0,  0.0,  0.0,
        -0.5, -0.5,  0.5, -1.0,  0.0,  0.0,
        -0.5,  0.5,  0.5, -1.0,  0.0,  0.0,

         0.5,  0.5,  0.5,  1.0,  0.0,  0.0,
         0.5,  0.5, -0.5,  1.0,  0.0,  0.0,
         0.5, -0.5, -0.5,  1.0,  0.0,  0.0,
         0.5, -0.5, -0.5,  1.0,  0.0,  0.0,
         0.5, -0.5,  0.5,  1.0,  0.0,  0.0,
         0.5,  0.5,  0.5,  1.0,  0.0,  0.0,

        -0.5, -0.5, -0.5,  0.0, -1.0,  0.0,
         0.5, -0.5, -0.5,  0.0, -1.0,  0.0,
         0.5, -0.5,  0.5,  0.0, -1.0,  0.0,
         0.5, -0.5,  0.5,  0.0, -1.0,  0.0,
        -0.5, -0.5,  0.5,  0.0, -1.0,  0.0,
        -0.5, -0.5, -0.5,  0.0, -1.0,  0.0,

        -0.5,  0.5, -0.5,  0.0,  1.0,  0.0,
         0.5,  0.5, -0.5,  0.0,  1.0,  0.0,
         0.5,  0.5,  0.5,  0.0,  1.0,  0.0,
         0.5,  0.5,  0.5,  0.0,  1.0,  0.0,
        -0.5,  0.5,  0.5,  0.0,  1.0,  0.0,
        -0.5,  0.5, -0.5,  0.0,  1.0,  0.0,
    ], dtype=np.float32)

    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)

    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    raw_glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * 4, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    raw_glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * 4, ctypes.c_void_p(3 * 4))
    glEnableVertexAttribArray(1)

    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)

    return vao, 36


def _box_faces(x0, y0, z0, x1, y1, z1):
    """Emit six quad faces (36 floats each) for an axis-aligned box."""
    faces = []
    faces += [x0, y0, z1, 0, 0, 1,  x1, y0, z1, 0, 0, 1,  x1, y1, z1, 0, 0, 1,
              x1, y1, z1, 0, 0, 1,  x0, y1, z1, 0, 0, 1,  x0, y0, z1, 0, 0, 1]
    faces += [x1, y0, z0, 0, 0, -1,  x0, y0, z0, 0, 0, -1,  x0, y1, z0, 0, 0, -1,
              x0, y1, z0, 0, 0, -1,  x1, y1, z0, 0, 0, -1,  x1, y0, z0, 0, 0, -1]
    faces += [x1, y0, z1, 1, 0, 0,  x1, y0, z0, 1, 0, 0,  x1, y1, z0, 1, 0, 0,
              x1, y1, z0, 1, 0, 0,  x1, y1, z1, 1, 0, 0,  x1, y0, z1, 1, 0, 0]
    faces += [x0, y0, z0, -1, 0, 0,  x0, y0, z1, -1, 0, 0,  x0, y1, z1, -1, 0, 0,
              x0, y1, z1, -1, 0, 0,  x0, y1, z0, -1, 0, 0,  x0, y0, z0, -1, 0, 0]
    faces += [x0, y1, z0, 0, 1, 0,  x1, y1, z0, 0, 1, 0,  x1, y1, z1, 0, 1, 0,
              x1, y1, z1, 0, 1, 0,  x0, y1, z1, 0, 1, 0,  x0, y1, z0, 0, 1, 0]
    faces += [x0, y0, z0, 0, -1, 0,  x0, y0, z1, 0, -1, 0,  x1, y0, z1, 0, -1, 0,
              x1, y0, z1, 0, -1, 0,  x1, y0, z0, 0, -1, 0,  x0, y0, z0, 0, -1, 0]
    return faces


def create_arrow_vao():
    head_vertices = [
        0, 0.5, 0,        0, 1, 0,
        -0.2, 0.1, -0.2, -1, 0, -1,
        0.2, 0.1, -0.2,   1, 0, -1,

        0, 0.5, 0,        0, 1, 0,
        0.2, 0.1, -0.2,   1, 0, -1,
        0.2, 0.1, 0.2,    1, 0, 1,

        0, 0.5, 0,        0, 1, 0,
        0.2, 0.1, 0.2,    1, 0, 1,
        -0.2, 0.1, 0.2,  -1, 0, 1,

        0, 0.5, 0,        0, 1, 0,
        -0.2, 0.1, 0.2,  -1, 0, 1,
        -0.2, 0.1, -0.2, -1, 0, -1,
    ]

    stem_vertices = _box_faces(-0.05, -0.3, -0.05, 0.05, 0.1, 0.05)
    vertices = np.array(head_vertices + stem_vertices, dtype=np.float32)

    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)

    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    raw_glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * 4, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    raw_glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * 4, ctypes.c_void_p(3 * 4))
    glEnableVertexAttribArray(1)

    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)

    return vao, len(vertices) // 6

def create_quad_vao():
    """Screen-space unit quad (0,0) to (1,1) for 2D UI overlays."""
    vertices = np.array([
        0.0, 0.0,
        1.0, 0.0,
        1.0, 1.0,
        1.0, 1.0,
        0.0, 1.0,
        0.0, 0.0,
    ], dtype=np.float32)

    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)

    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    raw_glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * 4, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)

    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)

    return vao, 6
