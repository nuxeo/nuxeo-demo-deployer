# nuxeo-demo-deployer

Python based tooling to deploy demo instances of Nuxeo marketplace packages built
on Jenkins CI

Installs a Nuxeo Server using the Ubuntu package from
http://apt.nuxeo.org/dists/precise/ using PostgreSQL and upload markeplace packages.

# Install

The following will install the module in the home folder of the current user
from the source hosted on the master branch on github, along with the boto
package (dependency to connect to EC2.

    $ pip install -U --user -r https://raw.github.com/nuxeo/nuxeo-demo-deployer/master/requirements-master.txt

# Usage

Setup your AWS credentials in environment variables:

    $ export AWS_ACCESS_KEY_ID=XXXXXXXXX
    $ export AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXX

or alternatively put the credentials in a shared file

Simple example:

    $ python -m nxdd \
             --instance-name my_demo \
             --key-folder /opt/build/aws-keys \
             --package /path/to/my-marketplace-package-version.zip

Example with advanced parameters:

    $ python -m nxdd.commandline \
             --instance-name my_demo \
             --image-id ami-895069fd \
             --region-name eu-west-1 \
             --instance-type m1.large \
             --keypair-name my_demo \
             --keys-folder /opt/build/aws \
             --nuxeo-distribution 'precise releases' \
             --package /path/to/first-marketplace-package-version.zip \
             --package /path/to/second-marketplace-package-version.zip \
             --bid 0.1 \
             --aws-credentials /opt/build/aws/aws-credentials.json \
             --user ubuntu


# Developers

To install the development version (git clone source folder) on your system,
use the following instead:

    $ git clone https://github.com/nuxeo/nuxeo-demo-deployer.git
    $ cd nuxeo-demo-deployer
    $ pip install -r requirements.txt
    $ pip install -e .
