import charms.reactive as reactive
import os
import re
# This charm's library contains all of the handler code associated with
# dmapi
import charm.openstack.dmapi as dmapi
from subprocess import (
    check_output,
    check_call,
)

from charmhelpers.core.hookenv import (
    config,
    log,
    application_version_set,
)

from charmhelpers.fetch import (
    apt_update,
    apt_upgrade,
)

from charmhelpers.contrib.openstack.utils import (
    configure_installation_source,
)

from charmhelpers.core.host import (
    service_restart,
    adduser,
    add_group,
    add_user_to_group,
    chownr,
    mkdir,
)

# Minimal inferfaces required for operation
MINIMAL_INTERFACES = [
    'shared-db.available',
    'identity-service.available',
    'amqp.available',
]

DMAPI_USR = 'dmapi'
DMAPI_GRP = 'dmapi'


def get_new_version(pkg_name):
    """
    Get the latest version available on the TrilioVault node.
    """
    apt_cmd = "apt list {}".format(pkg_name)
    pkg = check_output(apt_cmd.split()).decode('utf-8')
    new_ver = re.search(r'\s([\d.]+)', pkg).group().strip()

    return new_ver


def add_user():
    """
    Adding passwordless sudo access to nova user and adding to required groups
    """
    try:
        add_group(DMAPI_GRP, system_group=True)
        adduser(DMAPI_USR, password=None, shell='/bin/bash', system_user=True)
        add_user_to_group(DMAPI_USR, DMAPI_GRP)
    except Exception as e:
        log("Failed while adding user with msg: {}".format(e))
        return False

    return True


# use a synthetic state to ensure that it get it to be installed independent of
# the install hook.
@reactive.when_not('charm.installed')
def install_packages():
    # Add TrilioVault repository to install required package
    # and add queens repo to install nova libraries
    if not add_user():
        log("Adding dmapi user failed!")
        return

    os.system('sudo echo "{}" > '
              '/etc/apt/sources.list.d/trilio-gemfury-sources.list'.format(
                  config('triliovault-pkg-source')))

    new_src = config('openstack-origin')
    configure_installation_source(new_src)

    if config('python-version') == 2:
        dmapi_pkg = 'dmapi'
    else:
        dmapi_pkg = 'python3-dmapi'

    apt_update()
    dmapi.install()
    # Placing the service file
    os.system('sudo cp files/trilio/tvault-datamover-api.service '
              '/etc/systemd/system/')
    chownr('/var/log/dmapi', DMAPI_USR, DMAPI_GRP)
    mkdir('/var/cache/dmapi', DMAPI_USR, DMAPI_GRP, perms=493)
    os.system('sudo systemctl enable tvault-datamover-api')
    service_restart('tvault-datamover-api')

    application_version_set(get_new_version(dmapi_pkg))
    reactive.set_state('charm.installed')


@reactive.when('amqp.connected')
def setup_amqp_req(amqp):
    """Use the amqp interface to request access to the amqp broker using our
    local configuration.
    """
    amqp.request_access(username='dmapi',
                        vhost='openstack')
    dmapi.assess_status()


@reactive.when('shared-db.connected')
def setup_database(database):
    """On receiving database credentials, configure the database on the
    interface.
    """
    database.configure('nova', 'nova', prefix='dmapinova')
    database.configure('nova_api', 'nova', prefix='dmapinovaapi')
    dmapi.assess_status()


@reactive.when('identity-service.connected')
def setup_endpoint(keystone):
    dmapi.configure_ssl()
    dmapi.setup_endpoint(keystone)
    dmapi.assess_status()


def render(*args):
    dmapi.render_configs(args)
    reactive.set_state('config.complete')
    # change the ownership to 'dmapi'
    chownr('/etc/dmapi', DMAPI_USR, DMAPI_GRP)
    dmapi.assess_status()


@reactive.when('charm.installed')
@reactive.when_not('cluster.available')
@reactive.when(*MINIMAL_INTERFACES)
def render_unclustered(*args):
    dmapi.configure_ssl()
    render(*args)


@reactive.when('charm.installed')
@reactive.when('cluster.available',
               *MINIMAL_INTERFACES)
def render_clustered(*args):
    render(*args)


@reactive.when('charm.installed')
@reactive.when('config.complete')
@reactive.when_not('db.synced')
def run_db_migration():
    dmapi.restart_all()
    reactive.set_state('db.synced')
    dmapi.assess_status()


@reactive.when('ha.connected')
def cluster_connected(hacluster):
    dmapi.configure_ha_resources(hacluster)


@reactive.hook('upgrade-charm')
def upgrade_charm():
    os.system('sudo echo "{}" > '
              '/etc/apt/sources.list.d/trilio-gemfury-sources.list'.format(
                  config('triliovault-pkg-source')))

    new_src = config('openstack-origin')
    configure_installation_source(new_src)

    apt_update()
    apt_upgrade(fatal=True, dist=True)

    chownr('/var/log/dmapi', DMAPI_USR, DMAPI_GRP)

    check_call(['systemctl', 'daemon-reload'])
    service_restart('tvault-datamover-api')

    if config('python-version') == 2:
        dmapi_pkg = 'dmapi'
    else:
        dmapi_pkg = 'python3-dmapi'

    application_version_set(get_new_version(dmapi_pkg))
