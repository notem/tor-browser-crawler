import signal
from contextlib import contextmanager
from distutils.dir_util import copy_tree
from os import makedirs
from os.path import exists
from shutil import copyfile

from scapy.all import PcapReader, wrpcap

import psutil
from tbcrawler.common import TimeoutException


def create_dir(dir_path):
    """Create a directory if it doesn't exist."""
    if not exists(dir_path):
        makedirs(dir_path)
    return dir_path


def clone_dir_temporary(dir_path):
    """Makes a temporary copy of a directory."""
    import tempfile
    tempdir = tempfile.mkdtemp()
    copy_tree(dir_path, tempdir)
    return tempdir


def gen_all_children_procs(parent_pid):
    """Iterator over the children of a process."""
    parent = psutil.Process(parent_pid)
    for child in parent.children(recursive=True):
        yield child


def kill_all_children(parent_pid):
    """Kill all child process of a given parent."""
    for child in gen_all_children_procs(parent_pid):
        child.kill()


def get_dict_subconfig(config, section, prefix):
    """Return options in config for options with a `prefix` keyword."""
    return {option.split()[1]: config.get(section, option)
            for option in config.options(section) if option.startswith(prefix)}


def filter_pcap(pcap_path, iplist):
    """
    Filter capture by TCP packets addressed to any address in ``iplist``
    """
    pcap_filtered = []
    orig_pcap = pcap_path + ".original"
    copyfile(pcap_path, orig_pcap)
    with PcapReader(orig_pcap) as preader:
        for p in preader:
            if 'TCP' in p:
                ip = p.payload
                if ip.dst in iplist or ip.src in iplist:
                    pcap_filtered.append(p)
    wrpcap(pcap_path, pcap_filtered)


@contextmanager
def timeout(seconds):
    """From: http://stackoverflow.com/a/601168/1336939"""
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
