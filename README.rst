=====
pyess
=====

------------------------------------------------------------------------------
Python library for LG ESS Solar power converters with EnerVU app compatibility
------------------------------------------------------------------------------


.. image:: https://travis-ci.org/gluap/pyess.svg?branch=master
    :target: https://travis-ci.org/gluap/pyess?branch=master
.. image:: https://coveralls.io/repos/github/gluap/pyess/badge.svg?branch=master
    :target: https://coveralls.io/github/gluap/pyess?branch=master


Python library for communication with LG ESS power converter / energy storage devices for photovoltaic solar generators

This library is **not endorsed by the manufacturer**. It was written for lack of an official API. It should allow to
design home automation around the current state of a solar energy system - e.g. turn appliances on when there is surplus
solar power. LG only offers access via a badly scriptable web page or alternatively via a proprietary app that - at least
on my phone - crashes at least twice for every successful startup.

**Disclaimer:**
For this python module I reverse-engineered the communication between the *LG EnerVu Plus 1.2.3* Android
App and the Energy Storage / Inverter device, so there is some likelihood that it will work for devices that
can be accessed via that app. Nevertheless it looks like some of the interface is delivered by the ESS as html via the
network. Therefore it may be that not all commands work against all boxes. I only have customer-level access to my own
box, so this module only offers those parts of the API that are accessible to me as a customer. As far as I can tell
the installer has higher privileges and can fiddle with internal parameters of the system from what I saw him do when he
installed the system.


Usage
=====


Command Line
------------
This module comes with a rudimentary command line interface that allows for the following actions.

Fetch the device password
.........................

Caveat: **To fetch the device password you need to be connected to the devices wifi.** Once you are on the wifi you can
run the following to get the password. Write it down, it seems it is a static password per device::

    esscli --action get_password

The command assumes that the ess device is listening on ``192.168.23.1`` on its own wifi, in my setup it reproducibly
chooses that IP.

Find the esses on your network
..............................
Get a list of ESS devices on the local network (your home wifi, not the one of ess)::

    esscli --action list_ess


Fetch the state from ess as json
................................
fetch a bunch of json states as json and display the result on the command line::

    esscli --action get_data --password <your ess_password>

Examples for the data available:
- current power from and to the grid and the battery
- current voltage and power from both strings of the photovoltaic system independently
- current ip address
- details on grid power, battery state, daily and monthly statistics

Log ess state into a graphite server
....................................

This command will fetch the ``home`` and ``common`` info from ess every 10 seconds and log them against a graphite
server (assuming standard port and udp as protocol). Running this command requires the ess password to be passed on
the command line::

    esscli --action log_against_graphite --password <your_ess_password> --graphite <ip_of_graphite_server>


Sync ess state with an mqtt server (also accepts commands)
..........................................................

To connect your ESS with an mqtt server run the following in your venv::

    essmqtt --mqtt_server=<your_mqtt_server> --mqtt_user <your_mqtt_username> --mqtt_password <your_mqtt_password> --ess_password <your_ess_password>

Your ESS will show up in /ess/# on mqtt.

Available values to control the ess (write true/false) **Remember that this is an MIT-Licensed software and I take no responsibility for the usage of this library. That being said I send the same commands the app would send to trigger these actions to my best knowledge.**::

   /ess/control/winter_mode
   /ess/control/fastcharge
   /ess/control/active

Available paths with metrics to read from::

    ess/home/statistics/pcs_pv_total_power 0
    ess/home/statistics/batconv_power 190
    ess/home/statistics/bat_use 1
    ess/home/statistics/bat_status 2
    ess/home/statistics/bat_user_soc 81.25
    ess/home/statistics/load_power 191
    ess/home/statistics/load_today 0.0
    ess/home/statistics/grid_power 1
    ess/home/statistics/current_day_self_consumption 0.0
    ess/home/statistics/current_pv_generation_sum 0
    ess/home/statistics/current_grid_feed_in_energy 0
    ess/home/direction/is_direct_consuming_ 0
    ess/home/direction/is_battery_charging_ 0
    ess/home/direction/is_battery_discharging_ 1
    ess/home/direction/is_grid_selling_ 0
    ess/home/direction/is_grid_buying_ 1
    ess/home/direction/is_charging_from_grid_ 0
    ess/home/operation/status start
    ess/home/operation/mode 1
    ess/home/wintermode/winter_status on
    ess/home/pcs_fault/pcs_status pcs_ok
    ess/common/PV/brand LGE-SOLAR
    ess/common/PV/capacity 5850
    ess/common/PV/pv1_voltage 26.500000
    ess/common/PV/pv2_voltage 26.700001
    ess/common/PV/pv1_power 0
    ess/common/PV/pv2_power 0
    ess/common/PV/pv1_current 0.110000
    ess/common/PV/pv2_current 0.000000
    ess/common/PV/today_pv_generation_sum 0
    ess/common/PV/today_month_pv_generation_sum 438389
    ess/common/BATT/status 2
    ess/common/BATT/soc 81.2
    ess/common/BATT/dc_power 190
    ess/common/BATT/winter_setting on
    ess/common/BATT/winter_status on
    ess/common/BATT/safty_soc 20
    ess/common/BATT/today_batt_discharge_enery 135
    ess/common/BATT/today_batt_charge_energy 0
    ess/common/BATT/month_batt_charge_energy 72692
    ess/common/BATT/month_batt_discharge_energy 51250
    ess/common/GRID/active_power 2.790000
    ess/common/GRID/a_phase 230.899994
    ess/common/GRID/freq 49.959999
    ess/common/GRID/today_grid_feed_in_energy 0
    ess/common/GRID/today_grid_power_purchase_energy 0
    ess/common/GRID/month_grid_feed_in_energy 266094
    ess/common/GRID/month_grid_power_purchase_energy 7037
    ess/common/LOAD/load_power 191
    ess/common/LOAD/today_load_consumption_sum 135
    ess/common/LOAD/today_pv_direct_consumption_enegy 0
    ess/common/LOAD/today_batt_discharge_enery 135
    ess/common/LOAD/today_grid_power_purchase_energy 0
    ess/common/LOAD/month_load_consumption_sum 157890
    ess/common/LOAD/month_pv_direct_consumption_energy 99603
    ess/common/LOAD/month_batt_discharge_energy 51250
    ess/common/LOAD/month_grid_power_purchase_energy 7037
    ess/common/PCS/today_self_consumption 0.0
    ess/common/PCS/month_co2_reduction_accum 311256
    ess/common/PCS/today_pv_generation_sum 0
    ess/common/PCS/month_pv_generation_sum 438389
    ess/common/PCS/today_grid_feed_in_energy 0
    ess/common/PCS/month_grid_feed_in_energy 266094
    ess/common/PCS/pcs_stauts 3
    ess/common/PCS/feed_in_limitation 70
    ess/common/PCS/operation_mode 0

I use ``mosquitto_sub`` to find the values I'm interested in while debugging like so::

    mosquitto_sub -v -h <your_mqtt_server> -p 1883 -u <your_mqtt_user> -P <your_mqtt_password> -t "#"


API
---
For the time being please use the docstrings in the code on https://github.com/gluap/pyess as documentation for the
API. A good place to start is pyess/cli.py where you can find the implementation of the CLI. One thing available
via the API but not yet via the CLI is the data for the daily / weekly / monthly / yearly statistics graphs that can
be accessed via the EnerVu App.


Changelog
=========
**2020-04-29 0.1.2**
 - fix issue where esscli and essmqtt were incompatible with the app and confusing the web interface

**2020-04-26 0.1.1**
 - fix issue where commands via mqtt were not working
 - add ``--interval_seconds`` parameter for mqtt client to allow experimenting with poll timeouts on user side
 - fix logout handling on aiohttp

**2020-04-15 0.1.0**
 - fix issue with fetch_password using wrong IP
 - fix documentation
 - add new mqtt synchronization service script

**2019-11-03 0.0.3**
 - add aiohttp-based backend for use with asyncio

**2019-10-12 0.0.2**
 - some minor fixes

**2019-10-09 0.0.1**
 - More documentation
 - Initial commit for pypi relase

**License**::

    Copyright (c) 2019 Paul Görgen

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
