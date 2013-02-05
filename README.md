# nuxeo-demo-deployer

Python based tooling to deploy demo instances of Nuxeo marketplace packages built
 on Jenkins CI

# Install

	pip install -r requirements.txt
	pip install .

# Usage

	$ export AWS_ACCESS_KEY_ID=XXXXXXXXX
	$ export AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXX

	$ python -m nxdd \
	         --instance-name my_demo_box \
	         --image-id ami-895069fd \
	         --region-name eu-west-1 \
	         --instance-type m1.large \
	         --application-name my_demo_app \
	         --nuxeo-version 5.6.0 \
	         --package my-marketplace-package-version.zip \
	         --database postgresql \
	         --user ubuntu