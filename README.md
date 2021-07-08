# mca66

## A quick overview:
mca66.py is the main library that knows how to talk to the MCA66 controller. It has a MCA66Command factory class. You basically ask it for a command and it will return a command that can be executed over a serial connection.

Example:
```
zone_id = 1
power = True
command = MCA66Command.set_power(zone_id, power)
port = "/dev/ttyUSB0"
ser = serial.Serial(port, 38400, timeout=2)
result = command.execute(ser)
ser.close()
print result.json_data()
```

## Files
App.py is a simple Flask app that provides a REST API to control the different zones. I run this app on port 8080 using supervisord.
audio.html and audio.js Provide a web interface that will use the REST API to control the speakers. There are some hard coded values in there that works for my server but isn't generally applicable.

## How to Run
```
sudo docker rm soundcontrol
sudo docker build . -t mca66
sudo docker run -d --restart=always -p 80:8080 --device=/dev/ttyUSB0 --name soundcontrol mca66 
```

### How to Develop
```
sudo docker build . -t mca66
sudo docker run -p 80:8080 -v $(pwd):/usr/src/app -v $(pwd)/static:/usr/src/app/static --rm --device=/dev/ttyUSB0 --name soundcontrol-dev mca66
```
