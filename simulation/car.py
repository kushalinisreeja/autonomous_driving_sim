"""
Car — kinematic bicycle model with gear indicator, trail, and collision state.
"""
import math
import pygame

# ── Physical constants ──────────────────────────────────────────────────────
CAR_LENGTH        = 28
CAR_WIDTH         = 14
MAX_SPEED         = 160.0          # px / s  forward
MAX_REVERSE_SPEED = -55.0          # px / s  reverse
MAX_ACCEL         = 90.0           # px / s²
MAX_BRAKE         = 180.0          # px / s²
MAX_STEER_ANGLE   = math.radians(35)
STEER_RATE        = math.radians(90)   # max steer change / s
DRAG              = 0.014          # fractional speed loss per frame

TRAIL_MAX = 90

# ── Colours ─────────────────────────────────────────────────────────────────
_BLUE  = (60, 130, 220)
_RED   = (220, 60,  60)
_WHITE = (245, 245, 245)


class Car:
    def __init__(self, x: float, y: float, heading: float = 0.0):
        self.x        = x
        self.y        = y
        self.heading  = heading        # radians
        self.speed    = 0.0            # px/s  (+forward / -reverse)
        self.steer_angle = 0.0         # current wheel angle (radians)

        # Controller outputs (set externally each frame)
        self.throttle  = 0.0           # −1 … +1
        self.steer_cmd = 0.0           # −1 … +1

        # State
        self.gear    = 'N'             # 'D' / 'N' / 'R'
        self.collided = False
        self.trail    = []             # [(x, y), ...]

    # ── Physics update ───────────────────────────────────────────────────────
    def update(self, dt: float):
        # 1. Steer angle moves toward commanded value
        target = self.steer_cmd * MAX_STEER_ANGLE
        delta  = max(-STEER_RATE * dt, min(STEER_RATE * dt, target - self.steer_angle))
        self.steer_angle += delta

        # 2. Longitudinal acceleration / braking
        accel = self.throttle * (MAX_ACCEL if self.throttle >= 0 else MAX_BRAKE)
        self.speed += accel * dt
        self.speed *= (1.0 - DRAG)          # rolling friction / air drag
        self.speed  = max(MAX_REVERSE_SPEED, min(MAX_SPEED, self.speed))

        # 3. Gear indicator
        if   self.speed >  0.5: self.gear = 'D'
        elif self.speed < -0.5: self.gear = 'R'
        else:                   self.gear = 'N'

        # 4. Kinematic bicycle model
        if abs(self.steer_angle) > 1e-4:
            turn_r  = CAR_LENGTH / math.tan(self.steer_angle)
            ang_vel = self.speed / turn_r
        else:
            ang_vel = 0.0

        self.heading += ang_vel * dt
        self.x += self.speed * math.cos(self.heading) * dt
        self.y += self.speed * math.sin(self.heading) * dt

        # 5. Trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > TRAIL_MAX:
            self.trail.pop(0)

    # ── Geometry ─────────────────────────────────────────────────────────────
    def get_corners(self):
        """Return the four corner points of the car bounding box."""
        ch, sh = math.cos(self.heading), math.sin(self.heading)
        hl, hw = CAR_LENGTH / 2, CAR_WIDTH / 2
        corners = []
        for (dx, dy) in [(-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw)]:
            corners.append((
                dx * ch - dy * sh + self.x,
                dx * sh + dy * ch + self.y,
            ))
        return corners

    # ── Rendering ────────────────────────────────────────────────────────────
    def draw(self, surf: pygame.Surface):
        # Trail (fading)
        trail = self.trail
        n = len(trail)
        if n > 1:
            for i in range(n - 1):
                brightness = int(60 * i / n)
                pygame.draw.line(
                    surf,
                    (brightness, brightness, 80 + brightness),
                    (int(trail[i][0]),   int(trail[i][1])),
                    (int(trail[i+1][0]), int(trail[i+1][1])),
                    1,
                )

        # Car body
        pts   = [(int(c[0]), int(c[1])) for c in self.get_corners()]
        color = _RED if self.collided else _BLUE
        pygame.draw.polygon(surf, color, pts)

        # Heading indicator
        hx = self.x + (CAR_LENGTH / 2 + 5) * math.cos(self.heading)
        hy = self.y + (CAR_LENGTH / 2 + 5) * math.sin(self.heading)
        pygame.draw.line(surf, _WHITE,
                         (int(self.x), int(self.y)),
                         (int(hx), int(hy)), 2)
