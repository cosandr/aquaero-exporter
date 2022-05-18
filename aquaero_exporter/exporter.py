import argparse
import json
import logging
from datetime import datetime
from typing import Dict, NamedTuple, List, Optional

from aiohttp import web
from prometheus_client import generate_latest
from prometheus_client.core import GaugeMetricFamily, REGISTRY

NAMESPACE = 'aquaero'


class Status(NamedTuple):
    id: str
    val: float


class Exporter:
    def __init__(self, device, wait_seconds=30, write_file=''):
        self.wait_seconds: int = wait_seconds
        self.write_file: str = write_file
        if self.write_file:
            logging.info(f'Write status to {self.write_file}')
        self._last_read: Optional[datetime] = None
        self._last_status = dict()
        self.metrics: Dict[str, dict] = {
            "up": dict(name=f"{NAMESPACE}_up", documentation="Aquaero exporter running", value=1),
            "rpm": dict(name=f"{NAMESPACE}_rpm", documentation="Aquaero fan RPM", labels=['id']),
            "temp": dict(name=f"{NAMESPACE}_temp", documentation="Aquaero temperature sensor", labels=['id']),
            "flow": dict(name=f"{NAMESPACE}_flow", documentation="Aquaero flow meters", labels=['id']),
        }
        self._last_metrics = {}
        self.device = device
        REGISTRY.register(self)
        self.routes = [
            web.get("/", self.handler_root),
            web.get("/metrics", self.handler_metrics),
            web.get("/api/status", self.handler_api_status),
        ]

    def close(self):
        self.device.close()
        logging.info('Device closed')

    def collect(self):
        status = self.get_status()
        gauges = {}
        for k, v in self.metrics.items():
            gauges[k] = GaugeMetricFamily(**v)
        for k, s_list in status.items():
            if 'labels' not in self.metrics[k]:
                continue
            for s in s_list:
                try:
                    gauges[k].add_metric(labels=[s.id], value=s.val)
                except Exception as e:
                    logging.error('Failed to set gauge %s to %s: %s', k, s.val, str(e))
        for v in gauges.values():
            yield v

    def read_status_aquaero(self) -> dict:
        if not self._last_read or (datetime.now() - self._last_read).total_seconds() > self.wait_seconds:
            status = self.device.get_status()
            self._last_read = datetime.now()
            self._last_status = status
            logging.debug('Read new status from device')
        else:
            status = self._last_status
            logging.debug('Returning cached status')
        return status

    def parse_status(self, status: dict) -> Dict[str, List[Status]]:
        res = {k: [] for k, v in self.metrics.items() if 'labels' in v}
        # Fans
        for i, fan in enumerate(status.get('fans', []), 1):
            if not isinstance(fan, dict):
                logging.warning('Expected type dict for fan entry, got %s', type(fan))
                break
            if fan.get('speed') is not None:
                res['rpm'].append(Status(id=f'fan{i}', val=fan['speed']))
        # Temperatures
        for name, entries in status.get('temperatures', {}).items():
            for i, sensor in enumerate(entries, 1):
                if not isinstance(sensor, dict):
                    logging.warning('Expected type dict for %s, got %s', name, type(sensor))
                    break
                if sensor.get('temp') is not None:
                    res['temp'].append(Status(id=f'{name}{i}', val=sensor['temp']))
        # Flow meters
        for i, flow in enumerate(status.get('flow_meters', []), 1):
            if not isinstance(flow, dict):
                logging.warning('Expected type dict for flow entry, got %s', type(flow))
                break
            if flow.get('rate') is not None:
                res['flow'].append(Status(id=f'flow{i}', val=flow['rate']))
        # Aquastream speeds
        for i, stream in enumerate(status.get('aquastream', []), 1):
            if not isinstance(stream, dict):
                logging.warning('Expected type dict for aquastream entry, got %s', type(stream))
                break
            if stream.get('speed') is not None:
                res['rpm'].append(Status(id=f'aquastream{i}', val=stream['speed']))

        return res

    def get_status(self) -> Dict[str, List[Status]]:
        status = self.parse_status(self.read_status_aquaero())
        if self.write_file:
            write_str = ''
            for s_list in status.values():
                tmp = [f'{s.id}\t{s.val}' for s in s_list]
                write_str += f'{"|".join(tmp)}\n'
            try:
                with open(self.write_file, 'w') as f:
                    f.write(write_str.strip())
            except Exception as e:
                logging.error('Cannot write to %s: %s', self.write_file, str(e))
        return status

    async def handler_root(self, r: web.Request) -> web.Response:
        return web.Response(text="""
            <html>
            <head><title>Aquaero Exporter</title></head>
            <body>
            <h1>Aquaero Exporter</h1>
            <p><a href='/metrics'>Metrics</a></p>
            <p><a href='/api/status'>API</a></p>
            <h2>More information:</h2>
            <p><a href="https://github.com/cosandr/aquaero-exporter">github.com/cosandr/aquaero-exporter</a></p>
            </body>
            </html>
            """, content_type="text/html")

    async def handler_metrics(self, r: web.Request) -> web.Response:
        return web.Response(body=generate_latest(REGISTRY), content_type="text/plain")

    async def handler_api_status(self, r: web.Request) -> web.Response:
        status = self.get_status()
        status_dict = {}
        for k, v in status.items():
            if isinstance(v, list):
                status_dict[k] = {}
                for s in v:
                    if isinstance(s, Status):
                        status_dict[k][s.id] = s.val
        return web.Response(text=json.dumps(status_dict), content_type="application/json")


def main():
    parser = argparse.ArgumentParser(description="Prometheus exporter for Aquaero devices")
    parser.add_argument('--listen-address', type=str, default='0.0.0.0:2782', help='Listen address')
    parser.add_argument('--file', type=str, help='Write script-friendly output to file')
    parser.add_argument('--throttle', type=int, default=30, help='Time to cache data for in seconds')
    parser.add_argument('--log-level', type=str.upper, choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        default='WARNING', help='Time to cache data for in seconds')
    parser.add_argument('--quadro', action='store_true', help='Use a Quadro device')
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)
    if args.quadro:
        from pyquaero.quadro.core import Quadro
        device = Quadro()
        logging.info('Quadro device opened')
    else:
        from pyquaero.core import Aquaero
        device = Aquaero()
        logging.info('Aquaero device opened')
    exp = Exporter(device, wait_seconds=args.throttle, write_file=args.file)
    app = web.Application()
    app.add_routes(exp.routes)
    try:
        host, port = args.listen_address.split(':', 1)
        web.run_app(app, host=host, port=int(port))
    finally:
        exp.close()


if __name__ == '__main__':
    main()
