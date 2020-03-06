# Overview

TrilioVault Data Mover API provides API service for TrilioVault Datamover

# Usage

TrilioVault Data Mover API relies on services from mysql, rabbitmq-server
and keystone charms. Steps to deploy the charm:

    juju deploy trilio-dm-api
    juju deploy keystone
    juju deploy mysql
    juju deploy rabbitmq-server

    juju add-relation trilio-dm-api rabbitmq-server
    juju add-relation trilio-dm-api mysql
    juju add-relation trilio-dm-api keystone

# Configuration

python-version: "Openstack base python version(2 or 3)"

NOTE - Default value is set to "3". Please ensure to update this based on python version since installing
       python3 packages on python2 based setup might have unexpected impact.

TrilioVault Packages are downloaded from the repository added in below config parameter. Please change this only if you wish to download
TrilioVault Packages from a different source.

triliovault-pkg-source: Repository address of triliovault packages

# Contact Information

Trilio Support <support@trilio.com>
