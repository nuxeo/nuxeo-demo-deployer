#! /usr/bin/env python
#
# Copyright (C) 2013 Nuxeo and contributors

DESCRIPTION = """Python based tooling for deploying demo Nuxeo instances"""
VERSION = '0.1.0'

from distutils.core import setup

setup(
    name="nuxeo-demo-deployer",
    maintainer="Nuxeo",
    maintainer_email="contact@nuxeo.com",
    description=DESCRIPTION,
    license="BSD",
    url="http://github.com/nuxeo/nuxeo-demo-deployer",
    version=VERSION,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved',
        'Programming Language :: Python',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: MacOS',
        ])
