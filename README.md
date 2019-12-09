# Domoticz_iDetect v2

The modular and highly tweakable version that also runs on Windows :D

iDetect is a python plugin for Domoticz, which allows you to detect the presence of devices using various methods. Since version 2 it has also become a framework that can relatively easily be extended to support other types of presence detection.

### (New) features
* Running on Windows
* Adding additional detection methods (it is designed to be a framework)
* Ping devices on your network (not the preferred method, but can be useful)
* Getting connected devices from router through ssh (as before)
* Auto detecting the correct method for ssh routers (as before)
* Using your own ssh command(s)
* Tweaking individual settings for ‘tags’ (eg your mobile phone)
* Getting connected devices from Netgear Orbi using http api (as an example for adding other methods)

### (New) requirements
* the python module 'paramiko' needs to be installed (sudo pip3 install paramiko on linux)
* Python 3.5 or newer
* No longer needs sshpass for password based authentication (paramiko takes care of that.

More information and support can be found on the Domoticz forum topic at https://www.domoticz.com/forum/viewtopic.php?f=65&t=20467.\

Version 2 introduces some changes in the way the plugin is configured. Most older configuration will still work, but *check your logs for any messages indicating you are using a deprecated configuration syntax*.\

I kept the configuration as backwards compatible as possible, so it will work in most cases, for the time being…
The advanced options have been improved and this will be the syntax going forward. The old options will probably stop working in the future (if I decide to do some clean-up).\

There are some (configuration) breaking changes. E.g. `#ignore` changed to `#ignore=true`. The new syntax is explained below.\

First off… the labels on some configuration fields have changed, without really changing the fields (because that would break an existing configuration)\
‘Wifi router IP Address’ is now called tracker(s)\
‘MAC addresses to monitor’ is now called ‘tags’\

I think these names better reflect their function, since other devices than routers can now track tags and tags are not necessarily MAC addresses.

### Configuration syntax
There are several ways to configure some settings, but only one value will be used. Priority is taken by (high to low):
* New style configuration
* Old style configuration
* Global setting (corresponding field on the plugin’s settings page)

#### Tracker configuration
`<ip address>#<options>`\
Trackers should be separated by comma (,)\

Or (for backward compatibility)\
`<username>@<ip address>:<port>=<type>#<options>`

###### Options syntax
option1=value1&option2=value2&option3=value3\
For valid options see below\
Values can not contain comma, ampersand or equals sign!\

Only the IP address is mandatory. The plugin will use defaults for all other parameters.\
Example:\
`192.168.1.1`\
This configuration will use the globally set username and password to connect to 192.168.1.1. It will use ssh and automatically detect the command to be used (if supported by the plugin)\

Example:\
`192.168.1.1:2022#type=routeros&interval=30&user=admin&password Monday`\
In this example the username and password are specific to this tracker. Port 2020 is used instead of the default (22). The routeros tracker module is used instead of ssh autodetection. The poll interval is 30 seconds instead of the globally set poll interval.\

Backwards compatibility:\
`admin@192.168.1.1=routeros`\
Will still work. This was the old style configuration. The new style is preferred, but i put extra effort in maintaining some backward compatibility for (most) existing users. Especially for when this version becomes the master branch and might be installed automatically.\

Valid options for trackers are:\
port=Port number\
type=tracker module to use (see `__init__.py` in the tacker directory for supported tracker types)\
user=user name on the tracker (for ssh the ssh username)\
password=\
keyfile=individual keyfile to use for this tracker (only relevant for ssh)\
interval=number of seconds between polls\
disabled=true/false (so you can temporarily disable a tracker without having to delete its configuration)\
ssh=(a short command line to run instead of detecting/specifying modules)\

If the `ssh` option is specified then the `type` is ignored and a basic ssh tracker is started. The command specified is used and nothing is autodetected.\
E.g. `ssh=brctl` would use a basic ssh tracker and poll using a brctl command on the ssh host (router).\
`ssh=wl -i eth5 assoclist; wl -i eth6 assoclist` would use a basic ssh tracker and poll using a wl command on the ssh host twice (notice the semicolon). Once for eth5 and once for eth6 (they could be in one wl command, but hey, its an example;-))\

Be warned: the ssh option can be a powerful tool, but there is no fixed syntax, no checking if it is safe or if the router actually knows the command(s)! No extra path is added, so if the command is not in the routers path then you need to call it using a full path.  etc etc etc …\
*Opportunity:* Turning your specific ssh command into a module might benefit the community of you share as a pull request or on the forum!\

#### Tags configuration
`<name>=<identifier>#<options>`\

The name is the device name shown in the domoticz user interface and will also be used as the unit id.\
Identifiers can (for now) be MAC addresses or ip addresses. Ip addresses will be treated differently! They will be monitored by a special ping tracker. The ping tracker will only run if there are any ip addresses configured as tags.\

The options syntax for tags is the same as for trackers, but a tag obviously has some other options:\

ignore=true (to ignore a tag for the anyone home status and just track it individually)\
interval=number of seconds between poll (will only be used by IP address tags to set a per tag ping interval. Or any other future type of tag that has an individual poll method)\
grace=number of seconds after a last confirmation of presence that a device is assumed to be absent (must be higher than poll interval, otherwise it will be presumed absent before the next poll takes place!)\

A tag will still accept `#ignore` as a single(!) option (so without the =true part), again to maintain backward compatibility, so please change it.

#### Extra’s

I included a ‘dummy’ module. If you specify a tracker like `192.168.1.1#type=dummy` , then nothing is actually polled, but a (hard coded) list of Mac addresses is returned to the plugin on every ‘poll’. This can be useful for testing.

