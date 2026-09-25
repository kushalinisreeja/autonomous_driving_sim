"""
Autonomous Driving Logic Simulation — main entry point
=======================================================
Controls
--------
  1 / 2 / 3    Select scenario
  R            Reset current scenario
  M            Toggle Manual / Autonomous mode
  G            Toggle LiDAR sensor ray display
  D            Toggle debug sensor table
  P            Pause / unpause
  L            Toggle CSV data logging (saved to logs/)
  ESC / Q      Quit

Manual-mode controls (WASD or Arrow keys):
  W / ↑        Accelerate
  S / ↓        Brake / reverse
  A / ←        Steer left
  D / →        Steer right
"""
import math
import sys
import pygame
from pygame.locals import (
    K_ESCAPE, K_q, K_r, K_g, K_d, K_m, K_p, K_l,
    K_1, K_2, K_3,
    K_w, K_a, K_s, K_RIGHT, K_LEFT, K_UP, K_DOWN,
)

from simulation.scenario    import build_scenario
from simulation.sensors     import LiDARSensor
from simulation.controller  import compute_control
from simulation.hud         import HUD
from simulation.logger      import DataLogger

# ── Config ───────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1000, 700
FPS           = 60
DT            = 1.0 / FPS
BG_COLOR      = (28, 34, 28)   # dark-green aerial tint


# ── Collision helper ─────────────────────────────────────────────────────────
def _check_collisions(car, obstacles, traffic_cars, width, height) -> bool:
    margin = 15
    if car.x < margin or car.x > width - margin:
        return True
    if car.y < margin or car.y > height - margin:
        return True
    for obs in obstacles:
        if math.hypot(car.x - obs.x, car.y - obs.y) < obs.r + 10:
            return True
    for tc in traffic_cars:
        if math.hypot(car.x - tc.x, car.y - tc.y) < 22:
            return True
    return False


# ── Scenario loader ──────────────────────────────────────────────────────────
def load_scenario(num: int):
    sc = build_scenario(num)
    return (
        sc['car'],
        sc['planner'],
        sc['roads'],
        sc['intersections'],
        sc['traffic_lights'],
        sc['traffic_cars'],
        sc['obstacles'],
        sc['speed_zones'],
        sc['name'],
    )


# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Autonomous Driving Logic Simulation')
    zone_font = pygame.font.SysFont('consolas', 13)
    clock     = pygame.time.Clock()
    font_s    = pygame.font.SysFont('consolas', 12)

    lidar  = LiDARSensor(num_rays=18, fov_deg=210, max_range=210)
    hud    = HUD(WIDTH, HEIGHT)
    logger = DataLogger()

    # ── State ────────────────────────────────────────────────────────────────
    scenario_num = 1
    (car, planner, roads, intersections,
     traffic_lights, traffic_cars, obstacles,
     speed_zones, sc_name) = load_scenario(scenario_num)

    show_sensors  = True
    show_debug    = False
    paused        = False
    manual_mode   = False
    reached_goal  = False
    readings      = []

    running = True
    while running:
        # ── Events ────────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (K_ESCAPE, K_q):
                    running = False

                elif event.key == K_r:
                    (car, planner, roads, intersections,
                     traffic_lights, traffic_cars, obstacles,
                     speed_zones, sc_name) = load_scenario(scenario_num)
                    reached_goal = False
                    readings     = []

                elif event.key == K_1:
                    scenario_num = 1
                    (car, planner, roads, intersections,
                     traffic_lights, traffic_cars, obstacles,
                     speed_zones, sc_name) = load_scenario(1)
                    reached_goal = False
                    readings     = []

                elif event.key == K_2:
                    scenario_num = 2
                    (car, planner, roads, intersections,
                     traffic_lights, traffic_cars, obstacles,
                     speed_zones, sc_name) = load_scenario(2)
                    reached_goal = False
                    readings     = []

                elif event.key == K_3:
                    scenario_num = 3
                    (car, planner, roads, intersections,
                     traffic_lights, traffic_cars, obstacles,
                     speed_zones, sc_name) = load_scenario(3)
                    reached_goal = False
                    readings     = []

                elif event.key == K_g:
                    show_sensors = not show_sensors

                elif event.key == K_d:
                    show_debug = not show_debug

                elif event.key == K_m:
                    manual_mode = not manual_mode

                elif event.key == K_p:
                    paused = not paused

                elif event.key == K_l:
                    logger.enabled = not logger.enabled
                    if logger.enabled:
                        print(f'[LOG] Recording to {logger.path}')
                    else:
                        print('[LOG] Paused')

        # ── Simulation step ───────────────────────────────────────────────────
        if not paused:
            # Update world objects
            for obs in obstacles:
                obs.update(DT)
            for tc in traffic_cars:
                tc.update(DT, traffic_lights, traffic_cars)
            for tl in traffic_lights:
                tl.update(DT)

            # Sensor scan
            readings = lidar.scan(car, obstacles, traffic_cars, WIDTH, HEIGHT)

            # Active speed limit from zones
            speed_limit = 160.0
            for zone in speed_zones:
                if zone.contains(car.x, car.y):
                    speed_limit = min(speed_limit, zone.speed_limit)

            # ── Control ───────────────────────────────────────────────────────
            if not reached_goal:
                if manual_mode:
                    keys = pygame.key.get_pressed()
                    car.throttle  = 0.0
                    car.steer_cmd = 0.0
                    if keys[K_w] or keys[K_UP]:
                        car.throttle = 1.0
                    if keys[K_s] or keys[K_DOWN]:
                        car.throttle = -1.0
                    if keys[K_a] or keys[K_LEFT]:
                        car.steer_cmd = -1.0
                    if keys[K_RIGHT]:
                        car.steer_cmd = 1.0
                else:
                    # Auto: advance waypoint planner
                    planner.update(car.x, car.y)
                    goal = planner.current_goal
                    throttle, steer = compute_control(
                        car, readings, goal,
                        traffic_lights=traffic_lights,
                        speed_limit=speed_limit,
                    )
                    car.throttle  = throttle
                    car.steer_cmd = steer

            else:
                # Decelerate to stop after reaching goal
                car.throttle  = -0.5 if abs(car.speed) > 1 else 0.0
                car.steer_cmd = 0.0

            car.update(DT)

            # Boundary soft clamp (wall bounce)
            margin = 18
            if car.x < margin:
                car.x = margin;  car.speed *= 0.2
            if car.x > WIDTH - margin:
                car.x = WIDTH - margin;  car.speed *= 0.2
            if car.y < margin:
                car.y = margin;  car.speed *= 0.2
            if car.y > HEIGHT - margin:
                car.y = HEIGHT - margin;  car.speed *= 0.2

            # Collision detection
            car.collided = _check_collisions(
                car, obstacles, traffic_cars, WIDTH, HEIGHT)

            # Goal check (last waypoint)
            if not reached_goal and planner.done:
                reached_goal = True
                print(f'[SIM] Goal reached in scenario: {sc_name}')

            # Log
            logger.log(car, readings)

        # ── Rendering ─────────────────────────────────────────────────────────
        screen.fill(BG_COLOR)

        # Roads (drawn back-to-front: segments → intersections)
        for road in roads:
            road.draw(screen)
        for inter in intersections:
            inter.draw(screen)

        # Speed zone outlines
        for zone in speed_zones:
            zone.draw(screen, font_s)

        # Planned path
        planner.draw(screen)

        # Sensors (behind car but on top of roads)
        if show_sensors:
            lidar.draw(screen, car, readings)

        # Moving world objects
        for obs in obstacles:
            obs.draw(screen)
        for tc in traffic_cars:
            tc.draw(screen)
        for tl in traffic_lights:
            tl.draw(screen)

        # Ego car
        car.draw(screen)

        # Pause overlay
        if paused:
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 100))
            screen.blit(s, (0, 0))
            pause_font = pygame.font.SysFont('consolas', 40, bold=True)
            pt = pause_font.render('PAUSED — press P to resume', True, (230, 200, 60))
            screen.blit(pt, (WIDTH // 2 - pt.get_width() // 2, HEIGHT // 2 - 20))

        # HUD
        hud.draw(
            screen,
            car=car, readings=readings, planner=planner,
            traffic_lights=traffic_lights,
            scenario_name=sc_name,
            mode='MANUAL' if manual_mode else 'AUTO',
            fps=int(clock.get_fps()),
            reached_goal=reached_goal,
            show_debug=show_debug,
            logging=logger.enabled,
        )

        pygame.display.flip()
        clock.tick(FPS)

    # ── Cleanup ───────────────────────────────────────────────────────────────
    logger.close()
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()