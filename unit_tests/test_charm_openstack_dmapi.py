from __future__ import absolute_import
from __future__ import print_function

import mock
import sys

import charm.openstack.dmapi as dmapi

import charms_openstack.test_utils as test_utils


class Helper(test_utils.PatchHelper):

    def setUp(self):
        super().setUp()
        self.patch_release(dmapi.DmapiCharm.release)


class TestDmapiDBAdapter(Helper):

    def fake_get_uri(self, prefix):
        return 'mysql://uri/{}-database'.format(prefix)

    def test_dmapi_uri(self):
        relation = mock.MagicMock()
        a = dmapi.DmapiDBAdapter(relation)
        self.patch_object(dmapi.DmapiDBAdapter, 'get_uri')
        self.get_uri.side_effect = self.fake_get_uri
        self.assertEqual(a.dmapi_nova_uri, 'mysql://uri/dmapinova-database')
        self.assertEqual(a.dmapi_nova_api_uri, 'mysql://uri/dmapinovaapi-database')


class TestDmapiAdapters(Helper):

    @mock.patch.object(dmapi, 'hookenv')
    def test_dmapi_adapters(self, hookenv):
        reply = {
            'keystone-api-version': '3',
        }
        hookenv.config.side_effect = lambda: reply
        self.patch_object(
            dmapi.adapters.APIConfigurationAdapter,
            'get_network_addresses')
        cluster_relation = mock.MagicMock()
        cluster_relation.endpoint_name = 'cluster'
        amqp_relation = mock.MagicMock()
        amqp_relation.endpoint_name = 'amqp'
        shared_db_relation = mock.MagicMock()
        shared_db_relation.endpoint_name = 'shared_db'
        other_relation = mock.MagicMock()
        other_relation.endpoint_name = 'other'
        other_relation.thingy = 'help'
        # verify that the class is created with a DmapiConfigurationAdapter
        b = dmapi.DmapiAdapters([amqp_relation,
                               cluster_relation,
                               shared_db_relation,
                               other_relation])
        # ensure that the relevant things got put on.
        self.assertTrue(
            isinstance(
                b.other,
                dmapi.adapters.OpenStackRelationAdapter))
