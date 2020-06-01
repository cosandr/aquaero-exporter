# Prometheus exporter for Aquaero devices

This is a simple metrics exporter using the [pyquaero](https://github.com/shred/pyquaero) library.
It only exports fan speeds and temperatures, but it is easily expandable if desired.

## Installation

Arch users can use the PKGBUILD, but I prefer running it in a virtualenv.

[setup.sh](./setup.sh) can generate a systemd service that uses a `aquaero-exporter` virtualenv managed by pyenv.
If not using pyenv, provide the path to the python interpreter to use using the `--py-path` argument.

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