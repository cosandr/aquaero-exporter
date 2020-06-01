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
