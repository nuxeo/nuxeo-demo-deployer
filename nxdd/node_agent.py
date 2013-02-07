#!/usr/bin/env python
"""Stand alone Python script to be executed on the instance to set it up."""
from __future__ import print_function

import socket
import sys
import os

HOSTNAME = socket.gethostname()
NUXEO_CONF = '/etc/nuxeo/nuxeo.conf'
NUXEO_HOME = '/var/lib/nuxeo/server'
NUXEO_CONFIG_DIR = NUXEO_HOME + '/nxserver/config'


# TODO: turn this into a template to make it possible to deploy several
# Nuxeo instances with different ports and vhosts on the same EC2
# instance
NUXEO_VHOST = """\
<VirtualHost _default_:80>

    CustomLog /var/log/apache2/nuxeo_access.log combined
    ErrorLog /var/log/apache2/nuxeo_error.log

    DocumentRoot /var/www

    ProxyRequests Off
    <Proxy *>
        Order allow,deny
        Allow from all
    </Proxy>

    RewriteEngine On
    RewriteRule ^/$ /nuxeo/ [R,L]
    RewriteRule ^/nuxeo$ /nuxeo/ [R,L]

    ProxyPass        /nuxeo/ http://localhost:8080/nuxeo/
    ProxyPassReverse /nuxeo/ http://localhost:8080/nuxeo/
    ProxyPreserveHost On

    # WSS
    ProxyPass        /_vti_bin/     http://localhost:8080/_vti_bin/
    ProxyPass        /_vti_inf.html http://localhost:8080/_vti_inf.html
    ProxyPassReverse /_vti_bin/     http://localhost:8080/_vti_bin/
    ProxyPassReverse /_vti_inf.html http://localhost:8080/_vti_inf.html

</VirtualHost>
"""


def cmd(command):
    """Fail early to make it easier to troubleshoot"""
    pflush("[%s]> %s" % (HOSTNAME, command))
    code = os.system(command)
    if code != 0:
        raise RuntimeError("Error executing: " + command)


def sudocmd(command, user=None):
    if user is not None:
        command = "sudo -E -u " + user + " " + command
    else:
        command = "sudo -E " + command
    cmd(command)


def pflush(*args, **kwargs):
    """Flush stdout for making Jenkins able to monitor the progress"""
    print(*args, **kwargs)
    sys.stdout.flush()


def debconfselect(pkg, param, value):
    """Preselect DPKG options before installing in non-interactive mode"""
    cmd("echo %s %s select %s | debconf-set-selections" % (pkg, param, value))


def getconfig(filepath, param, default=None):
    """Read a parameter from a config file"""
    with open(filepath, 'rb') as f:
        for line in f:
            if line.strip().startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            if k.strip() == param:
                return v.strip()
    return default


def setconfig(filepath, param, value):
    """Edit a config file to set / add a parameter to a specific value"""

    with open(filepath, 'rb') as f:
        lines = f.readlines()
    with open(filepath, 'wb') as f:
        updated = False
        for line in lines:
            if line.strip().startswith('#') or '=' not in line:
                # keep comments and other non informative lines unchanged
                f.write(line)
                continue
            k, v = line.split('=', 1)
            if k.strip() == param:
                # update with new value
                f.write('%s=%s\n' % (param, value))
                updated = True
            else:
                # keep line unchanged
                f.write(line)
        if not updated:
            # append the new param at the end of the file
            f.write('%s=%s\n' % (param, value))


def check_install_nuxeo(upgrade=False,
						distribution="precise releases",
    					apt_url="http://apt.nuxeo.org/",
						key_url="http://apt.nuxeo.org/nuxeo.key"):
    """Check that Nuxeo is installed from the latest datebased release"""

    # Ensure the datebased release repo is configured and up to date
    with open('/etc/apt/sources.list', 'rb') as f:
        sources = f.readlines()
        nuxeo_sources = [s for s in sources
                             if (not s.strip().startswith('#')
                                 and distribution in s
                                 and apt_url in s)]
    if not nuxeo_sources:
        cmd('apt-add-repository "deb %s %s"' % (apt_url, distribution))
        cmd("wget -O- %s| apt-key add -" % key_url)
    cmd("apt-get update")
    if upgrade:
        cmd("apt-get upgrade -y")

    # Pre-accept Sun Java license & set Nuxeo options
    debconfselect("sun-java6-jdk", "shared/accepted-sun-dlj-v1-1", "true")
    debconfselect("sun-java6-jre", "shared/accepted-sun-dlj-v1-1", "true")
    debconfselect("nuxeo", "nuxeo/bind-address", "127.0.0.1")
    debconfselect("nuxeo", "nuxeo/http-port", "8080")
    debconfselect("nuxeo", "nuxeo/database", "Autoconfigure PostgreSQL")

    # Install or upgrade Nuxeo
    cmd("export DEBIAN_FRONTEND=noninteractive; "
                "apt-get install -y nuxeo")

def setup_nuxeo(marketplace_packages=()):
    pflush('Configuring Nuxeo server for the demo')

    # Skip wizard
    setconfig(NUXEO_CONF, 'nuxeo.wizard.done', 'true')

    # Need many concurrent core session to play HTML5 videos in chrome
    setconfig(NUXEO_CONF, 'nuxeo.vcs.max-pool-size', '100')

    # Define an environment variable to locate the nuxeo configuration
    os.environ['NUXEO_CONF'] = NUXEO_CONF

    # Shutting down nuxeo before update
    cmd('service nuxeo stop')

    # Register default nuxeo marketplace packages usually available in the
    # wizard
    nuxeoctl = NUXEO_HOME + '/bin/nuxeoctl'

    pflush('Full purge of existing marketplace packages')
    sudocmd(nuxeoctl + ' mp-purge --accept true', user='nuxeo')
    sudocmd(nuxeoctl + ' mp-init', user='nuxeo')

    pflush('Deploying DM')
    sudocmd(nuxeoctl + ' mp-install nuxeo-dm --accept true', user='nuxeo')
    pflush('Deploying DAM')
    sudocmd(nuxeoctl + ' mp-install nuxeo-dam --accept true', user='nuxeo')

    for package in marketplace_packages:
        pflush('Deploying / upgrading marketplace package ' + package)
        sudocmd(nuxeoctl + ' mp-install --accept=true --nodeps file://'
            + os.path.abspath(package), user='nuxeo')

    # Restarting nuxeo
    cmd('service nuxeo start')

def check_install_vhost():
    cmd("apt-get install -y apache2")
    filename = '/etc/apache2/sites-available/nuxeo'
    if not os.path.exists(filename):
        with open(filename, 'wb') as f:
            f.write(NUXEO_VHOST)

    cmd("a2enmod proxy proxy_http rewrite")
    cmd("a2dissite default")
    cmd("a2ensite nuxeo")
    cmd("apache2ctl -k graceful")


if __name__ == "__main__":
    check_install_nuxeo()
    setup_nuxeo(sys.argv[1:])
    check_install_vhost()