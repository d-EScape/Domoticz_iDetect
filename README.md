# Domoticz_iDetect
Python plugin for Domoticz: Presence detection from wireless router  
See http://www.domoticz.com for more information on the platform.  
Discussion thread about this plugin: https://www.domoticz.com/forum/viewtopic.php?f=65&t=20467).

This plugin will use information from your wireless router to detect if devices (phones) are present or absent. I believe this is the most efficient way, since other methods like geo-fencing (gps) or pinging phones might drain their batteries. 
You can configure multiple devices to look for by their MAC addresses. A Domoticz Device will be created for each one. Additionally a single "Anyone home" device will be created, which will be 'On' if any of the monitored devices is present.

Please let me know if the plugin works for your router by leaving a message in the forum containing your router brand and model. If it doesn't work, then please include a relevant portion of the Domoticz log (after enabling debug mode on the plugin's configuration page).

![alt text](https://github.com/d-EScape/Domoticz_iDetect/blob/master/resources/devices-idetect021.jpg)

## Requirements:
* Domoticz with python plugin framework enabled (currently only the Domoticz beta)
* SSH service enabled on the router and accesible to Domoticz
* One of the following for ssh authentication to the router
  *Preferred option: SSH key based authentication between Domoticz and the router. Tricky to setup, but the secure and generally accepted way to authenticate from any program or script. See: http://www.linuxproblem.org/art_9.html for the steps te create a key. In the example A is the Domoticz machine and B the router. Putting the public key on the router will be different (even between routers).
step 1: Create a keyfile for the user account (root be default) that runs Domoticz.
step 2: Place the public(!) key on the router. Using the asus merlin firmware this can be done in the GUI. This will be different for other routers and might be impossible on many standard firmwares!
The public and private key files should be in <homedir>/.ssh for the user running Domoticz(!)
   *Alternative option: Enter a password on the plugin hardware configuration page and install sshpass on your (linux) Domoticz machine (sudo apt-get install sshpass).Domoticz will store the password in plain text. This is therefore less secure, but far easier to setup.[/list][/list]

## Installation:
* > cd ~/domoticz/plugins
* > git clone https://github.com/d-EScape/Domoticz_iDetect iDetect (or any other target directory you like)
* You should now have a ~/domoticz/plugins/iDetect directory that contains the plugin.py and two zip files for icons. In the future you can update the pluging by going into this directory and do a 'git pull'.
* Restart Domoticz
* Add the plugin in the Domoticz hardware configuration screen
* Configure the plugin with:
  - router ip address
  - router username
  - router password (only needed if you don't have key based authentication setup)
  - mac addresses to monitor in the format name=mac addrress separated by a comma eg: phone1=F1:2A:33:44:55:66,phone2=B9:88:77:C6:55:44
  -'remove obsolete' gives you a choice to automatically delete devices that are no longer in de above list of mac-addresses OR to show them as timedout.
  - interval between checks (i use 10 seconds)
  - a grace period after which phones are shown as absent (to deal with temporarily dropped connections).

![alt text](https://github.com/d-EScape/Domoticz_iDetect/blob/master/resources/settings021.jpg)

## History:
**Update 04/05/2018 version 0.2.3**

- Addded: Wider router brand and model support by adding iwinfo command as a method to poll the router for info (next to existing wl and arp methods).
- Some minor optimizations.

**Update 04/05/2018 version 0.2.2**

- Adapted the configuration to use Dnpwwo's password field option. The (optional) password will no longer be shown in plain text. 

**Update 04/05/2018 version 0.2.1**

- Improved error handling and added some sensible logging if certain error occur

**Update 02/05/2018 version 0.2.0**

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

If the plugin keeps throwing errors like "No usable commandline to check presence. Trying again to detect router capabilities." then check the authentication settings and if the router is reachable. The initialization described above didn't work. If the error message persists you should disable the plugin because it might flood the Domoticz event system with retries. The methods used in this plugin might not be compatible with your router.

**Update 13/02/2018 version 0.0.2**

- Fixed: wl command not found on stock Asus firmware because of missing PATH in ssh session
- Changed: MAC addresses can be configured in upper or lower case. The plugin will convert them to upper case.
- Changed: MAC addresses and corresponding device names may contain leading or trailing spaces. They will be stripped by the plugin. 
- Changed: Different error message in the log for connection failures or data errors. Makes more sense.
