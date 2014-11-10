#!/bin/bash
#simply restart touchpad on e4310 dell notebook
#xinput list
xinput set-prop 14 "Device Enabled" 0
xinput set-prop 14 "Device Enabled" 1