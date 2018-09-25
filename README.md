# Domoticz_iDetect
Python plugin for Domoticz: Presence detection from wireless router  
See http://www.domoticz.com for more information on the platform.  
Discussion thread about this plugin: https://www.domoticz.com/forum/viewtopic.php?f=65&t=20467.

This plugin will use information from your wireless router to detect if wireless devices (phones) are present or absent. I believe this is the most efficient way, since other methods like geo-fencing (gps) or pinging phones might drain their batteries. The plugin will determine the chipset and interfaces of your router automatically, so it is not specific to one particular make and model of router.
You can configure multiple devices to look for by their MAC addresses. A Domoticz Device will be created for each one. Additionally a single "Anyone home" device will be created, which will be 'On' if any of the monitored devices is present. A override button allows you to temporarily override the presence status, which can be useful if you have visitors or to have another script take (partial) control of the presence status.

Please let me know if the plugin works for your router by leaving a message in the forum containing your router brand and model. If it doesn't work, then please include a relevant portion of the Domoticz log (after enabling debug mode on the plugin's configuration page).

![alt text](https://github.com/d-EScape/Domoticz_iDetect/blob/master/resources/devices-idetect021.jpg)

## Requirements:
(For the moment the plugin will not run on Windows, because of a unknown problem with the polling heartbeat. Help on fixing that will be appreciated!)
* Domoticz with python plugin framework enabled
* SSH service enabled on the router and accessible to Domoticz
* One of the following for ssh authentication to the router
  * Preferred option: SSH key based authentication between Domoticz and the router. Tricky to setup, but the secure and generally accepted way to authenticate from any program or script. See: http://www.linuxproblem.org/art_9.html for the steps te create a key. In the example A is the Domoticz machine and B the router. Putting the public key on the router will be different (even between routers).
    - step 1: Create a keyfile for the user account (root by default) that runs Domoticz.  
    The public and private key files should be in <homedir>/.ssh
    - step 2: Place the public(!) key on the router. Using the Asus/merlin firmware this can be done in the GUI. This will be different for other routers and might be impossible on many standard firmwares!
   * Alternative option: Enter a password on the plugin hardware configuration page and install sshpass on your (linux) Domoticz machine (sudo apt-get install sshpass).Domoticz will store the password in plain text. This is therefore less secure, but easier to setup.

## Installation:
Note: Always make sure Domoticz is setup to accept new devices/sensors (Domoticz settings). At least when starting the plugin for the first time and when adding new mac addresses to monitor.
* > cd ~/domoticz/plugins
* > git clone https://github.com/d-EScape/Domoticz_iDetect iDetect (or any other target directory you like)
* You should now have a ~/domoticz/plugins/iDetect directory that contains the plugin.py and two zip files for icons. In the future you can update the pluging by going into this directory and do a 'git pull'.
* Restart Domoticz
* Add the plugin in the Domoticz hardware configuration screen
* Configure the plugin with:
  - router ip address(es)
  - router username
  - router password (only needed if you don't have key based authentication setup)
  - mac addresses to monitor in the format (short) name=mac addrress, separated by a comma.  
  eg: phone1=F1:2A:33:44:55:66,phone2=B9:88:77:C6:55:44
  - 'remove obsolete' gives you a choice to automatically delete devices that are no longer in de above list of mac-addresses OR to show them as timedout.
  - interval between checks (i use 10 seconds)
  - a grace period after which phones are shown as absent (to deal with temporarily dropped connections).
  - you can enable a override button in case you want to automate or manually override the "Anyone home" device. The override butten (when enabled) can be controlled like any other Domoticz device (manual/api). 

## If it fails
If the plugin keeps throwing errors like "Could not retreive router capabilities from xxx.xxx.xxx.xxx” then it was unable to get information from the router
- check if you can logon to the router using ssh from the command line on the Domoticz host
- make sure you do this under the same user profile that is running Domoticz (might be root, while you are normally logged in as pi or another regular user)
- if you are asked for a password then key based authentication is not setup (no problem if you are using password based authentication)    

## Additional options and technical info
The plugin will try several chipset specific tools for monitoring wireless connections on your router. These tools are the most reliable and responsive way to tell if a device is connected (present) or not (absent). If no suitable tool can be found on the router the script will fall back on generic Linux commands that monitor the network bridge or arp table. A but slower to respond when someone leaves the house, but still usable (minutes instead of seconds). It is possible, but not necessary, te preconfigure the script and thereby skipping the automatic detection.
If you would like to have a additional tool for a thus far unsupported chipset added to the plugin then please leave a message on the forum.
- You can preconfigure the command(s) to use and the interface(s) to query per router like:   
`192.168.0.1=wl eth1 eth2&qcsapi_sockrpc eth5`   
In this example the wl command will be used to query interaces eth1 and eth2. The qcsapi_sockrpc will query eth5. Put an ampersand between two commands for the same router, not between the interface names or routers. You could also configure 192.168.0.1=brctl or 192.168.0.1=arp which would use the generic brctl or arp tool (don’t need interfaces specified).  
To make finding these commands easy the auto detect script will log them for you. You can just copy the parts from the Domoticz log after running it without reconfiguring any commands.
A Domoticz log line could look like this:    
`2018-09-13 22:30:41.751 Status: (iDetect) Using chipset specific wl command on router 192.168.0.1 for interfaces eth5 & eth6 (=wl eth5 eth6)`    
You want the part at the end, between parentheses. You can only specify commands that are supported by the plugin. For safety these are not actual shell commands, but identifiers for commands within the plugin. You can use obscure interface names that the plugin does not check for (although it would be better to leave a message on the forum to gat those added to the plugin).  
By preconfiguring you can reduce the startup time (with can be useful in large wifi infrastructures), deal with a obscure router or exclude certain interfaces from presence detection.  
This new option makes the #forcegeneric option (described below) kinda redundant, so i will probably remove that in a future version.
- (Deprecated! but backwards compatible for now) It is possible to force the plugin into using generic tools. This is not the preferred way, but can be useful in some situations. Because the plugin is already using all available settings fields i combined this setting with the 'WiFi Router IP address' field. If you add '#forcegeneric' behind the address(es) it will skip the detection of chipset specific tools (eg 192.168.0.1#forcegeneric). This option should be added at the and of the configuration line and will influence all routers configured (do not add it per router!). It should not be used in a multi router setup anyway (using a generic tool on a router will make absence detection slower and on some routers less reliable).
- If you need te specify different usernames for different routers, you can do so by adding username@ in front of the routers address, like: admin@192.168.0.1,root@192.168.0.2 (if you are using password based authentication, then the password must be the same on all routers)
- You can ignore a mac address (mobile device) from the 'Anyone home' detection. Just add #ignore behind the mac address in question. The device will still be monitored individually. Eg: phone1=11:22:33:44:55:66, phone2=33:44:55:66:77:88#ignore will only see anyone home when phone1 is present, but will still monitor both phone1 and phone2.

![alt text](https://github.com/d-EScape/Domoticz_iDetect/blob/master/resources/settings021.jpg)

## History:
**version 0.7.1**
- Added: You van specify a different ssh portnumber (optional) like: <host>:<port>
The hostname or ip of the router is still the only required configuration parameter, but the full options syntax is now:  
 <username>@<routerip>:<routerport>=<preconfigured poll command>

**version 0.7.0**
- Added: option to preconfigure the router commands (skipping auto detection) and a way to easily find out what to ‘preconfigure’. See github for instructions.
- Fixed: Router capability detection (compatibility with some firmwares that limit the ssh argument size).  
**`Important:`**
Please TEST the new version (watch te log) and leave a message on the forum if it fails where the previous version succeeded. There are changes in this version that i simply cannot test, because i don’t own every brand and model of router.

This release introduces a completely rewritten function to detect the router capabilities. Why fix something that doesn’t seem broken? Well, it turns out the original router (shell) part of the script was to long for some routers. In that case the ssh session would fail because the script was longer than the maximum length allowed for an ssh argument. So i used a shorter notation and broke it up into de detection of available commands and the detection of the interfaces to query. The new approach is also a bit easier to maintain (add or modify chipset support).

Using separate sessions for capabilities detection introduces some additional overhead, but only when the plugin/domoticz starts. It has zero impact on the poll times, since it generates the same poll commands as before.

An indication of the changed startup performance: The old detection function would take one session, which took 0.35 seconds on my Asus AC86. It will now take 2 sessions =  0.7 seconds. A router with two chipsets, like the AC87 will take 1+2 sessions = around 1 seconds. A mesh setup with three AC87’s will take 3 + 3x2 sessions, which translates into a little over 3 seconds. With the old function that same mesh setup would take around one second. If timeouts occur the wait time will quickly add up, so i lowered them to two seconds (per ssh session). That should not be a problem if your network, router and Domoticz host are in good shape, but please let me know if it proofs a little to close to the edge.
Thanks to mvzut for testing and for investigating why the capabilities detection was failing on his router!

**version 0.6.6**
- Improved: Debug logging for the ssh session now hides the ssh password. 
- Improved: Presence changes are now logged (without needing debug mode), so you can see something is going on.
- Improved: Some more log tweaking (removed some redundancies and changed log levels for some messages) 

**version 0.6.5**
- Improved: Lowering poll frequency on errors on a per router basis (one failed router will no longer affect the rest). 
- Improved: Less logging of non critical errors (one or two ssh failures is no reason to worry .. or log .. since the connection can recover on the next poll.)  

**version 0.6.3**
- Fixed: Error handling that was insufficient after introducing multi router support. 
- Fixed: Query for Quantenna chipset (Asus AC87 and others) was starting at wifi0 1  but should start at wifi0 0. 

**version 0.6.2**
- Added: You can now use different passwords for routers by configuring them as username@routerip (otherwise global username on the configuration page will be used).
- Added: Displaying the time a ssh command takes when in debug mode.
- Enhanced: Password is no longer displayed in the debug log.
- Fixed: Grep command for some openwrt routers. 

**version 0.6.1**
- Added: Ability to monitor multiple routers (eg in Mesh setup)
- Added: Option to ignore individual mac addresses from the 'Anyone Home' detection. The device in question will still be monitored individually.
- Fixed: The poll frequency did not reset to its original setting after a ssh failure was restored. 

**version 0.5.0**
- Added: Support voor routers with more than one wifi chipset (like Asus AC87)
- Added: Option to force plugin to use arp commands instead of wifi tools
- Improved: Error handling on startup (and more meaningful messages)

**version 0.4.2**
- Changed: No longer requires python3.5 (just 3.4 which is already required for the plugin framework in Domoticz)

**version 0.4.2**
- Added: An option to force the plugin to use generic linux commands on the router instead of trying several wifi driver specific tools. Can be used if you also want to monitor ethernet connected devices (not really what the plugin is intended for) or when the wifi tools are somehow not usable on your router make and model.

**version 0.4.1**
- Fixed: Beter handling of poll intervals of over 30 seconds
- Canged: Configuration of the poll interval is now a pull-down (don't forget to set it when upgrading)
- Fixed: Minor improvements on error handling (limit poll frequency after repeated ssh errors)

**version 0.4.0**
**Upgrade note! make sure you also download the new ioverride.zip file. It contains the required icons.**
- Added: A override switch that let's you force the 'Anyone home' to 'On' even if no phones are detect. You can configure it's behavior: disabled, override for a fixed time, override until the next time a phone is detected or leave it on indefinitely. The latter is also a great way to control the 'Anyone home' status from other scripts in parallel.
Use case: Broken router, broken phone or any other reason you cannot confirm your presence. If you use the plugin to control alarms or home automation tasks, such situations can be very annoying.
For security you can mark the Override switch as 'protected' in the Domoticz device properties.
- Added: Experimental support for routers that use wlanconfig command

**version 0.3.3**
- Added: fall back to reading /proc/net/arp file if it exists and al other methods are unavailable
- Fixed: no longer assuming devices are present if the plugin (or domoticz) is restarted

**version 0.3.1**
- Check if ssh and (if needed) sshpass are available on the host OS

**version 0.3.0**
- It is now possible to change the names of the devices after they have been created
- Devices are now identified by the DeviceID (friendly name in Domoticz) instead of their display name
- The names you configure are best kept short, since they are now also DeviceID's in the device list.
- Changing the name on the hardware configuration page will now result in a new device (and the old one being deleted or shown offline, depending on you setting for deleted devices)
- __**Beware!**__  
After installing this version your existing devices will be **deleted** and new ones will be created. If you do not change the configuration the initial names will be the same as before.

**version 0.2.3**  
- Added: Wider router brand and model support by adding iwinfo command as a method to poll the router for info (next to existing wl and arp methods).
- Some minor optimizations.

**version 0.2.2**  
- Adapted the configuration to use Dnpwwo's password field option. The (optional) password will no longer be shown in plain text. 

**version 0.2.1**  
- Improved error handling and added some sensible logging if certain error occur

**version 0.2.0**  
Some *major changes* in this release:
- Added password based authentication as an option instead of key based (which is still preferred)
- Added router capabilities detection instead of assuming wl command is available

Key based ssh authentication is still the preferred method, but since it can be challenging to setup there is now an alternative. If you enter a password in the password field the plugin will use sshpass to login to the router using username/password authentication. You must have sshpass installed (sudo apt-get install sshpass). That's all. Beware that the password is stored and shown in plain text within Domoticz.

The plugin will no longer just assume you have a router with the wl command (mostly broadcom based routers) or that the wifi interfaces are always eth1 and eth2. Instead it will try to detect some parameters when initializing, using a shell script it runs on the router.
- If it can't find the wl command (to query the wifi interfaces) it will try to use arp (routing information from the router) instead.
- Next all existing network interfaces are queried bij wl to see which ones are in use for your wifi network (not needed for arp).

Existing users: Please revisit the hardware settings page, since some parameters have changed.

Thanks to Innovator for the arp suggestion!

I hope this will make the plugin less dependent on the brand/model router. There is no way for me to test it on any other router than my Asus ac86u. If it is not working for you, then please let me know. Be sure to include logs (set the plugin to debug mode and restart it first).

If the plugin keeps throwing errors like "Could not retreive router capabilities from xxx.xxx.xxx.xxx” then check the authentication settings and if the router is reachable. The initialization described above didn't work for the router in question. If the error message persists you should disable the plugin because it might flood the Domoticz event system with retries. The methods used in this plugin might not be compatible with your router.

**version 0.0.2**  
- Fixed: wl command not found on stock Asus firmware because of missing PATH in ssh session
- Changed: MAC addresses can be configured in upper or lower case. The plugin will convert them to upper case.
- Changed: MAC addresses and corresponding device names may contain leading or trailing spaces. They will be stripped by the plugin. 
- Changed: Different error message in the log for connection failures or data errors. Makes more sense.
