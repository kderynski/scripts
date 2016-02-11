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

from nav.db import getConnection
import json
import re
import urllib2
import string

# config section
SERVER_HOSTNAME = "example.com"
DASHBORD_NAME = "dashboard_name"
url = "https://" + SERVER_HOSTNAME + "/grafana/api/dashboards/db/" + DASHBORD_NAME
authStr = "grafana auth string"
req = urllib2.Request(url, headers={'Authorization': authStr})
urlPost = "https://" + SERVER_HOSTNAME + "/grafana/api/dashboards/db"
# end of config section

alphabet = list(string.ascii_uppercase)
new = {}

# functions


def printTargets(d):
    """ Print targets from json - only for debug."""
    print "len rows = " + str(len(d['model']['rows']))
    for i in range(len(d['model']['rows'])):
        for j in range(len(d['model']['rows'][i]['panels'])):
            try:
                targets = d['model']['rows'][i]['panels'][j]['targets']
                targetsLen = len(targets)
                for z in range(targetsLen):
                    print targets
            except:
                pass


def dictFromNavDB():
    """Build dict from nav DB - key: (device, port) value: description."""
    sqlSelect = "SELECT netbox.sysname, interface.ifname, interface.ifalias "
    sqlFrom = "FROM netbox JOIN interface USING (netboxid)"
    query = sqlSelect + sqlFrom
    cursor = getConnection('default').cursor()
    cursor.execute(query)

    navDict = {}
    row = cursor.fetchone()
    while row is not None:
        key = (row[0].replace("/", "_").replace(".", "_"),
               row[1].replace("/", "_").replace(".", "_"))
        navDict[key] = row[2]
        row = cursor.fetchone()
    return navDict


def aliasesToDesc(d):
    for i in range(len(d['model']['rows'])):
        for j in range(len(d['model']['rows'][i]['panels'])):
            try:
                targetsLen = len(d['model']['rows'][i]['panels'][j]['targets'])
                for z in range(targetsLen):
                    target = d['model']['rows'][i][
                        'panels'][j]['targets'][z]['target']
                    b = re.search(
                        'nav\.devices\.([_\w-]+)\.ports\.([_\w-]+)\.', target)
                    if b is not None:
                        key = (b.group(1), b.group(2))
                    else:
                        #print 'failed for %s' % target
                        continue
                    if "timeShift" in target:
                        continue
                    elif "alias" in target:
                        splitedTarget = d['model']['rows'][i]['panels'][
                            j]['targets'][z]['target'].split("'")
                        # remove existing alias part
                        # print splitedTarget[0][6:-2]
                        # result = splitedTarget[
                        #    0] + "'" + navDict[key] + "'" + splitedTarget[2]
                        # result = "removeAboveValue(" + target + ", 100000000000)"
                        result = "alias(removeAboveValue(" + splitedTarget[0][6:-2] + ", 100000000000), '" + \
                                                    navDict[key] + "')"
                    else:
                        result = "alias(removeAboveValue(" + target + ", 100000000000), '" + \
                            navDict[key] + "')"
                    d['model']['rows'][i]['panels'][j][
                        'targets'][z]['target'] = result
            except KeyError:
                pass


def addTimeShifts(d):
    for i in range(len(d['model']['rows'])):
        for j in range(len(d['model']['rows'][i]['panels'])):

            timeShiftMetricList = []
            timeShiftTarget = None
            try:
                targetsLen = len(d['model']['rows'][i]['panels'][j]['targets'])
                for z in range(targetsLen):
                    char = "#" + alphabet[z]
                    timeShiftMetricList.append(char)
                    target = d['model']['rows'][i]['panels'][
                        j]['targets'][z]['target'].split("'")
                    if "timeShift" in str(target):
                        timeShiftTarget = z

                if timeShiftTarget:
                    metric = "alias(timeShift(sumSeries(" + \
                        ",".join(timeShiftMetricList)[
                            :-1] + "),\"7d\" ),\"last_week\")"
                else:
                    metric = "alias(timeShift(sumSeries(" + \
                        ",".join(timeShiftMetricList) + \
                        "),\"7d\" ),\"last_week\")"
                new = {"hide": False, "target": metric}

                if timeShiftTarget:
                    d['model']['rows'][i]['panels'][j][
                        'targets'][timeShiftTarget] = new
                else:
                    d['model']['rows'][i]['panels'][j]['targets'].append(new)
                d['model']['rows'][i]['panels'][j]['seriesOverrides'] = [
                    {
                        "alias": "last_week",
                        "fill": 0,
                        "linewidth": 2,
                        "stack": False
                    }]
                d['model']['rows'][i]['panels'][j][
                    'aliasColors']['last_week'] = "#BADFF4"
            except KeyError:
                print "Key error"


def convert2Grafana(d):
    c = {}
    c['dashboard'] = {}
    c['dashboard']['id'] = d['model']['id']
    c['dashboard']['title'] = d['model']['title']
    c['dashboard']['rows'] = d['model']['rows']
    c['overwrite'] = True
    return c
# end of functions

# convert whole dashboard to json format
r = urllib2.urlopen(req)
d = json.loads(r.read())

# build dict with key: (device, port) value: description from NAV database
navDict = dictFromNavDB()

# convert/add description as an alias in grafana dashboard
aliasesToDesc(d)
addTimeShifts(d)

# print all targets after conversion (for debug only)
# printTargets(d)

results = json.dumps(convert2Grafana(d))
header = {
    'Authorization': authStr,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
reqPost = urllib2.Request(urlPost, results, headers=header)
urllib2.urlopen(reqPost)
