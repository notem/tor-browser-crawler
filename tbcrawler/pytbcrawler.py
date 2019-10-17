import argparse
import ConfigParser
import sys
import traceback
from contextlib import contextmanager
from logging import INFO, DEBUG
from os import stat, chdir
from os.path import isfile, join, basename
from shutil import copyfile
from sys import maxsize, argv
from urlparse import urlparse
import re

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from tbselenium.tbdriver import TorBrowserDriver
from tbselenium.common import USE_RUNNING_TOR
from tbselenium.utils import start_xvfb, stop_xvfb

import tbcrawler.common as cm
import tbcrawler.utils as ut
import tbcrawler.crawler as crawler_mod
from tbcrawler.log import add_log_file_handler
from tbcrawler.log import wl_log, add_symlink
from tbcrawler.torcontroller import TorController


def run():
    # Parse arguments
    args, config = parse_arguments()

    # build dirs
    build_crawl_dirs(args.url_file)

    # Read URLs
    url_list = parse_url_list(args.url_file, args.start, args.stop)

    # Configure logger
    add_log_file_handler(wl_log, cm.DEFAULT_CRAWL_LOG)

    # Configure controller
    torrc_config = ut.get_dict_subconfig(config, args.config, "torrc")
    controller = TorController(cm.TBB_DIR,
                               torrc_dict=torrc_config,
                               pollute=False)

    # Configure browser
    ffprefs = ut.get_dict_subconfig(config, args.config, "ffpref")
    driver = TorBrowserWrapper(cm.TBB_DIR,
                               tbb_logfile_path=cm.DEFAULT_FF_LOG,
                               tor_cfg=USE_RUNNING_TOR,
                               pref_dict=ffprefs,
                               socks_port=int(torrc_config['socksport']))

    # Instantiate crawler
    crawler = crawler_mod.Crawler(driver, controller, args.screenshots, args.device)

    # Configure crawl
    job_config = ut.get_dict_subconfig(config, args.config, "job")
    job = crawler_mod.CrawlJob(job_config, url_list)

    # Setup stem headless display
    if args.virtual_display:
        xvfb_h = int(args.virtual_display.split('x')[0])
        xvfb_w = int(args.virtual_display.split('x')[1])
    else:
        xvfb_h = cm.DEFAULT_XVFB_WIN_H
        xvfb_w = cm.DEFAULT_XVFB_WIN_W
    xvfb_display = start_xvfb(xvfb_w, xvfb_h)

    # Run the crawl
    chdir(cm.CRAWL_DIR)
    try:
        crawler.crawl(job)
    except KeyboardInterrupt:
        wl_log.warning("Keyboard interrupt! Quitting...")
        sys.exit(-1)
    finally:
        # Post crawl
        post_crawl()

        # Close display
        stop_xvfb(xvfb_display)

    # die
    sys.exit(0)


def post_crawl():
    """Operations after the crawl."""
    # TODO: pack crawl
    # TODO: sanity checks
    pass


def build_crawl_dirs(video_file):
    # build crawl directory
    ut.create_dir(cm.RESULTS_DIR)
    ut.create_dir(cm.CRAWL_DIR)
    ut.create_dir(cm.LOGS_DIR)
    copyfile(cm.CONFIG_FILE, join(cm.LOGS_DIR, 'config.ini'))
    copyfile(video_file, join(cm.LOGS_DIR, 'videos.txt'))
    add_symlink(join(cm.RESULTS_DIR, 'latest_crawl'), basename(cm.CRAWL_DIR))


def parse_url_list(file_path, start, stop):
    """Return list of urls from a file."""
    try:
        with open(file_path) as f:
            # read file contents and split into elements
            file_contents = f.read()
            url_list = file_contents.splitlines()
            url_list = [url for url in url_list if url and not url.startswith('#')]
            url_list = url_list[start - 1:stop]
            processed_list = []
            for url in url_list:
                parsed = urlparse(url)
                if not parsed.hostname:
                    raise ValueError('URL {} has invalid hostname!'.format(url))
                processed_list.append(url)
    except Exception as e:
        wl_log.error("while parsing URL list: {} \n{}".format(e, traceback.format_exc()))
        sys.exit(-1)
    return processed_list


def parse_arguments():
    # Read configuration file
    config = ConfigParser.RawConfigParser()
    config.read(cm.CONFIG_FILE)

    # Parse arguments
    parser = argparse.ArgumentParser(description='Crawl a list of youtube URLs in multiple batches.')

    # List of urls to be crawled
    parser.add_argument('-u', '--url-file', required=True,
                        help='Path to the file that contains the list of video URLs to crawl.',
                        default=cm.VIDEO_LIST)
    parser.add_argument('-o', '--output',
                        help='Directory to dump the results (default=./results).',
                        default=cm.CRAWL_DIR)
    parser.add_argument('-c', '--config',
                        help="Crawler tor driver and controller configurations.",
                        choices=config.sections(),
                        default="default")
    parser.add_argument('-b', '--tbb-path',
                        help="Path to the Tor Browser Bundle directory.",
                        default=cm.TBB_DIR)
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='increase output verbosity',
                        default=False)
    parser.add_argument('-d', '--device', type=str, default='eth0',
                        help='Device interface on which to capture traffic.')
    parser.add_argument('--timeout', type=int, default=10,
                        help='Hard timeout (minutes) before video capture is interrupted.')

    # Crawler features
    parser.add_argument('-x', '--virtual-display',
                        help='Dimensions of the virtual display, eg 1200x800',
                        default=None)
    parser.add_argument('-s', '--screenshots', action='store_true',
                        help='Capture page screenshots',
                        default=False)

    # Limit crawl
    parser.add_argument('--start', type=int,
                        help='Select URLs starting with this line number: (default: 1).',
                        default=1)
    parser.add_argument('--stop', type=int,
                        help='Select URLs after this line number: (default: EOF).',
                        default=maxsize)

    # Parse arguments
    args = parser.parse_args()

    # Set verbose level
    wl_log.setLevel(DEBUG if args.verbose else INFO)
    del args.verbose

    # Change results dir if output
    cm.CRAWL_DIR = args.output
    del args.output

    # Change video load timeout
    cm.HARD_VISIT_TIMEOUT = args.timeout*60
    del args.timeout

    wl_log.debug("Command line parameters: %s" % argv)
    return args, config


class TorBrowserWrapper(object):
    """Wraps the TorBrowserDriver to configure it at the constructor
    and run it with the `launch` method.

    We might consider to change the TorBrowserDriver itself to follow
    torcontroller and stem behaviour: init configures and a method is
    used to launch driver/controller, and this method is the one used
    to implement the contextmanager.
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.driver = None

    def __getattr__(self, item):
        if self.driver is None:
            return
        if item == "launch":
            return getattr(self, item)
        return getattr(self.driver, item)

    @contextmanager
    def launch(self):
        caps = DesiredCapabilities().FIREFOX
        caps['pageLoadStrategy'] = 'eager'
        self.driver = TorBrowserDriver(*self.args, capabilities=caps, **self.kwargs)
        yield self.driver
        self.driver.quit()


if __name__ == '__main__':
    run()
