# Overview

This charm provides the TrilioVault Data Mover API service which forms
part of the [TrilioVault Cloud Backup solution][trilio.io].

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

# Bugs

Please report bugs on [Launchpad][lp-bugs-charm-trilio-dm-api].

[lp-bugs-charm-trilio-dm-api]: https://bugs.launchpad.net/charm-trilio-dm-api/+filebug
[trilio.io]: https://www.trilio.io/triliovault/openstack
