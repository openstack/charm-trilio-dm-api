# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import collections
import os

import charms_openstack.adapters as adapters
import charms_openstack.ip as os_ip
import charms_openstack.plugins as plugins

import charmhelpers.contrib.openstack.utils as ch_utils
import charmhelpers.core.hookenv as hookenv

DMAPI_DIR = "/etc/dmapi"
DMAPI_CONF = os.path.join(DMAPI_DIR, "dmapi.conf")


class DmapiDBAdapter(adapters.DatabaseRelationAdapter):
    """Get database URIs for the two nova databases"""

    @property
    def dmapi_nova_uri(self):
        """URI for nova DB"""
        return self.get_uri(prefix="dmapinova")

    @property
    def dmapi_nova_api_uri(self):
        """URI for nova_api DB"""
        return self.get_uri(prefix="dmapinovaapi")


class DmapiAdapters(adapters.OpenStackAPIRelationAdapters):
    """
    Adapters class for the Data Mover API charm.
    """

    relation_adapters = {
        "amqp": adapters.RabbitMQRelationAdapter,
        "cluster": adapters.PeerHARelationAdapter,
        "coordinator_memcached": adapters.MemcacheRelationAdapter,
        "shared_db": DmapiDBAdapter,
    }


class DmapiCharm(plugins.TrilioVaultCharm):

    # Internal name of charm + keystone endpoint
    service_name = "dmapi"
    name = "trilio-dm-api"

    # First release supported
    release = "queens"

    # Init services the charm manages
    services = ["tvault-datamover-api"]

    # Ports that need exposing.
    default_service = "dmapi-api"
    api_ports = {
        "dmapi-api": {
            os_ip.PUBLIC: hookenv.config("public-port"),
            os_ip.ADMIN: hookenv.config("admin-port"),
            os_ip.INTERNAL: hookenv.config("internal-port"),
        }
    }

    # Database sync command used to init the schema.
    sync_cmd = ["true"]

    # The restart map defines which services should be restarted when a given
    # file changes
    restart_map = {DMAPI_CONF: services}

    adapters_class = DmapiAdapters

    # Resource when in HA mode
    ha_resources = ["vips", "haproxy"]

    service_type = "dmapi"

    # DataMover requires a message queue, database and keystone to work,
    # so these are the 'required' relationships for the service to
    # have an 'active' workload status.  'required_relations' is used in
    # the assess_status() functionality to determine what the current
    # workload status of the charm is.
    required_relations = ["amqp", "shared-db", "identity-service"]

    user = "root"
    group = "dmapi"

    package_codenames = {
        "dmapi": collections.OrderedDict([("3", "stein")]),
        "python3-dmapi": collections.OrderedDict(
            [("3", "stein"), ("4", "train")]
        ),
    }

    def __init__(self, release=None, **kwargs):
        """Custom initialiser for class
        If no release is passed, then the charm determines the release from the
        ch_utils.os_release() function.
        """
        if release is None:
            release = ch_utils.os_release("python-keystonemiddleware")
        super(DmapiCharm, self).__init__(release=release, **kwargs)

    def get_amqp_credentials(self):
        return ("dmapi", "openstack")

    def get_database_setup(self):
        return [
            {"database": "nova", "username": "nova", "prefix": "dmapinova"},
            {
                "database": "nova_api",
                "username": "nova",
                "prefix": "dmapinovaapi",
            },
        ]

    @property
    def public_url(self):
        return "{}/v2".format(super().public_url)

    @property
    def admin_url(self):
        return "{}/v2".format(super().admin_url)

    @property
    def internal_url(self):
        return "{}/v2".format(super().internal_url)

    @property
    def packages(self):
        if hookenv.config("python-version") == 3:
            return ["python3-nova", "python3-dmapi"]
        return ["python-nova", "dmapi"]

    @property
    def version_package(self):
        if hookenv.config("python-version") == 3:
            return "python3-dmapi"
        return "dmapi"

    @property
    def release_pkg(self):
        return self.version_package
