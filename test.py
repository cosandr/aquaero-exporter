import pickle
from pyquaero.core import Aquaero


def dump_status_file():
    with Aquaero() as aq:
        status = aq.get_status()
    with open('status_dump.pickle', 'wb') as fw:
        pickle.dump(status, fw)


def read_status_file():
    with open('status_dump.pickle', 'rb') as fr:
        return pickle.load(fr)


if __name__ == '__main__':
    status: dict = read_status_file()
    res = []
    for k, v in status.items():
        print(f'{k}: {v}')
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
    print(res)