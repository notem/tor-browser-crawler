import os
import subprocess
import time
import psutil

import tbcrawler.common as cm
import tbcrawler.utils as ut
from tbcrawler.log import wl_log

DUMPCAP_START_TIMEOUT = 10.0


class Sniffer(object):
    """Capture network traffic using dumpcap."""

    def __init__(self, path="/dev/null", filter="", device="eth0", dumpcap_log=None):
        self.pcap_file = path
        self.pcap_filter = filter
        self.p0 = None
        self.is_recording = False
        self.device = device
        self.log = dumpcap_log

    def set_pcap_path(self, pcap_filename):
        """Set filename and filter options for capture."""
        self.pcap_file = pcap_filename

    def set_capture_filter(self, _filter):
        self.pcap_filter = _filter

    def get_pcap_path(self):
        """Return capture (pcap) filename."""
        return self.pcap_file

    def get_capture_filter(self):
        """Return capture filter."""
        return self.pcap_filter

    def start_capture(self, pcap_path=None, pcap_filter="", dumpcap_log=None):
        """Start capture. Configure sniffer if arguments are given."""
        if pcap_filter:
            self.set_capture_filter(pcap_filter)
        if pcap_path:
            self.set_pcap_path(pcap_path)
        prefix = "LD_LIBRARY_PATH=\"\" "  # fix capture util crashing
        command = '{}dumpcap -P -a duration:{} -a filesize:{} -i {} -s 0 -f \'{}\' -w {}'\
            .format(prefix, cm.HARD_VISIT_TIMEOUT, cm.MAX_DUMP_SIZE, self.device,
                    self.pcap_filter, self.pcap_file)
        #command = '{}tcpdump -G {} -i {} -w {} \'{}\''\
        #        .format(prefix, cm.HARD_VISIT_TIMEOUT, self.device, self.pcap_file, self.pcap_filter)
        #command = '{}tshark -i {} -w {} -f \'{}\' '\
        #        .format(prefix, self.device, self.pcap_file, self.pcap_filter)
        wl_log.info(command)
        if dumpcap_log:
            log_fi = open(dumpcap_log, "w+")
            self.p0 = subprocess.Popen(command, stdout=log_fi,
                                       stderr=log_fi, shell=True)
        else:
            self.p0 = subprocess.Popen(command, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)
        timeout = DUMPCAP_START_TIMEOUT  # in seconds
        while timeout > 0 and not self.is_dumpcap_running():
            time.sleep(0.1)
            timeout -= 0.1
        if timeout < 0:
            raise DumpcapTimeoutError()
        else:
            wl_log.debug("capture started in %s seconds" %
                         (DUMPCAP_START_TIMEOUT - timeout))

        self.is_recording = True

    def is_dumpcap_running(self):
        procname = "dumpcap"
        if procname in psutil.Process(self.p0.pid).cmdline():
            return self.p0.returncode is None
        for proc in ut.gen_all_children_procs(self.p0.pid):
            if procname in proc.cmdline():
                return True
        return False

    def stop_capture(self):
        """Kill the dumpcap process."""
        ut.kill_all_children(self.p0.pid)  # self.p0.pid is the shell pid
        self.p0.kill()
        self.is_recording = False
        if os.path.isfile(self.pcap_file):
            wl_log.info('Capture killed. Traffic size: %s Bytes %s' %
                        (os.path.getsize(self.pcap_file), self.pcap_file))
        else:
            wl_log.warning('Capture killed but cannot find capture file: %s'
                           % self.pcap_file)
            wl_log.warning('Check %s for error information!'
                           % self.log)

    def __enter__(self):
        self.start_capture(dumpcap_log=self.log)
        return self

    def __exit__(self, type, value, traceback):
        self.stop_capture()


class DumpcapTimeoutError(Exception):
    pass

