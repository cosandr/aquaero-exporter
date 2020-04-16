from time import perf_counter
from typing import List

import prometheus_client as prom
from flask import Response, Flask

from pyquaero.core import Aquaero


app = Flask(__name__)
gauges = []
aq = Aquaero()
print('Connected to aquaero device')


def timeit(func):
    def timed(*args, **kwargs):
        ts = perf_counter()
        res = func(*args, **kwargs)
        te = perf_counter()
        print(f'{func.__name__} ran in {(te-ts)*1000:.2f}ms')
        return res
    return timed


@timeit
def read_status_aquaero():
    return aq.get_status()


@timeit
def parse_status(status: dict):
    res = []
    for k, v in status.items():
        if k == 'fans':
            if not isinstance(v, list):
                print(f'Expected type list for fans, got {type(v)}')
                continue
            for i, fan in enumerate(v, 1):
                if not isinstance(fan, dict):
                    print(f'Expected type dict for fan entry, got {type(fan)}')
                    break
                if fan.get('speed'):
                    res.append(dict(name=f'aquaero_rpm_fan{i}', val=fan['speed'], desc=f'Fan {i} RPM'))
        if k == 'temperatures':
            if not isinstance(v, dict):
                print(f'Expected type dict for temperatures, got {type(v)}')
                continue
            for i, sensor in enumerate(v.get('sensor'), 1):
                if not isinstance(v, dict):
                    print(f'Expected type dict for sensor, got {type(sensor)}')
                    break
                if sensor.get('temp'):
                    res.append(dict(name=f'aquaero_temp_sensor{i}', val=sensor['temp'], desc=f'Sensor {i} temperature'))
    return res


@timeit
def status_to_gauges(status: List[dict]):
    global gauges
    if len(gauges) != len(status):
        gauges = []
        for s in status:
            gauges.append(prom.Gauge(s['name'], s['desc']))
    for i, s in enumerate(status):
        try:
            gauges[i].set(s['val'])
        except Exception as e:
            print(f'Failed to set gauge {s["name"]} to {s["val"]}: {str(e)}')


@timeit
@app.route("/metrics")
def requests_count():
    global gauges
    status_to_gauges(parse_status(read_status_aquaero()))
    res = [prom.generate_latest(prom.REGISTRY)]
    for g in gauges:
        res.append(prom.generate_latest(g))
    return Response(res, mimetype="text/plain")


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=8000)
    finally:
        aq.close()
        print('Aquaero device closed')
