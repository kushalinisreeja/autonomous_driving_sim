"""
TrafficCar — autonomous NPC vehicle that follows waypoints,
stops at red lights, and maintains a safe following distance.
"""
import math
import random
import pygame

_TC_LEN  = 26
_TC_W    = 13
_COLORS  = [
    (180, 80,  80),
    (80,  80,  180),
    (80,  160, 80),
    (160, 80,  160),
    (160, 140, 60),
    (80,  160, 160),
]

_STOP_RADIUS    = 80.0    # px — brake for red light within this dist
_FOLLOW_RADIUS  = 55.0    # px — maintain distance from traffic ahead
_MAX_STEER_RATE = math.radians(120)   # rad/s


def _wrap(a: float) -> float:
    while a >  math.pi: a -= 2 * math.pi
    while a < -math.pi: a += 2 * math.pi
    return a


class TrafficCar:
    def __init__(self, waypoints: list,
                 speed: float = None,
                 color: tuple  = None,
                 start_index:  int = 1):
        assert len(waypoints) >= 2, "Need at least 2 waypoints."
        self.waypoints = list(waypoints)
        self.index     = start_index % len(waypoints)

        x0, y0 = waypoints[start_index - 1]
        self.x, self.y = float(x0), float(y0)

        # Initial heading toward first target
        x1, y1 = waypoints[self.index]
        self.heading = math.atan2(y1 - y0, x1 - x0)

        self._nominal_speed = speed or random.uniform(55, 95)
        self._cur_speed     = self._nominal_speed * 0.5
        self.color          = color or random.choice(_COLORS)

    # ── Update ───────────────────────────────────────────────────────────────
    def update(self, dt: float, traffic_lights=None, other_traffic=None):
        traffic_lights = traffic_lights or []
        other_traffic  = other_traffic  or []

        # ── Decide target speed ──────────────────────────────────────────────
        target_speed = self._nominal_speed

        # Stop for red/yellow lights
        for tl in traffic_lights:
            if tl.is_stop() and math.hypot(self.x - tl.x, self.y - tl.y) < _STOP_RADIUS:
                target_speed = 0.0
                break

        # Keep following distance from traffic ahead
        if target_speed > 0:
            for other in other_traffic:
                if other is self:
                    continue
                d = math.hypot(self.x - other.x, self.y - other.y)
                if d < _FOLLOW_RADIUS:
                    # Scale speed down
                    target_speed = min(target_speed,
                                       self._nominal_speed * (d / _FOLLOW_RADIUS))

        # Smooth speed change
        rate = 50 * dt if target_speed > self._cur_speed else 100 * dt
        if target_speed > self._cur_speed:
            self._cur_speed = min(target_speed, self._cur_speed + rate)
        else:
            self._cur_speed = max(target_speed, self._cur_speed - rate)

        if self._cur_speed < 0.5:
            return   # stopped — no position update

        # ── Steer toward current waypoint ───────────────────────────────────
        gx, gy  = self.waypoints[self.index]
        desired = math.atan2(gy - self.y, gx - self.x)
        err     = _wrap(desired - self.heading)
        max_d   = _MAX_STEER_RATE * dt
        self.heading += max(-max_d, min(max_d, err))

        # ── Move ─────────────────────────────────────────────────────────────
        self.x += self._cur_speed * math.cos(self.heading) * dt
        self.y += self._cur_speed * math.sin(self.heading) * dt

        # ── Advance waypoint (loop) ──────────────────────────────────────────
        if math.hypot(self.x - gx, self.y - gy) < 28:
            self.index = (self.index + 1) % len(self.waypoints)

    # ── Rendering ────────────────────────────────────────────────────────────
    def draw(self, surf: pygame.Surface):
        ch, sh = math.cos(self.heading), math.sin(self.heading)
        hl, hw = _TC_LEN / 2, _TC_W / 2
        pts = []
        for dx, dy in [(-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw)]:
            pts.append((int(dx * ch - dy * sh + self.x),
                        int(dx * sh + dy * ch + self.y)))
        pygame.draw.polygon(surf, self.color, pts)
        # Windshield marker
        hx = int(self.x + hl * ch)
        hy = int(self.y + hl * sh)
        pygame.draw.line(surf, (200, 200, 200),
                         (int(self.x), int(self.y)), (hx, hy), 1)
