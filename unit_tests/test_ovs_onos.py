import testtools

from mock import call
from mock import patch
from mock import MagicMock

import reactive.main as ovs_onos_main

TO_PATCH = [
    'status_set',
    'kv',
    'subprocess',
    'ovs',
]

CONN_STRING = 'tcp:onos-controller:6640'
LOCALHOST = '10.1.1.1'


class CharmUnitTestCase(testtools.TestCase):

    def setUp(self, obj, patches):
        super(CharmUnitTestCase, self).setUp()
        self.patches = patches
        self.obj = obj
        self.patch_all()

    def patch(self, method):
        _m = patch.object(self.obj, method)
        mock = _m.start()
        self.addCleanup(_m.stop)
        return mock

    def patch_all(self):
        for method in self.patches:
            setattr(self, method, self.patch(method))


class MockUnitData():

    data = {}

    def set(self, k, v):
        self.data[k] = v

    def unset(self, k):
        if k in self.data:
            del self.data[k]

    def get(self, k):
        return self.data.get(k)

    def reset(self):
        self.data = {}


class TestOVSONOS(CharmUnitTestCase):

    def setUp(self):
        super(TestOVSONOS, self).setUp(ovs_onos_main, TO_PATCH)
        self.unitdata = MockUnitData()
        self.kv.return_value = self.unitdata

    def tearDown(self):
        super(TestOVSONOS, self).tearDown()
        self.unitdata.reset()

    def test_configure_openvswitch_not_installed(self):
        self.unitdata.unset('installed')
        onos_ovsdb = MagicMock()
        ovs_onos_main.configure_openvswitch(onos_ovsdb)
        self.assertFalse(self.subprocess.check_call.called)

    def test_configure_openvswitch_installed(self):
        self.unitdata.set('installed', True)
        onos_ovsdb = MagicMock()
        onos_ovsdb.connection_string.return_value = None
        ovs_onos_main.configure_openvswitch(onos_ovsdb)
        self.assertFalse(self.subprocess.check_call.called)

    def test_configure_openvswitch_installed_related(self):
        self.unitdata.set('installed', True)
        onos_ovsdb = MagicMock()
        onos_ovsdb.connection_string.return_value = CONN_STRING
        onos_ovsdb.private_address.return_value = 'onos-controller'
        ovs_onos_main.configure_openvswitch(onos_ovsdb)
        self.ovs.set_manager.assert_called_with(CONN_STRING)
        self.status_set.assert_called_with('active',
                                           'Open vSwitch configured and ready')

    def test_unconfigure_openvswitch_not_installed(self):
        self.unitdata.unset('installed')
        onos_ovsdb = MagicMock()
        ovs_onos_main.unconfigure_openvswitch(onos_ovsdb)
        self.assertFalse(self.subprocess.check_call.called)

    def test_unconfigure_openvswitch_installed(self):
        self.unitdata.set('installed', True)
        self.subprocess.check_output.return_value = 'br-int br-ex'
        onos_ovsdb = MagicMock()
        ovs_onos_main.unconfigure_openvswitch(onos_ovsdb)
        self.subprocess.check_call.assert_has_calls([
            call(['ovs-vsctl', 'del-manager']),
            call(['ovs-vsctl', 'del-controller', 'br-int']),
            call(['ovs-vsctl', 'del-controller', 'br-ex']),
        ])

    def test_configure_neutron_plugin(self):
        neutron_plugin = MagicMock()
        ovs_onos_main.configure_neutron_plugin(neutron_plugin)
        neutron_plugin.configure_plugin.assert_called_with(
            plugin='onos',
            config={
                "nova-compute": {
                    "/etc/nova/nova.conf": {
                        "sections": {
                            'DEFAULT': [
                                ('firewall_driver',
                                 'nova.virt.firewall.NoopFirewallDriver'),
                                ('libvirt_vif_driver',
                                 'nova.virt.libvirt.vif.'
                                 'LibvirtGenericVIFDriver'),
                                ('security_group_api', 'neutron'),
                            ],
                        }
                    }
                }
            }
        )
