# time-attendence

time-attendence is a Gui application for Raspberry Pi to stamp the RFID cards.
Works with every usb RFID card reader (working like a keyboard). 10 digits.
<h4>Features:</h4>
- create/edit users with own tag card and unique ID number<br>
- authorized manager can enter to the menu system<br>
- IN or OUT validation system<br>
- esport data logs by usb download or rest API <a href="https://github.com/85mattia/time-attendence/wiki">Wiki</a><br>
- view all users Logs or single user Logs<br>
- touch friendly interface:<br>
<img src="https://www.mediafire.com/convkey/2a9a/g6b862afqplsrp06g.jpg" width="50%" height="50%">
<img src="https://www.mediafire.com/convkey/2a51/a8ofd1es247d5gj6g.jpg" width="50%" height="50%">
<img src="https://www.mediafire.com/convkey/493d/9w1hcqx5l5ctfbo6g.jpg" width="50%" height="50%">
<img src="https://www.mediafire.com/convkey/6fcf/2pwhnv3laq16d1r6g.jpg" width="50%" height="50%">
<img src="https://www.mediafire.com/convkey/ec3a/e68p0f7knywlotw6g.jpg" width="50%" height="50%">

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
- raccomanded usb reader : <a href="https://www.ebay.it/itm/KKmoon-RFID-125KHz-portatili-vicinanza-stand-by-EM-scheda-ID-USB-Reader-Win8-OTG/292577195665?hash=item441ef5b691:g:3gMAAOSw1ZpbBwTn">125 khz Usb Reader</a><br>
- raccomanded touchscreen Raspberry display : <a href="https://www.ebay.it/itm/1080P-60fps-3-5-pollici-Display-LCD-HDMI-per-Raspberry-Pi-Custodia-in-acrilico/142739327725?_trkparms=aid%3D111001%26algo%3DREC.SEED%26ao%3D1%26asc%3D20160908105057%26meid%3De7e3b0f577dd44498701d1780b96afa4%26pid%3D100675%26rk%3D2%26rkt%3D15%26sd%3D183125235903%26itm%3D142739327725&_trksid=p2481888.c100675.m4236&_trkparms=pageci%3Acb1cc01a-6af9-11e8-9177-74dbd180bc86%7Cparentrq%3Ade9c405d1630a9c0abeed2befff6395c%7Ciid%3A1">3.5inch display</a><br>
