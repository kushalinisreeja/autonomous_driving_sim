"""
Road geometry — segments, intersections, and speed-zone circles.
All drawing is pure pygame (no external assets required).
"""
import math
import pygame

_ASPHALT     = (48,  50,  55)
_CENTER_LINE = (200, 200, 80)
_SHOULDER    = (160, 140, 80)
_CROSS_WALK  = (180, 180, 180)
_ZONE_RING   = (180, 80,  80)
_ZONE_TEXT   = (200, 100, 100)


class RoadSegment:
    """A straight road strip between two points."""

    def __init__(self, x1, y1, x2, y2, width: int = 60, speed_limit: float = 120):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.width       = width
        self.speed_limit = speed_limit

    def draw(self, surf: pygame.Surface):
        # Road surface
        pygame.draw.line(surf, _ASPHALT,
                         (self.x1, self.y1), (self.x2, self.y2),
                         self.width)
        # Shoulder lines
        angle   = math.atan2(self.y2 - self.y1, self.x2 - self.x1) + math.pi / 2
        off     = self.width // 2 - 4
        for sign in (1, -1):
            ox = sign * off * math.cos(angle)
            oy = sign * off * math.sin(angle)
            pygame.draw.line(surf, _SHOULDER,
                             (int(self.x1 + ox), int(self.y1 + oy)),
                             (int(self.x2 + ox), int(self.y2 + oy)), 2)
        # Dashed center line
        self._dashed_line(surf, _CENTER_LINE, 12, 9, 1)

    def _dashed_line(self, surf, color, dash, gap, width):
        length = math.hypot(self.x2 - self.x1, self.y2 - self.y1)
        if length < 1:
            return
        dx = (self.x2 - self.x1) / length
        dy = (self.y2 - self.y1) / length
        pos = 0.0
        while pos < length:
            end = min(pos + dash, length)
            sx, sy = self.x1 + dx * pos, self.y1 + dy * pos
            ex, ey = self.x1 + dx * end, self.y1 + dy * end
            pygame.draw.line(surf, color,
                             (int(sx), int(sy)), (int(ex), int(ey)), width)
            pos += dash + gap


class Intersection:
    """Square junction that visually fills crossing roads."""

    def __init__(self, x, y, size: int = 70):
        self.x, self.y, self.size = x, y, size

    def draw(self, surf: pygame.Surface):
        s  = self.size
        hx = self.x - s // 2
        hy = self.y - s // 2
        pygame.draw.rect(surf, _ASPHALT, (hx, hy, s, s))
        # Crosswalk stripes on all four sides
        stripe_w = 6
        num_stripes = 4
        for i in range(num_stripes):
            offset = 6 + i * (stripe_w + 3)
            # Bottom crosswalk
            pygame.draw.rect(surf, _CROSS_WALK,
                             (hx + offset, hy + s - 8, stripe_w, 8))
            # Top crosswalk
            pygame.draw.rect(surf, _CROSS_WALK,
                             (hx + offset, hy, stripe_w, 8))
            # Left crosswalk
            pygame.draw.rect(surf, _CROSS_WALK,
                             (hx, hy + offset, 8, stripe_w))
            # Right crosswalk
            pygame.draw.rect(surf, _CROSS_WALK,
                             (hx + s - 8, hy + offset, 8, stripe_w))


class SpeedZone:
    """A circular area with a custom speed limit."""

    def __init__(self, x, y, radius: float, speed_limit: float, label: str = ''):
        self.x, self.y   = x, y
        self.radius       = radius
        self.speed_limit  = speed_limit
        self.label        = label

    def contains(self, x, y) -> bool:
        return math.hypot(x - self.x, y - self.y) < self.radius

    def draw(self, surf: pygame.Surface, font=None):
        pygame.draw.circle(surf, _ZONE_RING,
                           (int(self.x), int(self.y)), int(self.radius), 1)
        if font and self.label:
            txt = font.render(self.label, True, _ZONE_TEXT)
            surf.blit(txt, (int(self.x) - txt.get_width() // 2,
                            int(self.y) - txt.get_height() // 2))
