"""
Obstacle — circular static or moving hazards.
"""
import random
import pygame

WIDTH,  HEIGHT = 1000, 700
_GRAY   = (90,  90,  90)
_ORANGE = (230, 140, 40)


class Obstacle:
    def __init__(self, x: float, y: float, r: float, moving: bool = False):
        self.x, self.y, self.r = float(x), float(y), float(r)
        self.moving = moving
        if moving:
            self.vx = random.uniform(-30, 30)
            self.vy = random.uniform(-30, 30)
        else:
            self.vx = self.vy = 0.0

    def update(self, dt: float):
        if not self.moving:
            return
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.x < self.r or self.x > WIDTH  - self.r: self.vx *= -1
        if self.y < self.r or self.y > HEIGHT - self.r: self.vy *= -1

    def draw(self, surf: pygame.Surface):
        cx, cy = int(self.x), int(self.y)
        base   = _ORANGE if self.moving else _GRAY
        pygame.draw.circle(surf, base, (cx, cy), int(self.r))
        # Highlight ring
        hi = tuple(min(c + 50, 255) for c in base)
        pygame.draw.circle(surf, hi, (cx, cy), int(self.r), 2)
