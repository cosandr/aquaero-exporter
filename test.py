import pickle
import random

from aiohttp import web
from pyquaero.core import Aquaero

from aquaero_exporter.exporter import Exporter


def dump_status_file():
    with Aquaero() as aq:
        status = aq.get_status()
    with open('status_dump.pickle', 'wb') as fw:
        pickle.dump(status, fw)


class MockDevice:
    def __init__(self, randomize=False):
        self.randomize = randomize

    def close(self):
        pass

    def get_status(self):
        with open('status_dump.pickle', 'rb') as fr:
            status = pickle.load(fr)
        if self.randomize:
            # Set some random fan speeds to None or change their speed
            for fan in status['fans']:
                if random.randint(0, 2) == 0:
                    fan['speed'] = None
                else:
                    fan['speed'] = random.randint(0, 3000)
            for sensor in status['temperatures']['sensor']:
                if random.randint(0, 2) == 0:
                    sensor['temp'] = None
                else:
                    sensor['temp'] = random.randint(0, 100)
        return status


if __name__ == '__main__':
    listen_address = '127.0.0.1:8000'
    exp = Exporter(MockDevice(randomize=True), wait_seconds=0)
    app = web.Application()
    app.add_routes(exp.routes)
    host, port = listen_address.split(':', 1)
    web.run_app(app, host=host, port=int(port))
