# time-attendence

time-attendence is a Gui application for Raspberry Pi to stamp the RFID cards.
Works with every usb RFID card reader (working like a keyboard). 10 digits.
![Alt text](https://www.mediafire.com/convkey/2a9a/g6b862afqplsrp06g.jpg)


<h3>required modules :</h3>

sudo apt-get install libgtk-3-dev <br>
sudo apt-get install python3-tzlocal<br>
sudo pip3 install pyroute2<br>
sudo pip3 install python-dateutil<br>
sudo pip3 install pyusb<br>
sudo pip3 install evdev<br>

<h3>installation :</h3>
create "time-attendence" folder in /home/pi<br>
clone whole repository<br>
<h4>launch:</h4>
cd time-attendence<br>
sudo python3 timeatt.py
<h4>tips:</h4>
- disable automatic showing options when removable media are insered<br>
- disable monitor in stop timeout<br>
- autorun app on startup:<br>
  <p>  sudo nano ~/.config/lxsession/LXDE-pi/autostart</p>
  <p>  add: "@lxterminal -e /home/pi/time-attendence/start.sh" and save</p>
  <p>  sudo chmod +x /home/pi/time-attendence/start.sh</p>
