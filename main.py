import sys
import math
import glfw
from enum import Enum, auto
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader

from math_utils import Matrix4, Quaternion
from shaders import VERTEX_SHADER, FRAGMENT_SHADER, PICKER_FRAGMENT_SHADER
from geometry import create_cube_vao, create_arrow_vao
from colors import (
    BG, BG_BOTTOM, BG_GLOW, CUBE_FACE, ARROW, WIGGLE, HOVER,
    UI_SHADOW, UI_PANEL, UI_PANEL_TOP, UI_PANEL_BORDER,
    UI_BUTTON, UI_BUTTON_TOP, UI_BUTTON_HOVER, UI_TEXT, UI_TEXT_DIM, UI_ACCENT,
)
from ui import UI
from bitmap_font import draw_text, text_width
from level_config import Difficulty, MAX_LEVEL, difficulty_label, projection_size_for_grid

import time
from game_logic import Grid, CubeState, LaunchResult

DRAG_THRESHOLD = 8


class GamePhase(Enum):
    MENU = auto()
    ABOUT = auto()
    PLAYING = auto()
    LEVEL_COMPLETE = auto()
    CAMPAIGN_COMPLETE = auto()


class Scoreboard:
    def __init__(self, total_cubes):
        self.total_cubes = total_cubes
        self.total_taps = 0
        self.launches = 0
        self.blocked = 0

    def reset(self, total_cubes):
        self.total_cubes = total_cubes
        self.total_taps = 0
        self.launches = 0
        self.blocked = 0

    def record(self, result):
        if result == LaunchResult.IGNORED:
            return
        self.total_taps += 1
        if result == LaunchResult.LAUNCHED:
            self.launches += 1
        elif result == LaunchResult.BLOCKED:
            self.blocked += 1

    def score(self, grid):
        removed = grid.cubes_removed_count()
        return removed * 100 - self.blocked * 15 - max(0, self.total_taps - removed) * 5


class TapAwayGame:
    def __init__(self, window, width, height):
        self.window = window
        self.width = width
        self.height = height

        self.shader_program = compileProgram(
            compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
            compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER),
        )
        self.picker_program = compileProgram(
            compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
            compileShader(PICKER_FRAGMENT_SHADER, GL_FRAGMENT_SHADER),
        )

        self.cube_vao, self.cube_count = create_cube_vao()
        self.arrow_vao, self.arrow_count = create_arrow_vao()
        self.ui = UI()

        self.phase = GamePhase.MENU
        self.difficulty = None
        self.level = 1
        self.campaign_score = 0

        self.grid = None
        self.scoreboard = Scoreboard(0)
        self.global_rotation = Quaternion()

        self.is_dragging = False
        self.was_dragged = False
        self.mouse_down_pos = (0, 0)
        self.last_mouse_pos = (0, 0)
        self.cursor_pos = (0, 0)
        self.hovered_cube_id = 0
        self.hovered_buttons = set()
        self.last_time = time.time()

        self.buttons = {}
        self._layout_ui()

        glfw.set_framebuffer_size_callback(self.window, self.on_resize)
        glfw.set_mouse_button_callback(self.window, self.on_mouse_button)
        glfw.set_cursor_pos_callback(self.window, self.on_mouse_move)
        glfw.set_key_callback(self.window, self.on_key)

    def _btn(self, key, x, y, w, h, label):
        self.buttons[key] = {"x": x, "y": y, "w": w, "h": h, "label": label}

    def _layout_ui(self):
        self.buttons = {}
        cx = self.width // 2
        bw, bh, gap = 200, 50, 16

        if self.phase == GamePhase.MENU:
            start_y = self.height // 2 - 50
            self._btn("easy", cx - bw // 2, start_y, bw, bh, "EASY")
            self._btn("medium", cx - bw // 2, start_y + (bh + gap), bw, bh, "MEDIUM")
            self._btn("hard", cx - bw // 2, start_y + 2 * (bh + gap), bw, bh, "HARD")
            self._btn("about", cx - bw // 2, start_y + 3 * (bh + gap), bw, bh, "ABOUT")
        elif self.phase == GamePhase.ABOUT:
            self._btn("back_menu", cx - 130, self.height - 70, 260, 50, "BACK TO MENU")
        else:
            self._btn("menu", 20, self.height - 70, 150, 50, "MENU")
            self._btn("restart", self.width - 170, self.height - 70, 150, 50, "RESTART")

            if self.phase == GamePhase.LEVEL_COMPLETE:
                self._btn("next", cx - 110, self.height // 2 + 110, 220, 50, "NEXT LEVEL")
            elif self.phase == GamePhase.CAMPAIGN_COMPLETE:
                self._btn("menu_center", cx - 110, self.height // 2 + 110, 220, 50, "MAIN MENU")

    def start_campaign(self, difficulty):
        self.difficulty = difficulty
        self.level = 1
        self.campaign_score = 0
        self.start_level()

    def start_level(self):
        self.grid = Grid(difficulty=self.difficulty, level=self.level)
        self.scoreboard.reset(self.grid.total_cubes)
        self.phase = GamePhase.PLAYING
        self.hovered_cube_id = 0
        self.global_rotation = Quaternion()
        self._layout_ui()
        print(f"Started {difficulty_label(self.difficulty)} level {self.level}")

    def restart_level(self):
        self.start_level()

    def return_to_menu(self):
        self.phase = GamePhase.MENU
        self.difficulty = None
        self.level = 1
        self.grid = None
        self.hovered_cube_id = 0
        self._layout_ui()
        print("Returned to main menu")

    def open_about(self):
        self.phase = GamePhase.ABOUT
        self._layout_ui()

    def open_about(self):
        self.phase = GamePhase.ABOUT
        self._layout_ui()

    def advance_level(self):
        self.campaign_score += self.scoreboard.score(self.grid)
        if self.level >= MAX_LEVEL:
            self.phase = GamePhase.CAMPAIGN_COMPLETE
            self._layout_ui()
            print(f"Campaign complete! Total score: {self.campaign_score}")
            return
        self.level += 1
        self.start_level()

    def on_key(self, window, key, scancode, action, mods):
        if action != glfw.PRESS:
            return
        if key == glfw.KEY_R and self.phase == GamePhase.PLAYING:
            self.restart_level()
        elif key == glfw.KEY_ESCAPE:
            self.return_to_menu()

    def on_resize(self, window, width, height):
        self.width = width
        self.height = height
        self.ui.resize(width, height)
        self._layout_ui()
        glViewport(0, 0, width, height)

    def on_mouse_button(self, window, button, action, mods):
        if button != glfw.MOUSE_BUTTON_LEFT:
            return
        if action == glfw.PRESS:
            self.is_dragging = True
            self.was_dragged = False
            self.mouse_down_pos = glfw.get_cursor_pos(window)
            self.last_mouse_pos = self.mouse_down_pos
        elif action == glfw.RELEASE:
            if self.is_dragging and not self.was_dragged:
                self.handle_click(*self.mouse_down_pos)
            self.is_dragging = False

    def on_mouse_move(self, window, xpos, ypos):
        self.cursor_pos = (xpos, ypos)
        self._update_button_hover(xpos, ypos)

        if self.phase != GamePhase.PLAYING or not self.is_dragging:
            return

        dx_from_press = xpos - self.mouse_down_pos[0]
        dy_from_press = ypos - self.mouse_down_pos[1]
        if math.hypot(dx_from_press, dy_from_press) > DRAG_THRESHOLD:
            self.was_dragged = True

        if self.was_dragged:
            dx = xpos - self.last_mouse_pos[0]
            dy = ypos - self.last_mouse_pos[1]
            self.last_mouse_pos = (xpos, ypos)
            sensitivity = 0.005
            rot_x = Quaternion.from_axis_angle([0, 1, 0], dx * sensitivity)
            rot_y = Quaternion.from_axis_angle([1, 0, 0], dy * sensitivity)
            self.global_rotation = rot_x.multiply(self.global_rotation).multiply(rot_y).normalize()

    def _update_button_hover(self, xpos, ypos):
        self.hovered_buttons = set()
        for key, btn in self.buttons.items():
            if UI.point_in_rect(xpos, ypos, btn["x"], btn["y"], btn["w"], btn["h"]):
                self.hovered_buttons.add(key)

    def _update_cube_hover(self):
        if self.phase != GamePhase.PLAYING or self.is_dragging or self.grid is None:
            self.hovered_cube_id = 0
            return
        self.hovered_cube_id = self.pick_cube_id_at(*self.cursor_pos)

    def handle_click(self, x, y):
        for key, btn in self.buttons.items():
            if not UI.point_in_rect(x, y, btn["x"], btn["y"], btn["w"], btn["h"]):
                continue
            if key == "easy":
                self.start_campaign(Difficulty.EASY)
            elif key == "medium":
                self.start_campaign(Difficulty.MEDIUM)
            elif key == "hard":
                self.start_campaign(Difficulty.HARD)
            elif key == "restart":
                self.restart_level()
            elif key in ("menu", "menu_center", "back_menu"):
                self.return_to_menu()
            elif key == "next":
                self.advance_level()
            elif key == "about":
                self.open_about()
            return

        if self.phase != GamePhase.PLAYING or self.grid is None:
            return

        cube_id = self.pick_cube_id_at(x, y)
        if cube_id <= 0:
            return
        cube = self.grid.get_cube_by_id(cube_id)
        if not cube:
            return
        result = cube.try_launch(self.grid)
        self.scoreboard.record(result)

    def pick_cube_id_at(self, x, y):
        if self.grid is None:
            return 0
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glClearColor(0, 0, 0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.picker_program)
        projection = self.get_projection_matrix()
        view = self.get_view_matrix()
        global_rot = self.global_rotation.to_matrix()
        glUniformMatrix4fv(glGetUniformLocation(self.picker_program, "u_Projection"), 1, GL_FALSE, projection.to_list())
        glUniformMatrix4fv(glGetUniformLocation(self.picker_program, "u_View"), 1, GL_FALSE, view.to_list())
        glBindVertexArray(self.cube_vao)
        for cube in self.grid.cubes:
            if cube.state not in (CubeState.ACTIVE, CubeState.WIGGLING):
                continue
            r = (cube.id & 0xFF) / 255.0
            g = ((cube.id >> 8) & 0xFF) / 255.0
            b = ((cube.id >> 16) & 0xFF) / 255.0
            glUniform3f(glGetUniformLocation(self.picker_program, "u_PickerColor"), r, g, b)
            model = global_rot * cube.get_model_matrix()
            glUniformMatrix4fv(glGetUniformLocation(self.picker_program, "u_Model"), 1, GL_FALSE, model.to_list())
            glDrawArrays(GL_TRIANGLES, 0, self.cube_count)

        fb_width, fb_height = glfw.get_framebuffer_size(self.window)
        pixel_x = int(x * (fb_width / self.width))
        pixel_y = int((self.height - y) * (fb_height / self.height))
        data = glReadPixels(pixel_x, pixel_y, 1, 1, GL_RGB, GL_UNSIGNED_BYTE)
        return data[0] | (data[1] << 8) | (data[2] << 16)

    def get_cube_face_color(self, cube):
        if cube.state == CubeState.WIGGLING:
            return WIGGLE
        if cube.id == self.hovered_cube_id and cube.state == CubeState.ACTIVE:
            return HOVER
        return CUBE_FACE

    def get_projection_matrix(self):
        aspect = self.width / self.height
        if self.grid is None:
            size = 5.0
        else:
            size = projection_size_for_grid(self.grid.size)
        return Matrix4.orthographic(-size * aspect, size * aspect, -size, size, 0.1, 100.0)

    def get_view_matrix(self):
        return Matrix4.translation(0, 0, -15)

    def _update_window_title(self):
        if self.phase == GamePhase.MENU:
            glfw.set_window_title(self.window, "Tap Away | Select Difficulty")
            return
        if self.phase == GamePhase.ABOUT:
            glfw.set_window_title(self.window, "Tap Away | About")
            return
        if self.grid is None:
            return
        score = self.scoreboard.score(self.grid)
        glfw.set_window_title(
            self.window,
            f"Tap Away | {difficulty_label(self.difficulty)} L{self.level} | "
            f"Score: {score} | Cleared: {self.grid.cubes_removed_count()}/{self.grid.total_cubes}",
        )

    def draw_background(self):
        self.ui.begin()
        self.ui.draw_background(BG, BG_BOTTOM, BG_GLOW)
        self.ui.draw_vignette((0.01, 0.02, 0.05))
        self.ui.end()

    def _draw_buttons(self, keys):
        for key in keys:
            if key not in self.buttons:
                continue
            btn = self.buttons[key]
            self.ui.draw_button(
                btn["x"], btn["y"], btn["w"], btn["h"], btn["label"],
                UI_BUTTON, UI_BUTTON_TOP, UI_BUTTON_HOVER, UI_BUTTON_HOVER,
                UI_TEXT, key in self.hovered_buttons,
            )

    def draw_menu(self):
        self.ui.begin()
        title = "TAP AWAY"
        tw = text_width(title, scale=4)
        draw_text(self.ui, (self.width - tw) / 2, self.height // 2 - 170, title, UI_ACCENT, scale=4)

        subtitle = "SELECT DIFFICULTY"
        sw = text_width(subtitle, scale=2)
        draw_text(self.ui, (self.width - sw) / 2, self.height // 2 - 115, subtitle, UI_TEXT_DIM, scale=2)

        info = "10 LEVELS PER MODE"
        iw = text_width(info, scale=1)
        draw_text(self.ui, (self.width - iw) / 2, self.height // 2 - 85, info, UI_TEXT_DIM, scale=1)

        self._draw_buttons(["easy", "medium", "hard", "about"])
        self.ui.end()

    def draw_about(self):
        self.ui.begin()

        panel_w = min(710, self.width - 40)
        panel_h = min(540, self.height - 80)
        px = (self.width - panel_w) // 2
        py = (self.height - panel_h) // 2
        self.ui.draw_panel(px, py, panel_w, panel_h, UI_PANEL, UI_PANEL_TOP, UI_PANEL_BORDER, UI_SHADOW, alpha=0.97, radius=14.0)

        title = "ABOUT TAP AWAY"
        tw = text_width(title, scale=3)
        draw_text(self.ui, px + (panel_w - tw) / 2, py + 24, title, UI_ACCENT, scale=3)

        lines = [
            "GOAL",
            "CLEAR ALL CUBES TO FINISH EACH LEVEL",
            "",
            "HOW TO PLAY",
            "ROTATE THE BOARD WITH A MOUSE DRAG",
            "CLICK A CUBE TO TRY TO LAUNCH IT",
            "IF A CUBE SHAKES IT IS BLOCKED",
            "FIND A CUBE WITH A FREE PATH",
            "",
            "CAMPAIGN",
            "CHOOSE EASY MEDIUM OR HARD",
            "EACH MODE HAS TEN LEVELS",
            "FINISH LEVEL TEN TO BEAT THE GAME",
            "",
            "CONTROLS",
            "R RESTARTS THE CURRENT LEVEL",
            "ESC RETURNS TO THE MAIN MENU",
        ]

        y = py + 78
        for line in lines:
            if line == "":
                y += 8
                continue
            section = line in ("GOAL", "HOW TO PLAY", "CAMPAIGN", "CONTROLS")
            color = UI_TEXT if section else UI_TEXT_DIM
            scale = 2 if section else 1
            draw_text(self.ui, px + 24, y, line, color, scale=scale)
            y += 20 if section else 16

        self._draw_buttons(["back_menu"])
        self.ui.end()

    def draw_hud(self):
        self.ui.begin()

        if self.grid is not None:
            panel_w = min(self.width - 24, 700)
            self.ui.draw_panel(12, 12, panel_w, 88, UI_PANEL, UI_PANEL_TOP, UI_PANEL_BORDER, UI_SHADOW)

            mode = f"{difficulty_label(self.difficulty)} L{self.level}"
            draw_text(self.ui, 24, 22, mode, UI_ACCENT, scale=2)

            score = self.scoreboard.score(self.grid)
            chip_x = 24
            chip_x += self.ui.draw_stat_chip(chip_x, 48, "SCORE", score, UI_ACCENT, UI_TEXT, UI_TEXT_DIM)
            chip_x += self.ui.draw_stat_chip(
                chip_x, 48, "TAPS", self.scoreboard.total_taps, UI_PANEL_BORDER, UI_TEXT, UI_TEXT_DIM,
            )
            chip_x += self.ui.draw_stat_chip(
                chip_x, 48, "BLOCKED", self.scoreboard.blocked, WIGGLE, UI_TEXT, UI_TEXT_DIM,
            )
            cleared = self.grid.cubes_removed_count()
            self.ui.draw_stat_chip(
                chip_x, 48, "CLEARED", f"{cleared}/{self.grid.total_cubes}",
                HOVER, UI_TEXT, UI_TEXT_DIM,
            )
            draw_text(self.ui, panel_w - 210, 24, "DRAG ROTATE", UI_TEXT_DIM, scale=1)
            draw_text(self.ui, panel_w - 210, 38, "TAP LAUNCH", UI_TEXT_DIM, scale=1)

        self._draw_buttons(["restart", "menu"])

        if self.phase in (GamePhase.LEVEL_COMPLETE, GamePhase.CAMPAIGN_COMPLETE):
            dim = (0.01, 0.02, 0.06)
            self.ui.draw_rect(0, 0, self.width, self.height, dim, 0.58, dim)

            overlay_w = min(520, self.width - 48)
            overlay_h = 260
            ox = (self.width - overlay_w) // 2
            oy = (self.height - overlay_h) // 2 - 20
            self.ui.draw_panel(ox, oy, overlay_w, overlay_h, UI_PANEL, UI_PANEL_TOP, UI_ACCENT, UI_SHADOW, alpha=0.97, radius=14.0)

            if self.phase == GamePhase.LEVEL_COMPLETE:
                head = f"LEVEL {self.level} COMPLETE"
                btn_keys = ["next"]
            else:
                head = "YOU BEAT THE GAME"
                btn_keys = ["menu_center"]

            hw = text_width(head, scale=3)
            draw_text(self.ui, ox + (overlay_w - hw) / 2, oy + 20, head, UI_ACCENT, scale=3)

            if self.phase == GamePhase.LEVEL_COMPLETE:
                line = f"SCORE {self.scoreboard.score(self.grid)}"
            else:
                line = f"TOTAL SCORE {self.campaign_score + self.scoreboard.score(self.grid)}"
            lw = text_width(line, scale=2)
            draw_text(self.ui, ox + (overlay_w - lw) / 2, oy + 70, line, UI_TEXT, scale=2)

            if self.phase == GamePhase.LEVEL_COMPLETE:
                sub = f"NEXT: LEVEL {self.level + 1}"
            else:
                sub = f"{difficulty_label(self.difficulty)} COMPLETE"
            sw = text_width(sub, scale=1)
            draw_text(self.ui, ox + (overlay_w - sw) / 2, oy + 115, sub, UI_TEXT_DIM, scale=1)

            self._draw_buttons(btn_keys)

        self.ui.end()

    def run(self):
        while not glfw.window_should_close(self.window):
            current_time = time.time()
            dt = current_time - self.last_time
            self.last_time = current_time

            if self.phase == GamePhase.PLAYING and self.grid is not None:
                self.grid.update(dt)
                if self.grid.is_empty():
                    if self.level >= MAX_LEVEL:
                        self.campaign_score += self.scoreboard.score(self.grid)
                        self.phase = GamePhase.CAMPAIGN_COMPLETE
                    else:
                        self.phase = GamePhase.LEVEL_COMPLETE
                    self._layout_ui()

            self._update_window_title()
            if self.phase == GamePhase.PLAYING:
                self._update_cube_hover()

            glClearColor(*BG, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.draw_background()

            if self.phase != GamePhase.MENU and self.grid is not None:
                glUseProgram(self.shader_program)
                projection = self.get_projection_matrix()
                view = self.get_view_matrix()
                global_rot = self.global_rotation.to_matrix()
                glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "u_Projection"), 1, GL_FALSE, projection.to_list())
                glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "u_View"), 1, GL_FALSE, view.to_list())
                glUniform3f(glGetUniformLocation(self.shader_program, "u_LightDir"), 0.5, 1.0, 0.3)

                for cube in self.grid.cubes:
                    if cube.state == CubeState.REMOVED:
                        continue
                    model_base = cube.get_model_matrix()
                    model = global_rot * model_base
                    glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "u_Model"), 1, GL_FALSE, model.to_list())
                    glUniform3f(glGetUniformLocation(self.shader_program, "u_Color"), *self.get_cube_face_color(cube))
                    glBindVertexArray(self.cube_vao)
                    glDrawArrays(GL_TRIANGLES, 0, self.cube_count)

                    arrow_color = WIGGLE if cube.state == CubeState.WIGGLING else ARROW
                    glUniform3f(glGetUniformLocation(self.shader_program, "u_Color"), *arrow_color)
                    arrow_rot = cube.get_arrow_rotation().to_matrix()
                    d = cube.direction
                    face_offset = Matrix4.translation(d.x * 0.51, d.y * 0.51, d.z * 0.51)
                    arrow_model = model * face_offset * arrow_rot * Matrix4.scale(0.8, 0.8, 0.8)
                    glUniformMatrix4fv(glGetUniformLocation(self.shader_program, "u_Model"), 1, GL_FALSE, arrow_model.to_list())
                    glBindVertexArray(self.arrow_vao)
                    glDrawArrays(GL_TRIANGLES, 0, self.arrow_count)

            if self.phase == GamePhase.MENU:
                self.draw_menu()
            elif self.phase == GamePhase.ABOUT:
                self.draw_about()
            else:
                self.draw_hud()

            glfw.swap_buffers(self.window)
            glfw.poll_events()

        glfw.terminate()


if __name__ == "__main__":
    if not glfw.init():
        sys.exit()

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)

    width, height = 800, 800
    window = glfw.create_window(width, height, "Tap Away", None, None)
    if not window:
        glfw.terminate()
        sys.exit()

    glfw.make_context_current(window)
    glEnable(GL_DEPTH_TEST)

    game = TapAwayGame(window, width, height)
    game.run()
