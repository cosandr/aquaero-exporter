import argparse
import os
from typing import Dict, NamedTuple, List

import prometheus_client as prom
from aiohttp import web
from pyquaero.core import Aquaero

WRITE_FILE = ''


class Status(NamedTuple):
    id: str
    val: float


class Exporter:
    def __init__(self):
        self.aq = Aquaero()
        print('Aquaero device opened')
        self.gauges: Dict[str, prom.Gauge] = {
            "aquaero_up": prom.Gauge("aquaero_up", "Aquaero exporter running"),
            "aquaero_rpm": prom.Gauge("aquaero_rpm", "Aquaero fan RPM", ['id']),
            "aquaero_temp": prom.Gauge("aquaero_temp", "Aquaero temperature sensor", ['id']),
        }
        self.gauges["aquaero_up"].set(1)

    def close(self):
        self.aq.close()
        print('Aquaero device closed')

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
                    if fan.get('speed') is not None:
                        res['aquaero_rpm'].append(Status(id=f'fan{i}', val=fan['speed']))
            if k == 'temperatures':
                if not isinstance(v, dict):
                    print(f'Expected type dict for temperatures, got {type(v)}')
                    continue
                for name, entries in v.items():
                    for i, sensor in enumerate(entries, 1):
                        if not isinstance(sensor, dict):
                            print(f'Expected type dict for {name}, got {type(sensor)}')
                            break
                        if sensor.get('temp') is not None:
                            res['aquaero_temp'].append(Status(id=f'{name}{i}', val=sensor['temp']))
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
        if WRITE_FILE:
            try:
                write_str = ''
                for s_list in status.values():
                    tmp = [f'{s.id}\t{s.val}' for s in s_list]
                    write_str += f'{"|".join(tmp)}\n'
                with open(WRITE_FILE, 'w') as f:
                    f.write(write_str.strip())
            except Exception as e:
                print(f'Cannot write to {WRITE_FILE}: {e}')
        return web.Response(body=prom.generate_latest(prom.REGISTRY), content_type="text/plain")


def main():
    parser = argparse.ArgumentParser(description="Prometheus exporter for Aquaero devices")
    parser.add_argument('--listen-address', type=str, default='0.0.0.0:2782', help='Listen address')
    parser.add_argument('--file', type=str, help='Write script-friendly output to file')
    args = parser.parse_args()
    if args.file:
        global WRITE_FILE
        WRITE_FILE = args.file
        print(f'Write status to {WRITE_FILE}')
    exp = Exporter()
    app = web.Application()
    app.add_routes([web.get("/metrics", exp.handler_metrics)])
    try:
        host, port = args.listen_address.split(':', 1)
        web.run_app(app, host=host, port=int(port))
    finally:
        exp.close()


if __name__ == '__main__':
    main()
