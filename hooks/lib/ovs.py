import subprocess


def set_manager(connection_url):
    '''Configure the OVSDB manager for the switch'''
    subprocess.check_call(['ovs-vsctl', 'set-manager', connection_url])
