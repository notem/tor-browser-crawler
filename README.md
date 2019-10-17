tor-browser-crawler-video
===============
![DISCLAIMER](https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Dialog-warning-orange.svg/40px-Dialog-warning-orange.svg.png "experimental")  **experimental - PLEASE BE CAREFUL. Intended for reasearch purposes.**

This is a fork of the [tor-browser-crawler](https://github.com/webfp/tor-browser-crawler).
The project has been revised such that instead of capturing webpage loads, this crawler captures video loads.

## Usage

This project may be run natively on the host system or in a docker container.
If running natively, the required libraries and python 2.7 modules must be installed.
Reference the ``Dockerfile`` and ``requirements.txt`` for the list of requirements.
Running through docker is easier and more reproducible. 
As such, this section will focus on the docker container setup.

#### Steps
1. Install Docker
    * follow [their documentation](https://docs.docker.com/install/)
    * don't forget to add your user to the ``docker`` group after install
2. Build the docker container
    * install the ``make`` utility if it is not native on your system
    * run ``make build`` to compile the docker image
3. Setup your crawl configuration files
    * replace ``videos.txt`` with your list of youtube urls
    * edit ``Makefile`` to use the correct network interface
    * if you are crawling long videos, adjust the ``--timeout`` value in the ``Makefile``
    * make any desired changes to ``config.ini`` 
4. Start the crawl
    * run ``make run`` to launch a container
    * the logs and packet captures should appear in the newly created ``results`` directory
    
## Notes
* Library Versions
    * versions of some components are important as different version combinations may be incompatible
    * this project has been frozen to **v8.0.2** of the TBB
    * to use the latest TBB version, remove the version number from the ``dockerfile``
    * newer versions of TBB may however require different version of selenium and geckodriver

* PCAP Size Limit
    * the crawler is configured to capture up to ~120MB per video
    * if this limit is inadequate, adjust ``MAX_DUMP_SIZE`` in the ``common.py`` source file