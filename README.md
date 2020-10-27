# Traffic Controller with Queue Management

## Getting Started

Clone the repo: `https://github.com/weijuinlee/TrafficController.git`

## Usage

```sh
cd TrafficController
```

## You need four terminals running:

### 1.
```sh
redis-server
```

### 2.
```sh
rq worker
```

### 3.
```sh
python app.py
```

### 4.
```sh
mosquitto
```

## To visualise and enter waypoints into the traffic controller, you need an emulator and an editor. GOTO: https://github.com/hanscau/AngularRobotEmulator

