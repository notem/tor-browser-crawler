tor-browser-crawler
===============
![DISCLAIMER](https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Dialog-warning-orange.svg/40px-Dialog-warning-orange.svg.png "experimental")  **experimental - PLEASE BE CAREFUL. Intended for reasearch purposes.**

This is a fork of the [tor-browser-crawler](https://github.com/webfp/tor-browser-crawler), updated to run correctly with updated libraries and TBB version.

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
    * replace ``sites.txt`` with the list of websites you wish to crawl
    * edit ``Makefile`` to use the correct network interface
    * adjust the ``--timeout`` value in the ``Makefile`` to higher values if needed
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

* Crawler has been modified to use the ``tcpdump`` utiltity in place of ``dumpcap`` to capture traffic.
    * This avoids runtime issues that exist when using ``dumpcap`` on some system configurations.
