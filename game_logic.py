import math
import random
import numpy as np
from enum import Enum, auto

from math_utils import Matrix4, Quaternion, Vec3
from level_config import Difficulty, get_level_params


class CubeState(Enum):
    ACTIVE = auto()
    WIGGLING = auto()
    FLYING = auto()
    REMOVED = auto()


class LaunchResult(Enum):
    IGNORED = auto()
    LAUNCHED = auto()
    BLOCKED = auto()


OFF_SCREEN_DISTANCE = 50.0

DIRECTIONS = (
    (1, 0, 0), (-1, 0, 0),
    (0, 1, 0), (0, -1, 0),
    (0, 0, 1), (0, 0, -1),
)


class Cube:
    def __init__(self, cube_id, grid_position, direction):
        self.id = cube_id
        self.grid_position = tuple(int(v) for v in grid_position)
        self.direction = Vec3(*direction)

        self.state = CubeState.ACTIVE
        self.animation_offset = Vec3(0.0, 0.0, 0.0)

        self.flight_time = 0.0
        self.flight_speed = 15.0

        self.wiggle_time = 0.0
        self.wiggle_duration = 0.3

    def update(self, dt):
        if self.state == CubeState.FLYING:
            self.flight_time += dt
            self.animation_offset = self.animation_offset + (
                self.direction * (self.flight_speed * dt)
            )
            visual = self.get_visual_position()
            if np.linalg.norm(visual.v) > OFF_SCREEN_DISTANCE:
                self.state = CubeState.REMOVED

        elif self.state == CubeState.WIGGLING:
            self.wiggle_time += dt
            if self.wiggle_time >= self.wiggle_duration:
                self.state = CubeState.ACTIVE
                self.wiggle_time = 0.0

    def get_visual_position(self):
        gx, gy, gz = self.grid_position
        return Vec3(
            gx + self.animation_offset.x,
            gy + self.animation_offset.y,
            gz + self.animation_offset.z,
        )

    def get_model_matrix(self):
        pos = self.get_visual_position()
        m = Matrix4.translation(pos.x, pos.y, pos.z)

        if self.state == CubeState.WIGGLING:
            offset = math.sin(self.wiggle_time * 40) * 0.05
            m = m * Matrix4.translation(
                self.direction.x * offset,
                self.direction.y * offset,
                self.direction.z * offset,
            )
        return m

    def get_arrow_rotation(self):
        d = self.direction
        if d.x > 0:
            return Quaternion.from_axis_angle([0, 0, 1], -math.pi / 2)
        if d.x < 0:
            return Quaternion.from_axis_angle([0, 0, 1], math.pi / 2)
        if d.y > 0:
            return Quaternion()
        if d.y < 0:
            return Quaternion.from_axis_angle([1, 0, 0], math.pi)
        if d.z > 0:
            return Quaternion.from_axis_angle([1, 0, 0], math.pi / 2)
        if d.z < 0:
            return Quaternion.from_axis_angle([1, 0, 0], -math.pi / 2)
        return Quaternion()

    def try_launch(self, grid):
        if self.state != CubeState.ACTIVE:
            return LaunchResult.IGNORED

        if grid.is_obstructed(self):
            self.state = CubeState.WIGGLING
            self.wiggle_time = 0.0
            return LaunchResult.BLOCKED

        grid.unoccupy(self)
        self.state = CubeState.FLYING
        self.flight_time = 0.0
        self.animation_offset = Vec3(0.0, 0.0, 0.0)
        return LaunchResult.LAUNCHED


def _coord_bounds(size):
    offset = (size - 1) // 2
    return -offset, offset


def _direction_steps(pos, direction, bounds):
    min_c, max_c = bounds
    x, y, z = pos
    dx, dy, dz = direction
    if dx > 0:
        return max_c - x
    if dx < 0:
        return x - min_c
    if dy > 0:
        return max_c - y
    if dy < 0:
        return y - min_c
    if dz > 0:
        return max_c - z
    return z - min_c


def _candidate_directions(pos, bounds, max_step_bonus):
    scored = [( _direction_steps(pos, d, bounds), d) for d in DIRECTIONS]
    scored.sort(key=lambda item: item[0])
    best = scored[0][0]
    limit = best + max_step_bonus
    return [direction for steps, direction in scored if steps <= limit]


def _is_blocked_in_sim(pos, direction, occupied, bounds):
    dx, dy, dz = direction
    x, y, z = pos
    min_c, max_c = bounds

    while True:
        x += dx
        y += dy
        z += dz
        if x < min_c or x > max_c or y < min_c or y > max_c or z < min_c or z > max_c:
            return False
        if (x, y, z) in occupied:
            return True


def _launchable_count(direction_map, bounds):
    occupied = set(direction_map.keys())
    return sum(
        1 for pos, direction in direction_map.items()
        if not _is_blocked_in_sim(pos, direction, occupied, bounds)
    )


def _can_clear_all(direction_map, bounds):
    occupied = dict(direction_map)
    while occupied:
        launchable = [
            pos for pos, direction in occupied.items()
            if not _is_blocked_in_sim(pos, direction, occupied, bounds)
        ]
        if not launchable:
            return False
        del occupied[launchable[0]]
    return True


def _tutorial_direction_map(size):
    min_c, max_c = _coord_bounds(size)
    direction_map = {}

    for x in range(min_c, max_c + 1):
        for y in range(min_c, max_c + 1):
            for z in range(min_c, max_c + 1):
                if x == 0 and y == 0 and z == 0:
                    direction_map[(x, y, z)] = (1, 0, 0)
                    continue
                ax, ay, az = abs(x), abs(y), abs(z)
                if ax >= ay and ax >= az:
                    direction_map[(x, y, z)] = (1 if x > 0 else -1, 0, 0)
                elif ay >= az:
                    direction_map[(x, y, z)] = (0, 1 if y > 0 else -1, 0)
                else:
                    direction_map[(x, y, z)] = (0, 0, 1 if z > 0 else -1)

    return direction_map


def _build_direction_map(size, difficulty, level):
    params = get_level_params(difficulty, level)
    min_c, max_c = _coord_bounds(size)
    bounds = (min_c, max_c)
    positions = [
        (x, y, z)
        for x in range(min_c, max_c + 1)
        for y in range(min_c, max_c + 1)
        for z in range(min_c, max_c + 1)
    ]

    min_launchable = params["min_launchable"]
    max_step_bonus = params["max_step_bonus"]
    best_map = None
    best_launchable = -1

    for _ in range(120):
        direction_map = {}
        for pos in positions:
            choices = _candidate_directions(pos, bounds, max_step_bonus)
            random.shuffle(choices)
            direction_map[pos] = choices[0]

        launchable = _launchable_count(direction_map, bounds)
        if not _can_clear_all(direction_map, bounds):
            continue
        if launchable >= min_launchable and launchable > best_launchable:
            best_launchable = launchable
            best_map = dict(direction_map)
        elif best_map is None and launchable > best_launchable:
            best_launchable = launchable
            best_map = dict(direction_map)

    if best_map is None:
        best_map = _tutorial_direction_map(size)

    return best_map


class Grid:
    def __init__(self, difficulty=Difficulty.EASY, level=1):
        params = get_level_params(difficulty, level)
        self.size = params["size"]
        self.difficulty = difficulty
        self.level = level
        self.cubes = []
        self.occupied = {}
        cube_id = 1

        direction_map = _build_direction_map(self.size, difficulty, level)

        for grid_position, direction in direction_map.items():
            cube = Cube(cube_id, grid_position, direction)
            self.cubes.append(cube)
            self.occupied[grid_position] = cube
            cube_id += 1

    @property
    def total_cubes(self):
        return len(self.cubes)

    def cubes_removed_count(self):
        return sum(1 for cube in self.cubes if cube.state == CubeState.REMOVED)

    def unoccupy(self, cube):
        self.occupied.pop(cube.grid_position, None)

    def is_obstructed(self, target_cube):
        if target_cube.state != CubeState.ACTIVE:
            return True

        dx = int(target_cube.direction.x)
        dy = int(target_cube.direction.y)
        dz = int(target_cube.direction.z)
        x, y, z = target_cube.grid_position
        min_c, max_c = _coord_bounds(self.size)

        while True:
            x += dx
            y += dy
            z += dz
            if x < min_c or x > max_c or y < min_c or y > max_c or z < min_c or z > max_c:
                return False
            blocker = self.occupied.get((x, y, z))
            if blocker is not None and blocker is not target_cube:
                if blocker.state in (CubeState.ACTIVE, CubeState.WIGGLING):
                    return True

    def is_empty(self):
        return all(cube.state == CubeState.REMOVED for cube in self.cubes)

    def get_cube_by_id(self, cube_id):
        for cube in self.cubes:
            if cube.id == cube_id:
                return cube
        return None

    def update(self, dt):
        for cube in self.cubes:
            cube.update(dt)
