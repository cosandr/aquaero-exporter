import argparse
from time import perf_counter
from typing import Dict, NamedTuple, List

import prometheus_client as prom
from aiohttp import web
from pyquaero.core import Aquaero


def timeit(func):
    def timed(*args, **kwargs):
        ts = perf_counter()
        res = func(*args, **kwargs)
        te = perf_counter()
        print(f'{func.__name__} ran in {(te-ts)*1000:.2f}ms')
        return res
    return timed


class Status(NamedTuple):
    id: str
    val: float


class Exporter:
    def __init__(self):
        self.aq = Aquaero()
        print('Aquaero device opened')
        self.gauges: Dict[str, prom.Gauge] = {
            "aquaero_rpm": prom.Gauge("aquaero_rpm", "Aquaero fan RPM", ['id']),
            "aquaero_temp": prom.Gauge("aquaero_temp", "Aquaero temperature sensor", ['id']),
        }

    def close(self):
        self.aq.close()
        print('Aquaero device closed')

    @timeit
    def read_status_aquaero(self) -> dict:
        return self.aq.get_status()

    def parse_status(self, status: dict) -> Dict[str, List[Status]]:
        res = {k: [] for k in self.gauges.keys()}
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
                        res['aquaero_rpm'].append(Status(id=f'fan{i}', val=fan['speed']))
            if k == 'temperatures':
                if not isinstance(v, dict):
                    print(f'Expected type dict for temperatures, got {type(v)}')
                    continue
                for i, sensor in enumerate(v.get('sensor'), 1):
                    if not isinstance(v, dict):
                        print(f'Expected type dict for sensor, got {type(sensor)}')
                        break
                    if sensor.get('temp'):
                        res['aquaero_temp'].append(Status(id=f'sensor{i}', val=sensor['temp']))
        return res

    def update_gauges(self, status: Dict[str, List[Status]]):
        for k, s_list in status.items():
            for s in s_list:
                try:
                    self.gauges[k].labels(id=s.id).set(s.val)
                except Exception as e:
                    print(f'Failed to set gauge {k} to {s.val}: {str(e)}')

    async def handler_metrics(self, r: web.Request) -> web.Response:
        status = self.parse_status(self.read_status_aquaero())
        self.update_gauges(status)
        return web.Response(body=prom.generate_latest(prom.REGISTRY), content_type="text/plain")


def main():
    parser = argparse.ArgumentParser(description="Prometheus exporter for Aquaero devices")
    parser.add_argument('--host', type=str, help='Listen address host', default='0.0.0.0')
    parser.add_argument('--port', type=int, help='Listen address port', default=2782)
    args = parser.parse_args()
    exp = Exporter()
    app = web.Application()
    app.add_routes([web.get("/metrics", exp.handler_metrics)])
    try:
        # Use port 2782 (AQUA)
        web.run_app(app, host=args.host, port=args.port)
    finally:
        exp.close()


if __name__ == '__main__':
    main()
