# Prometheus exporter for Aquaero devices

This is a simple metrics exporter using my
[pyquaero](https://github.com/cosandr/pyquaero/tree/windows) fork for Windows.
It only exports fan speeds and temperatures, but it is easily expandable if desired.

## Installation

Use NSSM or task scheduler to run it all the time. NSSM with venv example:

```
python setup.py install
nssm.exe install AquaeroExporter "C:\Users\Andrei\venvs\aquaero-exporter\Scripts\aquaero_exporter.exe"
```

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