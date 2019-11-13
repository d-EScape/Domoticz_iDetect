# Domoticz_iDetect BETA 2.0

iDectect 2.0 .. the modular and highly tweakable edition

This version is a work in progress (as is this documentation) en must be considered a beta. Bugs are to be expected! Please leave some feedback on the domoticz forum. This will help me to improve functionality and squash those pesky bugs.
The forum can be found at at https://www.domoticz.com/forum/viewtopic.php?f=65&t=20467.

* What do you like and dislike about this version?
* Did you run into any problems?
* How is it performing in your setup (and what does your setup look like)?

The documentation is also a work in progress, but let me at least share the new configuration syntax. I kept is as backwards compatible as possible, so most users won't have to change their configuration. The advanced options have been improved.

There are some (configuration) breaking changes. E.g. #ignore changed to #ignore=true. The new syntax is explained below.

First off… the labels on some configuration fields have changed, without really changing the fields (because that would break an existing configuration)
‘Wifi router IP Address’ is now called tracker(s)
‘MAC addresses to monitor’ is now called ‘tags’

I think these names better reflect their function, since other devices than routers can now track tags and tags are not necessarily MAC addresses.

New features
* The (now) modular plugin offers the possibility to build (and share!) your own ways of detecting presence, while still using the functionality of this plugin (like override, anyone home etc.)
* Other types of tags can be build into the plugin. Right now mac-addresses and ip-addresses (will ping) work. Not interchangeable though!
* Several parameters, like poll interval, password and keyfile can now be configured on a per tracker basis (using advanced options described below)
* Tags can also be configured individually

Configuration syntax
There are several ways to configure some settings, but only on value will be use. Priority is taken by (high to low):
* New style configuration 
* Old style configuration
* Global setting (corresponding field on the plugin’s settings page)

Tracker configuration
<ip address>#<options>
Trackers should be separated by comma (,)

Or (for backward compatibility)
<username>@<ip address>:<port>=<type># <options>

Options syntax
option1=value1&option2=value2&option3=value3 
For valid options see below
Values can not contain comma, ampersand (&) or equals sign (=)!

Only the IP address is mandatory. The plugin will use defaults for all other parameters. 
Example: 
192.168.1.1

This configuration will use the globally set username and password to connect to 192.168.1.1. It will use ssh and automatically detect the command to be used (if supported by the plugin)

Example:
192.168.1.1:2022#type=routeros&interval=30&user=admin&password Monday


In this example the username and password are specific to this tracker. Port 2020 is used instead of the default (22). The routeros tracker module is used instead of ssh autodetection. The poll interval is 30 seconds instead of the globally set poll interval.


Backwards compatibility:
admin@192.168.1.1=routeros 


Will still work. This was the old style configuration. The new style is preferred, but i put extra effort in maintaining some backward compatibility for (most) existing users. Especially for when this version becomes the master branch and might be installed automatically.


Valid options for trackers are:   
port=Port number   
type=module to use   
user=user name on the tracker (for ssh the ssh username)   
password=    
keyfile=keyfile to use for this tracker (only relevant for ssh)    
interval=number of seconds between polls    
disabled=true/false (so you can temporarily disable a tracker without having to delete its configuration)     
ssh=(a short command line to run instead of detecting/specifying modules)      

If the ‘ssh’ option is specified then the ‘type’ is ignored and a basis ssh tracker is started. The command specified is used and nothing is autodetected.
E.g. ‘ssh=brctl’ would use a basic ssh tracker and poll using a brctl command on the ssh host (router). 
‘ssh=wl -i eth5 assoclist; wl -i eth6 assoclist ’ would use a basic ssh tracker and poll using a wl command on the ssh host twice (notice the semicolon). Once for eth5 and once for eth6 (they could be in one wl command, but hey, its an example;-))

Be warned: the ssh option can be a powerful tool, but there is no fixed syntax, no checking if it is safe or if the router actually knows the command(s). No extra path is added, so if the command is not in the routers path then you need to call it using a full path.  etc etc etc … 
Opportunity: Turning your specific ssh command into a module might benefit the community!

Tags configuration    
<name>=<identifier>#<options>


The name is the device name shown in the domoticz user interface and will also be used as unit id.
Identifiers can (for now) be MAC addresses or ip addresses. Ip addresses will be treated differently! They are not monitored by the configured trackers, but by a special ping tracker. The ping tracker will only run if there are any ip addresses configured as tags.
Options syntax is the same as for trackers. The options for tags are:


ignore=true (to ignore a tag for the anyone home status and just track it individually)     
interval=number of seconds between poll (will only be used by IP address tags to set a per tag ping interval. Otherwise the default ping interval of 30 seconds is used)      
grace=number of seconds after a last confirmation of presence that a device is assumed to be absent (must be higher than poll interval!)      


A tag will still accept #ignore as a single(!) option (so without the =true part), again to maintain backward compatibility.


Limitations
Although you can theoretically set a poll interval or grace offline period to anything, even a second or 0 seconds, those speeds will not work as expected. The heartbeat of the plugin runs every 4 seconds, so nothing will be faster than that. It should not really matter because such low interval values are not really practical.
Also bare in mind that the ping tracker will start a separate ping process for every tag. That might become a problem with a lot of ip’s to ping. So I set the hard coded ping interval to 60 seconds and would advice you to set higher intervals per tag where possible. Only lower intervals where needed.


Extra’s


I included a ‘dummy’ module. If you specify a tracker like 192.168.1.1#type=dummy , then nothing is actually polled, but a (hard coded) list of Mac addresses is returned to the plugin on every interval. Can be useful for testing.

