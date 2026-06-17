from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader

from shaders import UI_VERTEX_SHADER, UI_FRAGMENT_SHADER
from geometry import create_quad_vao
from bitmap_font import draw_text, text_width


class UI:
    def __init__(self):
        self.program = compileProgram(
            compileShader(UI_VERTEX_SHADER, GL_VERTEX_SHADER),
            compileShader(UI_FRAGMENT_SHADER, GL_FRAGMENT_SHADER),
        )
        self.quad_vao, self.quad_count = create_quad_vao()
        self.screen_w = 800
        self.screen_h = 800
        self._loc_offset = glGetUniformLocation(self.program, "u_Offset")
        self._loc_size = glGetUniformLocation(self.program, "u_Size")
        self._loc_screen = glGetUniformLocation(self.program, "u_ScreenSize")
        self._loc_color = glGetUniformLocation(self.program, "u_Color")
        self._loc_color2 = glGetUniformLocation(self.program, "u_Color2")
        self._loc_alpha = glGetUniformLocation(self.program, "u_Alpha")
        self._loc_radius = glGetUniformLocation(self.program, "u_Radius")
        self._loc_gradient = glGetUniformLocation(self.program, "u_UseGradient")

    def resize(self, width, height):
        self.screen_w = width
        self.screen_h = height

    def begin(self):
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glUseProgram(self.program)
        glBindVertexArray(self.quad_vao)
        glUniform2f(self._loc_screen, float(self.screen_w), float(self.screen_h))

    def end(self):
        glBindVertexArray(0)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)

    def draw_rect(self, x, y, w, h, color, alpha=1.0, color2=None, radius=0.0, gradient=0.0):
        glUniform2f(self._loc_offset, float(x), float(y))
        glUniform2f(self._loc_size, float(w), float(h))
        glUniform3f(self._loc_color, *color)
        glUniform3f(self._loc_color2, *(color2 if color2 else color))
        glUniform1f(self._loc_alpha, float(alpha))
        glUniform1f(self._loc_radius, float(radius))
        glUniform1f(self._loc_gradient, float(gradient))
        glDrawArrays(GL_TRIANGLES, 0, self.quad_count)

    def draw_background(self, top_color, bottom_color, glow_color):
        """Full-screen vertical gradient with a soft center glow behind the puzzle."""
        self.draw_rect(0, 0, self.screen_w, self.screen_h, top_color, 1.0, bottom_color, gradient=1.0)

        cx = self.screen_w * 0.5 - 180
        cy = self.screen_h * 0.5 - 180
        self.draw_rect(cx, cy, 360, 360, glow_color, 0.12, glow_color, radius=180.0)

    def draw_vignette(self, color):
        band = 90
        alpha = 0.55
        self.draw_rect(0, 0, self.screen_w, band, color, alpha)
        self.draw_rect(0, self.screen_h - band, self.screen_w, band, color, alpha)
        self.draw_rect(0, 0, band, self.screen_h, color, alpha)
        self.draw_rect(self.screen_w - band, 0, band, self.screen_h, color, alpha)

    def draw_panel(self, x, y, w, h, fill, fill_top, border, shadow_color, alpha=0.94, radius=10.0):
        self.draw_rect(x + 3, y + 4, w, h, shadow_color, 0.55, shadow_color, radius=radius)
        self.draw_rect(x, y, w, h, fill, alpha, fill_top, radius=radius, gradient=1.0)
        accent_h = 3
        self.draw_rect(x + 1, y + 1, w - 2, accent_h, border, 0.85, border, radius=radius)
        border_w = 1
        self.draw_rect(x, y, w, border_w, border, 0.35, border)
        self.draw_rect(x, y + h - border_w, w, border_w, border, 0.35, border)
        self.draw_rect(x, y, border_w, h, border, 0.25, border)
        self.draw_rect(x + w - border_w, y, border_w, h, border, 0.25, border)

    def draw_button(self, x, y, w, h, label, base, base_top, hover, hover_top, text_color, hovered, radius=8.0):
        shadow = (0.01, 0.02, 0.06)
        self.draw_rect(x + 2, y + 3, w, h, shadow, 0.5, shadow, radius=radius)

        if hovered:
            self.draw_rect(x, y, w, h, hover, 0.98, hover_top, radius=radius, gradient=1.0)
            shine = (0.55, 0.78, 1.0)
        else:
            self.draw_rect(x, y, w, h, base, 0.96, base_top, radius=radius, gradient=1.0)
            shine = (0.35, 0.58, 0.92)

        self.draw_rect(x + 4, y + 3, w - 8, 2, shine, 0.45, shine, radius=2.0)

        label_w = text_width(label, scale=2)
        tx = x + (w - label_w) / 2
        ty = y + (h - 7 * 2) / 2
        draw_text(self, tx, ty, label, text_color, scale=2)

    def draw_stat_chip(self, x, y, label, value, accent, text, dim):
        chip_w = max(text_width(label, 1) + text_width(str(value), 2) + 28, 110)
        chip_h = 34
        self.draw_rect(x, y, chip_w, chip_h, (0.06, 0.08, 0.14), 0.88, (0.10, 0.13, 0.20), radius=6.0, gradient=1.0)
        self.draw_rect(x, y, 3, chip_h, accent, 0.9, accent, radius=3.0)
        draw_text(self, x + 10, y + 6, label, dim, scale=1)
        draw_text(self, x + 10, y + 18, str(value), text, scale=2)
        return chip_w + 8

    @staticmethod
    def point_in_rect(px, py, x, y, w, h):
        return x <= px <= x + w and y <= py <= y + h
