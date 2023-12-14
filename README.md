# Simulated UAV Patrol and Tracking System

## Demo
![Demo GIF](/demo/github-demo.gif)

## Introduction
This is a simulated drone patrol and tracking system based on OM2M.

The simulation environment generates a person (detection target) who wanders around the map and periodically leaves the map, only to respawn after a certain interval.

The patrol drones begin patrolling when all drones are on standby. If a drone detects the target, it will briefly take over the tracking mission until the tracking drone successfully follows the target. The other patrol drones will then return to base and wait on standby.

The tracking drone usually stays at the base and starts its tracking mission only when a patrol drone detects something unusual. It continues this tracking mission until the target leaves the visible range.

## Pre-requisites
- Docker
- python3

## How to run (Development)
1.  Install python dependencies 
    - ```bash
        pip install -r requirements.txt
        ```

2. Run OM2M CSE, and wait for setup to complete
    - ```bash
        docker-compose up
        ```

3. Run simulated enviroment
    - ```bash
        cd simulated_enviroment
        python app.py
        ```

4. Run IN-Server
    - ```bash
        cd in_server
        python app.py
        ```

5. Run Track Drone API (AE)
    - ```bash
        cd drone
        python track_drone_app.py
        ```

6. Run Patrol Drone API (AE)
    - ```bash
        cd drone
        python patrol_drone_app.py
        ```

7. Run Frontend
    - ```bash
        cd gcs-application
        npm install
        npm run dev
        ```

## port
- 3000: Frontend
- 8122: Simulated Enviroment
- 8125: Patrol Drone API (MN-AE)
- 8126: Track Drone API (MN-AE)
- 8127: IN-Server (IN-AE)
- 9332: IN-CSE (8080)
- 9333: Patrol-Drone-MN-CSE-1 (8282)
- 9334: Patrol-Drone-MN-CSE-2 (8282)
- 9335: Patrol-Drone-MN-CSE-3 (8282)
- 9336: Track-Drone-MN-CSE-1 (8282)

## Icon References

<a href="https://www.flaticon.com/free-icons/government" title="government icons">Government icons created by Freepik - Flaticon</a>

<a href="https://www.flaticon.com/free-icons/suspicious" title="suspicious icons">Suspicious icons created by Freepik - Flaticon</a>

<a href="https://www.flaticon.com/free-icons/drone" title="drone icons">Drone icons created by Freepik - Flaticon</a>

<a href="https://www.flaticon.com/free-icons/drone-case" title="drone case icons">Drone case icons created by Freepik - Flaticon</a>

<a href="https://www.flaticon.com/free-icons/alarm" title="alarm icons">Alarm icons created by Freepik - Flaticon</a>

<a href="https://www.flaticon.com/free-icons/info" title="info icons">Info icons created by juicy_fish - Flaticon</a>

<a href="https://www.flaticon.com/free-icons/tick" title="tick icons">Tick icons created by Freepik - Flaticon</a>