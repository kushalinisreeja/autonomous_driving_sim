"""
Data logger — records per-frame telemetry to a timestamped CSV file.
Toggle with the L key in-game.
"""
import os
import csv
import math
from datetime import datetime


class DataLogger:
    HEADERS = [
        'frame', 'x', 'y', 'heading_deg', 'speed_px_s',
        'throttle', 'steer_deg', 'gear',
        'min_sensor_dist', 'num_hits', 'collided',
    ]

    def __init__(self, log_dir: str = 'logs'):
        os.makedirs(log_dir, exist_ok=True)
        ts        = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.path = os.path.join(log_dir, f'run_{ts}.csv')
        self._file   = open(self.path, 'w', newline='', encoding='utf-8')
        self._writer = csv.writer(self._file)
        self._writer.writerow(self.HEADERS)
        self._frame   = 0
        self.enabled  = False   # toggled by main loop

    def log(self, car, readings: list):
        if not self.enabled:
            return
        if readings:
            min_d   = min(r.distance for r in readings)
            num_hit = sum(1 for r in readings if r.hit_type != 'clear')
        else:
            min_d, num_hit = 999.0, 0

        self._writer.writerow([
            self._frame,
            f'{car.x:.1f}',
            f'{car.y:.1f}',
            f'{math.degrees(car.heading):.1f}',
            f'{car.speed:.2f}',
            f'{car.throttle:.3f}',
            f'{math.degrees(car.steer_angle):.1f}',
            car.gear,
            f'{min_d:.1f}',
            num_hit,
            int(car.collided),
        ])
        self._frame += 1

    def close(self):
        self._file.flush()
        self._file.close()
