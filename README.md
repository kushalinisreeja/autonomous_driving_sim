# Autonomous Driving Logic Simulation (INTERN ID - CITS9171)

A feature-rich **2D top-down autonomous driving simulation** built with Python + Pygame.  
The car drives itself using LiDAR sensors, a potential-field controller, waypoint path planning, traffic light compliance, and speed-zone awareness — or you can take the wheel yourself in **manual mode**.

---

## What it simulates

| Component | What it does |
|---|---|
| **Kinematic bicycle model** | Realistic car physics — steering angle, acceleration, drag, gear states |
| **LiDAR sensor (18 rays)** | 210° fan of ray-cast beams detecting obstacles, traffic, and walls |
| **Potential-field controller** | Obstacle repulsion + goal attraction = autonomous steering/throttle |
| **Waypoint planner** | Car follows a pre-defined road route, advancing point-by-point |
| **Traffic lights** | RED→YELLOW→GREEN cycle; car brakes smoothly at red lights |
| **NPC traffic cars** | Follow waypoint loops, brake at lights, maintain following distance |
| **Speed zones** | Circular areas with custom speed limits the controller respects |
| **Collision detection** | Flags wall/obstacle/NPC hits; car turns red |
| **HUD dashboard** | Live speed bar, gear, steer, waypoint progress, signal state |
| **Data logger** | Records telemetry to `logs/run_YYYYMMDD_HHMMSS.csv` |

---

## Requirements

```bash
pip install pygame numpy
```

## Run

```bash
python main.py
```

---

## Controls

| Key | Action |
|---|---|
| `1` / `2` / `3` | Switch scenario |
| `R` | Reset current scenario |
| `M` | Toggle **Manual** ↔ **Autonomous** mode |
| `G` | Toggle LiDAR sensor ray display |
| `D` | Toggle sensor debug table (right panel) |
| `P` | Pause / unpause |
| `L` | Start / stop CSV data logging |
| `ESC` / `Q` | Quit |

### Manual driving (when M is active)
| Key | Action |
|---|---|
| `W` / `↑` | Accelerate |
| `S` / `↓` | Brake / reverse |
| `A` / `←` | Steer left |
| `D` / `→` | Steer right |

---

## Scenarios

### 1 — City Block *(default)*
Grid of roads with 6 intersections, staggered traffic lights, 5 NPC cars circling different city blocks, and 6 obstacles. The ego car navigates an S-path across the grid.

### 2 — Highway
Gentle S-curve high-speed road (speed limit 180 px/s), 8 NPC cars, moving obstacles. Tests high-speed sensor response and smooth lane holding.

### 3 — Parking Lot
Tight aisle network with dozens of parked-car obstacles. Speed limit 40 px/s. Tests low-speed precision navigation and tight-turn handling.

---

## Project Structure

```
autonomous_driving_sim/
├── main.py                  ← Entry point / game loop
├── simulation/
│   ├── __init__.py
│   ├── car.py               ← Kinematic bicycle model, gear, trail
│   ├── obstacle.py          ← Static + moving circular obstacles
│   ├── sensors.py           ← LiDAR ray-cast sensor
│   ├── traffic_light.py     ← RED/YELLOW/GREEN state machine
│   ├── road.py              ← Road segments, intersections, speed zones
│   ├── traffic.py           ← NPC traffic cars
│   ├── planner.py           ← Waypoint path planner
│   ├── controller.py        ← Autonomous decision logic
│   ├── scenario.py          ← 3 scenario definitions
│   ├── hud.py               ← Dashboard / HUD rendering
│   └── logger.py            ← CSV telemetry logger
└── logs/                    ← Auto-created; CSV run files appear here
```

---

## Sensor color coding

| Color | Meaning |
|---|---|
| 🔴 Red | Distance < 35 px — **DANGER** (emergency brake) |
| 🟡 Yellow | Distance < 85 px — **CAUTION** (slow down) |
| Dim blue | Clear / wall hit |
| Orange dot | Traffic car detected |
| Purple | Wall hit |

---

## Data logging format (CSV)

```
frame, x, y, heading_deg, speed_px_s, throttle, steer_deg, gear, min_sensor_dist, num_hits, collided
```

Press `L` in-game to start recording. Files are saved to `logs/` automatically.
