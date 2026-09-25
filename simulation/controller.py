"""
Autonomous controller — potential-field obstacle avoidance + goal seeking
with traffic-light compliance and speed-limit awareness.
"""
import math

# ── Tuning parameters ────────────────────────────────────────────────────────
SAFE_DIST     = 85.0     # px — start reacting to obstacles
CRIT_DIST     = 35.0     # px — emergency brake
STEER_GAIN    = 2.8      # repulsion steering multiplier
GOAL_GAIN     = 1.0      # attraction toward goal
LIGHT_BRAKE   = 95.0     # px — start braking for red light
FWD_CONE_DEG  = 28.0     # half-angle of forward sensor cone


def _wrap(a: float) -> float:
    while a >  math.pi: a -= 2 * math.pi
    while a < -math.pi: a += 2 * math.pi
    return a


def compute_control(car, readings: list, goal: tuple,
                    traffic_lights=None,
                    speed_limit: float = 160.0) -> tuple:
    """
    Compute (throttle, steer_cmd) in [-1, 1] for the ego car.

    Args:
        car           – Car instance
        readings      – list of SensorReading from LiDARSensor.scan()
        goal          – (x, y) current intermediate waypoint
        traffic_lights – list of TrafficLight objects (optional)
        speed_limit   – maximum allowed speed in current zone (px/s)

    Returns:
        (throttle, steer_cmd) both clamped to [-1, 1]
    """
    traffic_lights = traffic_lights or []
    fwd_cone_rad   = math.radians(FWD_CONE_DEG)

    # ── Goal attraction ───────────────────────────────────────────────────────
    gx, gy     = goal
    goal_dx    = gx - car.x
    goal_dy    = gy - car.y
    goal_dist  = math.hypot(goal_dx, goal_dy)
    goal_angle = math.atan2(goal_dy, goal_dx)
    heading_err = _wrap(goal_angle - car.heading)

    steer_attract = GOAL_GAIN * (heading_err / math.pi)   # −1 … +1

    # ── Obstacle repulsion (potential field) ──────────────────────────────────
    repulsion    = 0.0
    min_fwd_dist = SAFE_DIST * 2   # start optimistic

    for r in readings:
        if r.distance < SAFE_DIST:
            closeness  = (SAFE_DIST - r.distance) / SAFE_DIST
            centrality = 1.0 - min(1.0, abs(r.angle_offset) / math.pi)
            direction  = -1.0 if r.angle_offset >= 0 else 1.0
            repulsion += direction * closeness * (0.3 + 0.7 * centrality)

        # Track the nearest obstacle in the forward cone
        if abs(r.angle_offset) < fwd_cone_rad:
            min_fwd_dist = min(min_fwd_dist, r.distance)

    steer_cmd = max(-1.0, min(1.0, steer_attract + STEER_GAIN * repulsion))

    # ── Traffic-light compliance ──────────────────────────────────────────────
    stop_for_light = False
    nearest_light_dist = float('inf')
    for tl in traffic_lights:
        d = math.hypot(car.x - tl.x, car.y - tl.y)
        if tl.is_stop() and d < LIGHT_BRAKE:
            stop_for_light = True
            nearest_light_dist = min(nearest_light_dist, d)

    # ── Speed control ─────────────────────────────────────────────────────────
    if stop_for_light:
        # Smooth brake proportional to distance
        if nearest_light_dist < CRIT_DIST:
            throttle = -1.0
        else:
            frac     = (nearest_light_dist - CRIT_DIST) / (LIGHT_BRAKE - CRIT_DIST)
            throttle = -1.0 + frac * 1.0   # −1 → 0 as we approach
    elif min_fwd_dist < CRIT_DIST:
        throttle = -1.0                     # emergency brake
    elif min_fwd_dist < SAFE_DIST:
        frac     = (min_fwd_dist - CRIT_DIST) / (SAFE_DIST - CRIT_DIST)
        throttle = 0.1 + 0.5 * frac        # slow roll
    elif goal_dist < 30:
        throttle = 0.15                     # gentle approach to waypoint
    else:
        # Normal cruise — slow for sharp turns
        turn_factor = 1.0 - min(1.0, abs(heading_err) / (math.pi / 2))
        throttle    = 0.35 + 0.65 * turn_factor

        # Respect speed limit
        if speed_limit > 0 and car.speed > speed_limit * 0.9:
            throttle *= 0.55

    return throttle, steer_cmd
