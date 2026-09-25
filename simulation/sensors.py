"""
LiDAR sensor — ray-cast fan returning structured hit data.
Color-coded by threat level: red (danger) / yellow (caution) / dim (clear).
"""
import math
import pygame
from dataclasses import dataclass

# Threat thresholds (px)
CRIT_DIST   = 35.0
CAUTION_DIST = 85.0

# Hit-type colours
_TYPE_COLORS = {
    'obstacle': (220, 60,  60),
    'traffic':  (230, 140, 40),
    'wall':     (160, 60, 200),
    'clear':    (40,  40,  65),
}


@dataclass
class SensorReading:
    angle_offset: float   # relative to car heading (radians)
    distance:     float   # px to nearest hit
    hit_type:     str     # 'clear' | 'obstacle' | 'traffic' | 'wall'


class LiDARSensor:
    def __init__(self, num_rays: int = 16, fov_deg: float = 200, max_range: float = 200):
        self.num_rays  = num_rays
        self.fov       = math.radians(fov_deg)
        self.max_range = max_range

    # ── Main scan ────────────────────────────────────────────────────────────
    def scan(self, car, obstacles, traffic_cars=None,
             width: int = 1000, height: int = 700) -> list:
        traffic_cars = traffic_cars or []
        readings     = []
        half_fov     = self.fov / 2
        n            = self.num_rays

        for i in range(n):
            t      = i / (n - 1) if n > 1 else 0.0
            offset = -half_fov + t * self.fov
            angle  = car.heading + offset
            dist, hit = self._cast(car.x, car.y, angle, obstacles, traffic_cars, width, height)
            readings.append(SensorReading(offset, dist, hit))
        return readings

    # ── Ray casting ──────────────────────────────────────────────────────────
    def _cast(self, ox, oy, angle, obstacles, traffic_cars, W, H):
        dx, dy     = math.cos(angle), math.sin(angle)
        best_dist  = self.max_range
        best_type  = 'clear'

        # Circular obstacles
        for obs in obstacles:
            d = self._ray_circle(ox, oy, dx, dy, obs.x, obs.y, obs.r)
            if d is not None and d < best_dist:
                best_dist, best_type = d, 'obstacle'

        # Traffic cars (approximated as circles)
        for tc in traffic_cars:
            d = self._ray_circle(ox, oy, dx, dy, tc.x, tc.y, 14)
            if d is not None and d < best_dist:
                best_dist, best_type = d, 'traffic'

        # Axis-aligned walls
        for wd in self._wall_dists(ox, oy, dx, dy, W, H):
            if 0 < wd < best_dist:
                best_dist, best_type = wd, 'wall'

        return best_dist, best_type

    # ── Geometry helpers ─────────────────────────────────────────────────────
    @staticmethod
    def _ray_circle(ox, oy, dx, dy, cx, cy, r):
        """Analytic ray-circle intersection.  Returns hit distance or None."""
        ex, ey = cx - ox, cy - oy
        proj   = ex * dx + ey * dy
        if proj < 0:
            return None
        px, py = ox + proj * dx, oy + proj * dy
        d2c    = math.hypot(cx - px, cy - py)
        if d2c > r:
            return None
        back = math.sqrt(max(0.0, r * r - d2c * d2c))
        hit  = proj - back
        return hit if hit >= 0 else None

    @staticmethod
    def _wall_dists(x, y, dx, dy, W, H):
        dists = []
        if   dx >  1e-6: dists.append((W - x) / dx)
        elif dx < -1e-6: dists.append((-x)    / dx)
        if   dy >  1e-6: dists.append((H - y) / dy)
        elif dy < -1e-6: dists.append((-y)    / dy)
        return dists

    # ── Rendering ────────────────────────────────────────────────────────────
    def draw(self, surf: pygame.Surface, car, readings: list):
        for r in readings:
            ang = car.heading + r.angle_offset
            ex  = car.x + r.distance * math.cos(ang)
            ey  = car.y + r.distance * math.sin(ang)

            if r.distance < CRIT_DIST:
                color = (220, 60, 60)
            elif r.distance < CAUTION_DIST:
                color = (230, 200, 60)
            else:
                color = _TYPE_COLORS.get(r.hit_type, (40, 40, 65))

            pygame.draw.line(surf, color,
                             (int(car.x), int(car.y)),
                             (int(ex),    int(ey)), 1)
            # Endpoint dot for hits
            if r.hit_type != 'clear':
                pygame.draw.circle(surf, color, (int(ex), int(ey)), 3)
