import subprocess

import lib.ovs as ovs

from charmhelpers.core.hookenv import config
from charmhelpers.core.hookenv import log
from charmhelpers.core.hookenv import status_set
from charmhelpers.core.reactive import hook
from charmhelpers.core.reactive import when
from charmhelpers.core.reactive import when_not
from charmhelpers.core.unitdata import kv

from charmhelpers.fetch import apt_install
from charmhelpers.fetch import apt_purge
from charmhelpers.fetch import filter_installed_packages
from subprocess import check_call

# Packages to install/remove
PACKAGES = ['openvswitch-switch']
DEBPACKS = ['dkms', 'libc6-dev', 'make', 'kmod', 'netbase', 'procps',
            'python-argparse', 'uuid-runtime', 'python:any', 'libssl1.0.0',
            'linux-headers-3.16.0-71-generic']


@when('ovsdb-manager.access.available')
def configure_openvswitch(onos_ovsdb):
    db = kv()
    # NOTE(jamespage): Check connection string as well
    #                  broken/departed seems busted right now
    if db.get('installed') and onos_ovsdb.connection_string():
        log("Configuring OpenvSwitch with ONOS controller: %s" %
            onos_ovsdb.connection_string())
        ovs.set_manager(onos_ovsdb.connection_string())
        status_set('active', 'Open vSwitch configured and ready')


@when_not('ovsdb-manager.access.available')
def unconfigure_openvswitch(onos_ovsdb=None):
    db = kv()
    if db.get('installed'):
        log("Unconfiguring OpenvSwitch")
        subprocess.check_call(['ovs-vsctl', 'del-manager'])
        bridges = subprocess.check_output(['ovs-vsctl',
                                           'list-br']).split()
        for bridge in bridges:
            subprocess.check_call(['ovs-vsctl',
                                   'del-controller', bridge])
        status_set('waiting',
                   'Open vSwitch not configured with ONOS controller')


@when_not('ovsdb-manager.connected')
def no_ovsdb_manager(onos_ovsdb=None):
    status_set('blocked', 'Not related to ONOS controller')


@when('neutron-plugin.connected')
def configure_neutron_plugin(neutron_plugin):
    neutron_plugin.configure_plugin(
        plugin='onos',
        config={
            "nova-compute": {
                "/etc/nova/nova.conf": {
                    "sections": {
                        'DEFAULT': [
                            ('firewall_driver',
                             'nova.virt.firewall.'
                             'NoopFirewallDriver'),
                            ('libvirt_vif_driver',
                             'nova.virt.libvirt.vif.'
                             'LibvirtGenericVIFDriver'),
                            ('security_group_api', 'neutron'),
                        ],
                    }
                }
            }
        })


@hook('install')
def install_packages():
    db = kv()
    if not db.get('installed'):
        status_set('maintenance', 'Installing packages')
        if config('profile') == 'onos-sfc':
            apt_install(filter_installed_packages(DEBPACKS))
            check_call("sudo wget http://205.177.226.237:9999/onosfw\
                  /package_ovs_debian.tar.gz -O ovs.tar", shell=True)
            check_call("sudo tar xvf ovs.tar", shell=True)
            check_call("sudo dpkg -i openvswitch-common_2.5.90-1_amd64.deb",
                       shell=True)
            check_call("sudo dpkg -i openvswitch-datapath-dkms_\
                       2.5.90-1_all.deb", shell=True)
            check_call("sudo dpkg -i openvswitch-switch_2.5.90-1_amd64.deb",
                       shell=True)
        else:
            apt_install(filter_installed_packages(PACKAGES))
        db.set('installed', True)


@hook('stop')
def uninstall_packages():
    db = kv()
    if db.get('installed'):
        status_set('maintenance', 'Purging packages')
        apt_purge(PACKAGES)
        db.unset('installed')
