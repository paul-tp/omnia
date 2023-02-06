# Copyright 2023 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
---

- name: Initialize variables
  ansible.builtin.set_fact:
    nics_dict: {}
    nics_list: []

- name: Fetch the network interfaces in UP state in the system
  ansible.builtin.shell: set -o pipefail && /usr/sbin/ip a | awk '/state UP/{print $2}'
  register: nic_addr_up
  changed_when: false

- name: Create a list of NICs
  ansible.builtin.set_fact:
    nics_list: "{{ nics_list + [item.split(':')[0]] }}"
  with_items: "{{ nic_addr_up.stdout.split('\n') }}"

- name: Append NICs and subnets to dictionary
  ansible.builtin.set_fact:
    nics_dict: '{{ nics_dict | combine({item: lookup("vars", "ansible_" + item).ipv4.network}) }}'
  with_items: "{{ nics_list }}"

- name: Fetch the BMC NIC
  ansible.builtin.set_fact:
    bmc_nic: "{{ item.key }}"
  when: item.value == bmc_nic_subnet
  with_dict: "{{ nics_dict }}"

- name: Fetch BMC NIC IP and netmask details
  ansible.builtin.set_fact:
    bmc_nic_ip: "{{ lookup('vars', 'ansible_' + bmc_nic).ipv4.address }}"
    bmc_nic_netmask: "{{ lookup('vars', 'ansible_' + bmc_nic).ipv4.netmask }}"

- name: Configure bmc_network in networks table with static ranges
  ansible.builtin.shell: >
    chdef -t network -o bmc_network net={{ bmc_nic_subnet }} mask={{ bmc_nic_netmask }} mgtifname={{ bmc_nic }}
    gateway={{ bmc_nic_ip }} dhcpserver={{ bmc_nic_ip }} dynamicrange="{{ bmc_dynamic_start_range }}-{{ bmc_dynamic_end_range }}"
    staticrange="{{ bmc_static_start_range }}-{{ bmc_static_end_range }}"
  changed_when: true
  when: bmc_static_status

- name: Configure bmc_network in networks table without static ranges
  ansible.builtin.shell: >
    chdef -t network -o bmc_network net={{ bmc_nic_subnet }} mask={{ bmc_nic_netmask }} mgtifname={{ bmc_nic }}
    gateway={{ bmc_nic_ip }} dhcpserver={{ bmc_nic_ip }} dynamicrange="{{ bmc_dynamic_start_range }}-{{ bmc_dynamic_end_range }}"
  changed_when: true
  when: not bmc_static_status
 
