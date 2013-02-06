"""Parse the commandline or fallback to default options.

The following command should be parseable::

	$ python -m nxdd.commandline \
	         --instance-name my_demo \
	         --image-id ami-895069fd \
	         --region-name eu-west-1 \
	         --instance-type m1.large \
	         --keypair-name my_demo \
	         --keys-folder /opt/build/aws-keys \
	         --nuxeo-distribution 'precise releases' \
	         --package /path/to/first-marketplace-package-version.zip \
             --package /path/to/second-marketplace-package-version.zip \
	         --user ubuntu

"""
from __future__ import print_function
import sys
import argparse

from nxdd.controller import Controller

# From http://cloud-images.ubuntu.com/desktop/precise/current/

DEFAULT_INSTANCE_NAME = 'nuxeo_demo'
DEFAULT_NUXEO_DISTRIBUTION = 'precise releases'  # Can be datebased or snapshots
DEFAULT_IMAGE_ID = 'ami-1f8c8e6b'  # Ubuntu 12.04 64bits for eu-west-1
DEFAULT_INSTANCE_TYPE = 'm1.large'
DEFAULT_REGION_NAME = 'eu-west-1'
DEFAULT_KEYS_FOLDER = '~/aws-keys'
DEFAULT_USER = 'ubuntu'


def make_cli_parser():
    """Parse commandline arguments using a git-like subcommands scheme"""

    parser = argparse.ArgumentParser(
        description="Deploy a Nuxeo demo server on EC2.",
    )
    parser.add_argument(
        "--instance-name",
        help="Name (tag) of the EC2 instance to reuse or create.",
        default=DEFAULT_INSTANCE_NAME,
    )
    # TODO: add --application-name option to be able to deploy several
    # nuxeo instances
    parser.add_argument(
        "--image-id",
        help=("AMI to use if a new instance is created. "
        	  "Need to agree with region-name."),
        default=DEFAULT_IMAGE_ID,
    )
    parser.add_argument(
        "--region-name",
        help=("EC2 region name to use if a new instance is created."),
        default=DEFAULT_REGION_NAME,
    )
    parser.add_argument(
        "--instance-type",
        help=("EC2 instance type use if a new instance is created."),
        default=DEFAULT_INSTANCE_TYPE,
    )
    parser.add_argument(
        "--keypair-name",
        help=("SSH keypair to connect to the instance. Automatically "
        	  "set to instance-name by default."),
    )
    parser.add_argument(
        "--keys-folder",
        help=("Local folder to store the private keys. Needs to be "
         	  "shared by all Jenkins CI slave running this script. "
         	  " Typically /opt/build/aws-keys at Nuxeo."),
        default=DEFAULT_KEYS_FOLDER,
    )
	# TODO: do not use the debian packages but instead make it possible
    # to deploy from a raw zip distribution of nuxeo so as to make it
    # possible to run several Nuxeo demos with different versions and
    # DB / data folders with separate vhost configuations.
    parser.add_argument(
        "--nuxeo-distribution",
        help=("APT distribution of Nuxeo to use."),
        default=DEFAULT_NUXEO_DISTRIBUTION,
    )
    parser.add_argument(
        "--package", nargs="*", default=(), dest='packages',
        help=("Market place package to install on the demo."),
    )
    parser.add_argument(
        "--user",
        help=("UNIX user to used to deploy the demo. "
        	  "Requires sudoer's rights."),
        default=DEFAULT_USER,
    )
    return parser


def main(argv=sys.argv[1:]):
	parser = make_cli_parser()
	options = parser.parse_args(argv)

	if options.keypair_name is None:
		options.keypair_name = options.instance_name

	ctl = Controller(options.region_name, options.keypair_name,
					 options.keys_folder, ssh_user=options.user)


	return 0

if __name__ == "__main__":
	sys.exit(main())









