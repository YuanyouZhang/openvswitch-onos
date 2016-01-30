#!/bin/bash
ifconfig | grep onos_port

if [ $? -eq 1 ];then
  
  external_port="eth1";
  
  if [[ -z "$1" ]]; then
    return 1
  else
    external_port=$1
  fi
  
  ifconfig | grep br-ex

  if [ $? -eq 1 ];then
    echo "create br-ex with ${external_port} in computer node"
    sudo ovs-vsctl add-br br-ex
    sudo ovs-vsctl add-port br-ex ${external_port}
  fi

  echo "ready to create onos_port"
  sudo ip link add onos_port1 type veth peer name onos_port2
  sudo ifconfig onos_port1 up
  sudo ifconfig onos_port2 up

  external_mac=$(ifconfig ${external_port} | \
                 grep -Eo "[0-9a-f\]+:[0-9a-f\]+:[0-9a-f\]+:[0-9a-f\]+:[0-9a-f\]+:[0-9a-f\]+")

  sudo ifconfig onos_port2 hw ether ${external_mac}
  sudo ovs-vsctl add-port br-ex onos_port1
else
  echo "onos_port already exist"

fi
