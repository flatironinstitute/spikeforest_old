from mountaintools import client as mt
# from . import sorters as sorters

from spikesorters import MountainSort4, SpykingCircus, YASS, YASS1, IronClust, KiloSort, KiloSort2, MountainSort4TestError, HerdingSpikes2, JRClust, Klusta, Tridesclous, Waveclus

Processors = dict(
    MountainSort4=(MountainSort4, 'default'),
    IronClust=(IronClust, None),
    SpykingCircus=(SpykingCircus, 'default'),
    KiloSort=(KiloSort, None),
    KiloSort2=(KiloSort2, None),
    Yass=(YASS, 'default'),
    Yass1=(YASS1, 'default'),
    MountainSort4TestError=(MountainSort4TestError, 'default'),
    HerdingSpikes2=(HerdingSpikes2, 'default'),
    JRClust=(JRClust, None),
    Klusta=(Klusta, None),
    Tridesclous=(Tridesclous, 'default'),
    Waveclus=(Waveclus, None),
)


def find_sorter_processor_and_container(processor_name):
    if processor_name not in Processors:
        raise Exception('No such sorter: ' + processor_name)
    SS = Processors[processor_name][0]
    SS_container = Processors[processor_name][1]
    if SS_container:
        if SS_container == 'default':
            SS_container = SS.CONTAINER
    return SS, SS_container
