#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Copyright 2015 Kamil Derynski, Opera Software ASA
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy of
# the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations under
# the License.

import psycopg2
import sys
import json
import datetime
import re
import ipaddr

con = None
q = "select sysname, ifname, netaddr, vlan.vlan, ifalias, roomid,  active_ip_cnt from interface left outer join gwportprefix on (gwportprefix.interfaceid = interface.interfaceid) left outer join prefix on (gwportprefix.prefixid = prefix.prefixid) left outer join prefix_active_ip_cnt on (prefix_active_ip_cnt.prefixid = prefix.prefixid) left outer join vlan on (vlan.vlanid = prefix.vlanid) left outer join netbox on (netbox.netboxid = interface.netboxid)"

data = {}
data['interfaces']= []
data['timestamp'] = str(datetime.datetime.now())
pattern = '(\.|Vlan\s)\d+$' 


try:     
    con = psycopg2.connect(database='nav')
    cur = con.cursor()
    cur.execute(q)
    ver = cur.fetchall()
   #sysname, ifname, netaddr, vlan.vlan
    for i in ver:
        vlan_name = i[4]
        if i[2] != None:
            vlan = i[3]
            if i[3] == None:
                b = re.search(pattern, str(i[1]), re.IGNORECASE)
                if b:
                    if "Vlan " in b.group(0):
                        vlan = int(b.group(0)[5:])
                    else:
                        vlan = int(b.group(0)[1:])
                    if "st0" in i[1]:
                        vlan = 0
                else:
                    vlan = 0
            if vlan == 0:
                vlan_name = ''
            else:
                vlan_name = i[4]
            net = ipaddr.IPNetwork(i[2])
            if i[6]:
                active_ips = int(i[6])
                active_ips_supported = True
            else:
                active_ips = 0
                active_ips_supported = False
            data['interfaces'].append({'prefix':i[2], 'network':str(net.network), 'netmask':str(net.netmask), 'prefix_len':net.prefixlen ,'active_ips':active_ips, 'active_ips_supported':active_ips_supported, 'version':net.version, 'device': i[0], 'interface':i[1], 'vlan_id': int(vlan), 'vlan_name':vlan_name, 'datacenter':i[5]})

                
    json_data = json.dumps(data, sort_keys=True,
                  indent=4, separators=(',', ': '))
    print json_data

except psycopg2.DatabaseError, e:
    print 'Error %s' % e    
    sys.exit(1)
    
    
finally:
    if con:
        con.close() 
