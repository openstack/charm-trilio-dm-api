import os
import charmhelpers.contrib.openstack.utils as ch_utils
import charms_openstack.charm
import charms_openstack.adapters
import charms_openstack.ip as os_ip

from charmhelpers.core.hookenv import (
    config
)

DMAPI_DIR = '/etc/dmapi'
DMAPI_CONF = os.path.join(DMAPI_DIR, 'dmapi.conf')


class DmapiDBAdapter(charms_openstack.adapters.DatabaseRelationAdapter):
    """Get database URIs for the two nova databases"""

    @property
    def dmapi_nova_uri(self):
        """URI for nova DB"""
        return self.get_uri(prefix='dmapinova')

    @property
    def dmapi_nova_api_uri(self):
        """URI for nova_api DB"""
        return self.get_uri(prefix='dmapinovaapi')


class DmapiAdapters(charms_openstack.adapters.OpenStackAPIRelationAdapters):
    """
    Adapters class for the Data Mover API charm.
    """
    relation_adapters = {
        'shared_db': DmapiDBAdapter,
    }


class DmapiCharm(charms_openstack.charm.HAOpenStackCharm):

    # Internal name of charm + keystone endpoint
    service_name = 'dmapi'
    name = 'trilio-dm-api'

    # First release supported
    release = 'queens'

    # Packages the service needs installed
    if config('python-version') == 3:
        packages = ['python3-nova', 'python3-dmapi']
    else:
        packages = ['python-nova', 'dmapi']

    # Init services the charm manages
    services = ['tvault-datamover-api']

    # Ports that need exposing.
    default_service = 'dmapi-api'
    api_ports = {
        'dmapi-api': {
            os_ip.PUBLIC: config('public-port'),
            os_ip.ADMIN: config('admin-port'),
            os_ip.INTERNAL: config('internal-port'),
        }
    }

    # Database sync command used to initalise the schema.
    sync_cmd = []

    # The restart map defines which services should be restarted when a given
    # file changes
    restart_map = {
        DMAPI_CONF: services,
    }

    adapters_class = DmapiAdapters

    # Resource when in HA mode
    ha_resources = ['vips', 'haproxy']

    # DataMover requires a message queue, database and keystone to work,
    # so these are the 'required' relationships for the service to
    # have an 'active' workload status.  'required_relations' is used in
    # the assess_status() functionality to determine what the current
    # workload status of the charm is.
    required_relations = ['amqp', 'shared-db', 'identity-service']

    def __init__(self, release=None, **kwargs):
        """Custom initialiser for class
        If no release is passed, then the charm determines the release from the
        ch_utils.os_release() function.
        """
        if release is None:
            release = ch_utils.os_release('python-keystonemiddleware')
        super(DmapiCharm, self).__init__(release=release, **kwargs)

    def install(self):
        """Customise the installation, configure the source and then call the
        parent install() method to install the packages
        """
        self.configure_source()
        # and do the actual install
        super(DmapiCharm, self).install()

    @property
    def public_url(self):
        return super().public_url + "/v2"

    @property
    def admin_url(self):
        return super().admin_url + "/v2"

    @property
    def internal_url(self):
        return super().internal_url + "/v2"


def install():
    """Use the singleton from the DmapiCharm to install the packages on the
    unit
    """
    DmapiCharm.singleton.install()


def restart_all():
    """Use the singleton from the DmapiCharm to restart services on the
    unit
    """
    DmapiCharm.singleton.restart_all()


def setup_endpoint(keystone):
    """When the keystone interface connects, register this unit in the keystone
    catalogue.
    """
    charm = DmapiCharm.singleton
    keystone.register_endpoints(charm.service_name,
                                charm.region,
                                charm.public_url,
                                charm.internal_url,
                                charm.admin_url)


def render_configs(interfaces_list):
    """Using a list of interfaces, render the configs and, if they have
    changes, restart the services on the unit.
    """
    DmapiCharm.singleton.render_with_interfaces(interfaces_list)


def assess_status():
    """Just call the DmapiCharm.singleton.assess_status() command to update
    status on the unit.
    """
    DmapiCharm.singleton.assess_status()


def configure_ha_resources(hacluster):
    """Use the singleton from the DmapiCharm to run configure_ha_resources
    """
    DmapiCharm.singleton.configure_ha_resources(hacluster)


def configure_ssl():
    """Use the singleton from the DmapiCharm to run configure_ssl
    """
    DmapiCharm.singleton.configure_ssl()
