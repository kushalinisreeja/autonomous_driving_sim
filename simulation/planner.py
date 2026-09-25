"""
WaypointPlanner — sequences a list of (x, y) waypoints,
advances as the car arrives, and renders the planned path.
"""
import math
import pygame

_ARRIVE_R   = 38.0    # px — radius within which a waypoint is considered reached
_PATH_COLOR = (55, 100, 170)
_WP_FUTURE  = (70,  70, 140)
_WP_CURRENT = (230, 200, 60)
_WP_DONE    = (50,  110, 50)
_GOAL_COLOR = (60,  210, 100)


def _dashed_line(surf, color, start, end, dash=12, gap=7, width=1):
    x1, y1 = start
    x2, y2 = end
    length  = math.hypot(x2 - x1, y2 - y1)
    if length < 1:
        return
    dx, dy = (x2 - x1) / length, (y2 - y1) / length
    pos = 0.0
    while pos < length:
        e = min(pos + dash, length)
        pygame.draw.line(surf, color,
                         (int(x1 + dx * pos), int(y1 + dy * pos)),
                         (int(x1 + dx * e),   int(y1 + dy * e)), width)
        pos += dash + gap


class WaypointPlanner:
    def __init__(self, waypoints: list):
        """
        Args:
            waypoints: ordered list of (x, y) tuples.
                       The last one is treated as the final goal.
        """
        assert len(waypoints) >= 1
        self.waypoints = list(waypoints)
        self.index     = 0   # index of the *current* target waypoint

    # ── Accessors ─────────────────────────────────────────────────────────────
    @property
    def done(self) -> bool:
        return self.index >= len(self.waypoints)

    @property
    def current_goal(self) -> tuple:
        """Return the current target (x, y).  Clamps to last if finished."""
        idx = min(self.index, len(self.waypoints) - 1)
        return self.waypoints[idx]

    # ── Update ────────────────────────────────────────────────────────────────
    def update(self, car_x: float, car_y: float):
        """Call each frame; advances waypoint index when car is close enough."""
        if self.done:
            return
        gx, gy = self.current_goal
        if math.hypot(car_x - gx, car_y - gy) < _ARRIVE_R:
            self.index += 1

    # ── Rendering ─────────────────────────────────────────────────────────────
    def draw(self, surf: pygame.Surface):
        wps = self.waypoints
        n   = len(wps)

        # Dashed path lines
        for i in range(n - 1):
            _dashed_line(surf, _PATH_COLOR, wps[i], wps[i + 1])

        # Waypoint dots
        for i, (wx, wy) in enumerate(wps):
            if i < self.index:
                col, r = _WP_DONE,    5   # visited
            elif i == self.index:
                col, r = _WP_CURRENT, 7   # current target (highlighted)
            else:
                col, r = _WP_FUTURE,  4   # upcoming

            pygame.draw.circle(surf, col, (int(wx), int(wy)), r)

        # Final-goal marker (large ring)
        fx, fy = wps[-1]
        pygame.draw.circle(surf, _GOAL_COLOR, (int(fx), int(fy)), 18, 3)
        pygame.draw.circle(surf, _GOAL_COLOR, (int(fx), int(fy)),  6)
