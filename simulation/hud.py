"""
HUD — full dashboard rendered as semi-transparent panels.
"""
import math
import pygame

_WHITE  = (245, 245, 245)
_BLACK  = (0,   0,   0)
_GREEN  = (60,  210, 100)
_RED    = (220, 60,  60)
_YELLOW = (230, 200, 60)
_BLUE   = (60,  130, 220)
_GRAY   = (100, 100, 110)
_ORANGE = (230, 140, 40)

from .car import MAX_SPEED


class HUD:
    def __init__(self, width: int, height: int):
        self.W = width
        self.H = height
        self.font_b = pygame.font.SysFont('consolas', 17, bold=True)
        self.font_m = pygame.font.SysFont('consolas', 14)
        self.font_s = pygame.font.SysFont('consolas', 12)

    # ── Main draw call ────────────────────────────────────────────────────────
    def draw(self, surf: pygame.Surface, *,
             car, readings: list, planner,
             traffic_lights: list, scenario_name: str,
             mode: str, fps: int,
             reached_goal: bool, show_debug: bool, logging: bool):

        # ── Status panel (top-left) ──────────────────────────────────────────
        self._panel(surf, 8, 8, 330, 138)
        mode_col  = _YELLOW if mode == 'MANUAL' else _GREEN
        stop_col  = _RED if car.collided else _GREEN
        stop_txt  = 'COLLISION !' if car.collided else ('GOAL REACHED' if reached_goal else 'NAVIGATING')

        lines = [
            (f'[{scenario_name}]   {mode}', mode_col),
            (f'Speed    : {car.speed:+7.1f} px/s', _WHITE),
            (f'Gear     : {car.gear}', _WHITE),
            (f'Steer    : {math.degrees(car.steer_angle):+6.1f} deg', _WHITE),
            (f'Throttle : {car.throttle:+.2f}', _WHITE),
            (f'Status   : {stop_txt}', stop_col),
            (f'FPS      : {fps}', _GRAY),
        ]
        for i, (text, col) in enumerate(lines):
            surf.blit(self.font_m.render(text, True, col), (14, 14 + i * 18))

        # ── Speed bar ────────────────────────────────────────────────────────
        self._speed_bar(surf, car, 8, 154)

        # ── Waypoint progress ────────────────────────────────────────────────
        total = len(planner.waypoints)
        done  = min(planner.index, total)
        self._panel(surf, 8, 200, 240, 44)
        surf.blit(self.font_m.render(f'Waypoint: {done}/{total}', True, _WHITE), (14, 205))
        bw  = 220
        pct = done / max(total, 1)
        pygame.draw.rect(surf, _GRAY, (14, 222, bw, 10), border_radius=5)
        pygame.draw.rect(surf, _BLUE, (14, 222, int(bw * pct), 10), border_radius=5)

        # ── Nearest traffic-light indicator ──────────────────────────────────
        lt_state, lt_dist = self._nearest_light(car, traffic_lights)
        if lt_state:
            lc = {'RED': _RED, 'YELLOW': _YELLOW, 'GREEN': _GREEN}.get(lt_state, _WHITE)
            self._panel(surf, 8, 252, 220, 34)
            surf.blit(self.font_m.render(
                f'Signal: {lt_state}  {lt_dist:.0f}px', True, lc), (14, 259))

        # ── Logging indicator ────────────────────────────────────────────────
        if logging:
            txt = self.font_s.render('● REC', True, _RED)
            surf.blit(txt, (self.W - txt.get_width() - 12, 10))

        # ── Controls bar (bottom) ────────────────────────────────────────────
        ctrl = ('[M]Manual/Auto  [G]Sensors  [D]Debug  [P]Pause  '
                '[L]Log  [1][2][3]Scenario  [R]Reset  [ESC]Quit')
        ct   = self.font_s.render(ctrl, True, (110, 110, 120))
        surf.blit(ct, (self.W // 2 - ct.get_width() // 2, self.H - 18))

        # ── Manual mode banner ───────────────────────────────────────────────
        if mode == 'MANUAL':
            txt = self.font_b.render(
                '[ MANUAL MODE — WASD / Arrows ]', True, _YELLOW)
            surf.blit(txt, (self.W // 2 - txt.get_width() // 2, self.H - 44))

        # ── Goal-reached banner ──────────────────────────────────────────────
        if reached_goal:
            txt = self.font_b.render('★  GOAL REACHED!  ★', True, _GREEN)
            surf.blit(txt, (self.W // 2 - txt.get_width() // 2, 22))

        # ── Collision warning ─────────────────────────────────────────────────
        if car.collided:
            txt = self.font_b.render('!! COLLISION !!', True, _RED)
            surf.blit(txt, (self.W // 2 - txt.get_width() // 2, 22))

        # ── Debug overlay ─────────────────────────────────────────────────────
        if show_debug and readings:
            self._debug(surf, car, readings)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _panel(self, surf, x, y, w, h, alpha=190):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((10, 12, 22, alpha))
        surf.blit(s, (x, y))

    def _speed_bar(self, surf, car, x, y):
        self._panel(surf, x, y, 240, 40)
        surf.blit(self.font_s.render('SPEED', True, _GRAY), (x + 6, y + 3))
        bw  = 220
        pct = min(1.0, abs(car.speed) / MAX_SPEED)
        col = _RED if pct > 0.85 else (_YELLOW if pct > 0.5 else _GREEN)
        pygame.draw.rect(surf, _GRAY, (x + 6, y + 22, bw, 10), border_radius=5)
        pygame.draw.rect(surf, col,   (x + 6, y + 22, int(bw * pct), 10), border_radius=5)
        v_txt = self.font_s.render(f'{abs(car.speed):.0f}', True, _WHITE)
        surf.blit(v_txt, (x + 8 + int(bw * pct), y + 22))

    def _debug(self, surf, car, readings):
        rows  = len(readings)
        pw    = 215
        self._panel(surf, self.W - pw - 4, 8, pw, 22 + rows * 13)
        surf.blit(self.font_s.render('SENSOR DEBUG', True, _YELLOW),
                  (self.W - pw, 12))
        for i, r in enumerate(readings):
            deg = math.degrees(r.angle_offset)
            txt = self.font_s.render(
                f'{deg:+6.1f}°  {r.distance:5.1f}  {r.hit_type[:5]}',
                True, _WHITE)
            surf.blit(txt, (self.W - pw, 24 + i * 13))

    @staticmethod
    def _nearest_light(car, traffic_lights):
        best_d, best_s = float('inf'), None
        for tl in traffic_lights:
            d = math.hypot(car.x - tl.x, car.y - tl.y)
            if d < best_d:
                best_d, best_s = d, tl.state
        return best_s, best_d
