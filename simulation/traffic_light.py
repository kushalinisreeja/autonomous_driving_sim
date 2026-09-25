"""
TrafficLight — RED / YELLOW / GREEN cycle with configurable timing.
Drawn as a pole + three-light housing at intersections.
"""
import pygame

_HOUSING = (35, 35, 35)
_DIM = {
    'RED':    (60, 20, 20),
    'YELLOW': (55, 50, 15),
    'GREEN':  (15, 55, 25),
}
_BRIGHT = {
    'RED':    (220, 60,  60),
    'YELLOW': (230, 200, 60),
    'GREEN':  (60,  210, 100),
}
_TIMINGS = {
    'GREEN':  5.0,
    'YELLOW': 1.5,
    'RED':    4.5,
}
_CYCLE = ['GREEN', 'YELLOW', 'RED']


class TrafficLight:
    def __init__(self, x: int, y: int,
                 initial_state: str = 'RED',
                 phase_offset:  float = 0.0):
        self.x     = x
        self.y     = y
        self.state = initial_state
        # Advance timer so lights are not all in sync
        self.timer = phase_offset % _TIMINGS[initial_state]

    # ── Properties ───────────────────────────────────────────────────────────
    @property
    def color(self):
        return _BRIGHT[self.state]

    def is_stop(self) -> bool:
        """Returns True when the ego car should stop/brake."""
        return self.state in ('RED', 'YELLOW')

    # ── Update ───────────────────────────────────────────────────────────────
    def update(self, dt: float):
        self.timer += dt
        if self.timer >= _TIMINGS[self.state]:
            self.timer = 0.0
            idx        = _CYCLE.index(self.state)
            self.state = _CYCLE[(idx + 1) % len(_CYCLE)]

    # ── Rendering ────────────────────────────────────────────────────────────
    def draw(self, surf: pygame.Surface):
        # Pole
        pygame.draw.line(surf, (60, 60, 60),
                         (self.x, self.y + 8),
                         (self.x, self.y + 30), 3)
        # Housing background
        pygame.draw.rect(surf, _HOUSING,
                         (self.x - 10, self.y - 34, 20, 44),
                         border_radius=4)
        # Three lights top→bottom: RED, YELLOW, GREEN
        for i, s in enumerate(['RED', 'YELLOW', 'GREEN']):
            cy  = self.y - 26 + i * 15
            col = _BRIGHT[s] if self.state == s else _DIM[s]
            pygame.draw.circle(surf, col, (self.x, cy), 6)
        # State label
        # (drawn by HUD; not here to avoid font dependency)
