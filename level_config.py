from enum import Enum

class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

MAX_LEVEL = 10


def get_level_params(difficulty, level):
    """Return grid size and generation targets for a difficulty/level pair."""
    level = max(1, min(MAX_LEVEL, int(level)))

    if difficulty == Difficulty.EASY:
        if level <= 3:
            return {"size": 2, "min_launchable": 5, "max_step_bonus": 0}
        if level <= 6:
            return {"size": 3, "min_launchable": 10, "max_step_bonus": 0}
        return {"size": 3, "min_launchable": 7, "max_step_bonus": 0}

    if difficulty == Difficulty.MEDIUM:
        if level <= 4:
            return {"size": 3, "min_launchable": 7, "max_step_bonus": 1}
        if level <= 7:
            return {"size": 3, "min_launchable": 4, "max_step_bonus": 1}
        return {"size": 4, "min_launchable": 6, "max_step_bonus": 1}

    if level <= 3:
        return {"size": 3, "min_launchable": 4, "max_step_bonus": 2}
    if level <= 7:
        return {"size": 4, "min_launchable": 3, "max_step_bonus": 2}
    return {"size": 4, "min_launchable": 2, "max_step_bonus": 2}

def difficulty_label(difficulty):
    return difficulty.value.upper()

def projection_size_for_grid(grid_size):
    return 3.2 + grid_size * 1.85
