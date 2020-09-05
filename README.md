# Prometheus exporter for Aquaero devices

This is a simple metrics exporter using the [pyquaero](https://github.com/shred/pyquaero) library.
It only exports fan speeds and temperatures, but it is easily expandable if desired.

## Installation

Arch users can use the PKGBUILD, but I prefer running it in a virtualenv.

[setup.sh](./setup.sh) can generate a systemd service.

If aquaero-exporter is installed in a virtualenv managed by pyenv, it will run that.
Otherwise it will use the virtualenv interpreter to launch the script directly.
If you don't have pyenv, it will run the script with the current interpreter.

Generating a systemd unit file will fail if the script cannot start.

## Example metrics

```text
# HELP aquaero_rpm Aquaero fan RPM
# TYPE aquaero_rpm gauge
aquaero_rpm{id="fan1"} 1284.0
aquaero_rpm{id="fan2"} 230.0
aquaero_rpm{id="fan3"} 1780.0
aquaero_rpm{id="fan4"} 319.0
# HELP aquaero_temp Aquaero temperature sensor
# TYPE aquaero_temp gauge
aquaero_temp{id="sensor1"} 31.83
aquaero_temp{id="sensor2"} 24.1
```

## Example API response
`GET /api/status`
```json
{
  "rpm": {
    "fan1": 1705,
    "fan2": 1426,
    "fan3": 2241,
    "fan4": 1463,
    "fan5": 2977,
    "fan7": 2581,
    "fan9": 2540,
    "fan10": 1229
  },
  "temp": {
    "sensor1": 90,
    "sensor3": 8,
    "sensor6": 1,
    "virtual1": 3.19,
    "fan_vrm1": 30.91,
    "fan_vrm2": 30.91,
    "fan_vrm3": 30.28,
    "fan_vrm4": 30.28
  }
}
```