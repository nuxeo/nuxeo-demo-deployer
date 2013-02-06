# nuxeo-demo-deployer

Python based tooling to deploy demo instances of Nuxeo marketplace packages built
on Jenkins CI

Installs a Nuxeo Server using the Ubuntu package from
http://apt.nuxeo.org/dists/precise/	using PostgreSQL and upload a 

# Install

	pip install -r requirements.txt
	pip install .

# Usage

Setup your AWS credentials in environment variables:

	$ export AWS_ACCESS_KEY_ID=XXXXXXXXX
	$ export AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXX

Simple example:

	$ python -m nxdd \
	         --instance-name my_demo \
	         --key-folder /opt/build \
	         --package /path/to/my-marketplace-package-version.zip

Custom example:

	$ python -m nxdd \
	         --instance-name my_demo \
	         --image-id ami-895069fd \
	         --region-name eu-west-1 \
	         --instance-type m1.large \
	         --keypair-name my_demo \
	         --key-folder /opt/build \
	         --nuxeo-distribution 'precise releases' \
	         --package /path/to/first-marketplace-package-version.zip \
             --package /path/to/second-marketplace-package-version.zip \
	         --user ubuntu

