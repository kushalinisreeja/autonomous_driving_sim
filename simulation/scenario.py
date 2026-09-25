"""
Three built-in scenarios:
  1 – City Block  : grid roads, traffic lights, 5 NPC cars
  2 – Highway     : curved high-speed stretch, dense traffic
  3 – Parking Lot : tight lanes, static parked cars, slow speed

Each build_* function returns a dict with the keys expected by main.py:
    car, planner, roads, intersections, traffic_lights,
    traffic_cars, obstacles, speed_zones, name
"""
from .car          import Car
from .obstacle     import Obstacle
from .traffic      import TrafficCar
from .traffic_light import TrafficLight
from .road         import RoadSegment, Intersection, SpeedZone
from .planner      import WaypointPlanner

W, H = 1000, 700   # canvas size


# ── Public entry-point ────────────────────────────────────────────────────────
def build_scenario(num: int) -> dict:
    builders = {1: _city_block, 2: _highway, 3: _parking_lot}
    return builders.get(num, _city_block)()


# ═══════════════════════════════════════════════════════════════════════════════
# Scenario 1 – City Block
# ═══════════════════════════════════════════════════════════════════════════════
def _city_block() -> dict:
    # ── Ego route: S-path across the city grid ──────────────────────────────
    ego_wps = [
        ( 70, 350),   # start
        (300, 350),   # first junction
        (300, 150),   # turn up
        (500, 150),   # across top
        (700, 150),   # top right
        (700, 350),   # down to middle
        (700, 550),   # down to bottom
        (500, 550),   # across bottom
        (300, 550),   # bottom left junction
        (300, 350),   # back to middle row
        (500, 350),   # mid cross
        (930, 350),   # GOAL
    ]
    car     = Car(70, 350, heading=0.0)
    planner = WaypointPlanner(ego_wps)

    # ── Roads ────────────────────────────────────────────────────────────────
    roads = [
        # Horizontal
        RoadSegment( 50, 350, 950, 350, width=62, speed_limit=100),
        RoadSegment( 50, 150, 950, 150, width=62, speed_limit= 80),
        RoadSegment( 50, 550, 950, 550, width=62, speed_limit= 80),
        # Vertical
        RoadSegment(300,  50, 300, 650, width=62, speed_limit= 80),
        RoadSegment(700,  50, 700, 650, width=62, speed_limit= 80),
    ]

    intersections = [
        Intersection(300, 150), Intersection(700, 150),
        Intersection(300, 350), Intersection(700, 350),
        Intersection(300, 550), Intersection(700, 550),
    ]

    traffic_lights = [
        TrafficLight(300, 150, 'RED',    phase_offset=0.0),
        TrafficLight(700, 150, 'GREEN',  phase_offset=2.5),
        TrafficLight(300, 350, 'GREEN',  phase_offset=1.0),
        TrafficLight(700, 350, 'RED',    phase_offset=3.5),
        TrafficLight(300, 550, 'YELLOW', phase_offset=0.8),
        TrafficLight(700, 550, 'GREEN',  phase_offset=4.2),
    ]

    # ── NPC traffic cars — each loops its own grid segment ──────────────────
    tc_routes = [
        [(300, 150), (700, 150), (700, 350), (300, 350)],
        [(700, 150), (700, 350), (700, 550), (300, 550)],
        [(300, 350), (300, 150), (500, 150), (700, 150)],
        [(700, 350), (300, 350), (300, 550), (500, 550)],
        [(500, 150), (700, 150), (700, 350), (500, 350)],
    ]
    traffic_cars = []
    for i, route in enumerate(tc_routes):
        si = (i * 2) % len(route)
        traffic_cars.append(TrafficCar(
            route,
            start_index=max(1, si),
        ))

    obstacles = [
        Obstacle(480, 290,  18),
        Obstacle(450, 430,  22),
        Obstacle(600, 220,  15),
        Obstacle(200, 270,  20),
        Obstacle(820, 460,  17),
        Obstacle(560, 500,  14, moving=True),
    ]

    speed_zones = [
        SpeedZone(300, 350, 85,  50, '50'),
        SpeedZone(700, 350, 85,  50, '50'),
    ]

    return dict(
        car=car, planner=planner,
        roads=roads, intersections=intersections,
        traffic_lights=traffic_lights, traffic_cars=traffic_cars,
        obstacles=obstacles, speed_zones=speed_zones,
        name='City Block',
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Scenario 2 – Highway
# ═══════════════════════════════════════════════════════════════════════════════
def _highway() -> dict:
    # Gentle S-curve high-speed road
    ego_wps = [
        ( 60, 350),
        (200, 230),
        (380, 270),
        (550, 200),
        (720, 300),
        (880, 250),
        (940, 350),
    ]
    car     = Car(60, 350, heading=0.0)
    planner = WaypointPlanner(ego_wps)

    roads = []
    for i in range(len(ego_wps) - 1):
        x1, y1 = ego_wps[i]
        x2, y2 = ego_wps[i + 1]
        roads.append(RoadSegment(x1, y1, x2, y2, width=80, speed_limit=180))

    # Dense traffic on same route — staggered starting positions
    import random
    traffic_cars = []
    n_tc = 8
    for i in range(n_tc):
        idx = i % (len(ego_wps) - 1)
        x0, y0 = ego_wps[idx]
        tc = TrafficCar(ego_wps, speed=random.uniform(75, 130),
                        start_index=max(1, idx + 1))
        tc.x, tc.y = float(x0), float(y0)
        traffic_cars.append(tc)

    obstacles = [
        Obstacle(350, 255, 18, moving=False),
        Obstacle(650, 310, 16, moving=False),
        Obstacle(490, 235, 20, moving=True),
        Obstacle(780, 280, 14, moving=True),
    ]

    speed_zones = [
        SpeedZone(500, 270, 400, 180, '180'),
    ]

    return dict(
        car=car, planner=planner,
        roads=roads, intersections=[],
        traffic_lights=[], traffic_cars=traffic_cars,
        obstacles=obstacles, speed_zones=speed_zones,
        name='Highway',
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Scenario 3 – Parking Lot
# ═══════════════════════════════════════════════════════════════════════════════
def _parking_lot() -> dict:
    ego_wps = [
        ( 80,  80),
        (300,  80),
        (300, 200),
        (500, 200),
        (500,  80),
        (750,  80),
        (750, 300),
        (500, 300),
        (500, 450),
        (750, 450),
        (750, 600),
        (300, 600),
        (300, 450),
        (100, 450),
        (100, 300),
        (920, 620),   # GOAL
    ]
    car     = Car(80, 80, heading=0.0)
    planner = WaypointPlanner(ego_wps)

    roads = [
        # Horizontal aisles
        RoadSegment( 50,  80, 950,  80, width=48, speed_limit=40),
        RoadSegment( 50, 300, 950, 300, width=48, speed_limit=40),
        RoadSegment( 50, 450, 950, 450, width=48, speed_limit=40),
        RoadSegment( 50, 600, 950, 600, width=48, speed_limit=40),
        # Vertical aisles
        RoadSegment(100,  50, 100, 650, width=48, speed_limit=40),
        RoadSegment(300,  50, 300, 650, width=48, speed_limit=40),
        RoadSegment(500,  50, 500, 650, width=48, speed_limit=40),
        RoadSegment(750,  50, 750, 650, width=48, speed_limit=40),
    ]

    # Parked cars as static obstacles (in bays between aisles)
    bay_y_rows  = [175, 375, 525]
    bay_x_cols  = [160, 220, 380, 440, 560, 620, 800, 860]
    parked: list[Obstacle] = []
    for by in bay_y_rows:
        for bx in bay_x_cols:
            parked.append(Obstacle(bx, by, 13))

    # A few obstacles near turns
    extra = [
        Obstacle(400, 130, 12),
        Obstacle(640, 380, 14),
        Obstacle(200, 530, 12),
    ]

    speed_zones = [
        SpeedZone(500, 350, 450, 40, '40'),
    ]

    return dict(
        car=car, planner=planner,
        roads=roads, intersections=[],
        traffic_lights=[], traffic_cars=[],
        obstacles=parked + extra, speed_zones=speed_zones,
        name='Parking Lot',
    )
