# domoticz-efesto
Domoticz Efesto Heater Plugin

Work in progress! Not yet tested.

Short summary
-------------

Add virtual devices for your Efesto (compatible) heater to your [Domoticz](https://www.domoticz.com/)

Control your pellet heater from Domoticz. For example with a Tado or other smart home thermostat.

You will need to add the Wifi module to your pellet heater for this to work.
There is no official API, but the web-app uses an ajax interface that can be used by Domoticz.
You will have to login to the interface and copy the PHPSESSID from the headers after login. 
Use developer tools (F12 in Chrome -> Network) to find it.

Installation and setup
----------------------

If you are use a Raspberry Pi to host your Domoticz, you probably need to install libpython3.4 for plugins to work.

```bash
sudo apt install libpython3.4
```

At the moment of writing you also need to install:

```bash
sudo apt install python3-dev
```

In your `domoticz/plugins` directory do

```bash
cd domoticz/plugins
git clone https://github.com/appelflap/domoticz-efesto.git
```

Alternatively you can download the latest version from
https://github.com/appelflap/domoticz-efesto/archive/master.zip
and unzip it. Then create a directory on your Domoticz device
in `domoticz/plugins` named `efesto` and transfer all the
files to your device.

Restart your Domoticz service with:

```bash
sudo service domoticz.sh restart
```

Now go to **Setup**, **Hardware** in your Domoticz interface. There you add
**Efesto Heater Control**.

Make sure you enter all the required fields.
