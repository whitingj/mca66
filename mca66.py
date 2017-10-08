import serial
import time
import collections
import json
import copy

class ByteUtils:

  """ helper class to create byte arrays """
  @staticmethod
  def ba2hex(a):
    """ converts a byte array to hex """
    return ":".join("%0.2x" % x for x in a)

  @staticmethod
  def s2hex(s):
    """ converts a string to hex values """
    return ":".join(x.encode('hex') for x in s)

  @staticmethod
  def diff(s1, s2, name1, name2):
    h1 = ByteUtils.s2hex(s1)
    h2 = ByteUtils.s2hex(s2)
    print "1 ("+name1+") "
    print h1
    print "2 ("+name2+") "
    print h2
    d = ""
    a1 = h1.split(":")
    a2 = h2.split(":")
    for i in range(0, len(a1)):
      if len(d) > 0:
        d += ":"
      if a1[i] != a2[i]:
        try:
          #d += ByteUtils.b2h(ByteUtils.h2b(a1[i]) - ByteUtils.h2b(a2[i]))
          d += a1[i]
        except:
          print a1, a2
      else:
        d += "--"
    print "d "
    print d

  @staticmethod
  def h2b(v):
    """ hex to byte """
    return int(v, 16)

  @staticmethod
  def b2h(v):
    """ byte to hex """
    return "%0.2x" % v

  @staticmethod
  def to_byte_array(hex_tuple):
    """ converts an array of hex string to a byte array """
    command = bytearray([0 for number in xrange(len(hex_tuple))])
    index = 0
    for h in hex_tuple:
      command[index] = ByteUtils.h2b(h)
      index += 1
    return ByteUtils._checksum(command)

  @staticmethod
  def _checksum(command):
    """ calculates the checksum """
    checksum = 0
    for char in command:
      checksum += char
    command[len(command)-1] = checksum
    return command

class ZoneState(object):
  def __init__(self, bindata):
    data = []
    for i in bindata:
      data.append(ord(i))
    if data[0] != 0x02:
      raise Exception("bad data input: header "+str(data[0])+" "+ByteUtils.s2hex(data))
    if data[1] != 0x00:
      raise "bad data input: reserved"
    self.zone = data[2]
    self.command = data[3]
    self.state = collections.OrderedDict()
    if data[3] == 5:
      #Data1 - general state
      self.state["power"]      = True if data[4] & 0b10000000 else False
      self.state["mute"]        = True if data[4] & 0b01000000 else False
      self.state["mode"]        = "attributes" if data[4] & 0b00100000 else "volume"
      #self.state["power2"]      = True if data[4] & 0b00010000 else False
      self.state["party"]       = True if data[4] & 0b00001000 else False
      self.state["party_input"] = data[4] & 0b00000111

      #Data2 - keypad led indicator
      self.state["mode_led"] = data[5] & 0b01111111

      #Data3 - inputs?
      #self.state["led_input"] = data[6] & 0b00111111
      #self.state["power3"] = True if data[6] & 0b10000000 else False
      #self.state["input1"] = True if data[6] & 0b00100000 else False
      #self.state["input2"] = True if data[6] & 0b00010000 else False
      #self.state["input3"] = True if data[6] & 0b00001000 else False
      #self.state["input4"] = True if data[6] & 0b00000100 else False
      #self.state["input5"] = True if data[6] & 0b00000010 else False
      #self.state["input6"] = True if data[6] & 0b00000001 else False

      #Data4 - reserved

      #Data5 - input port
      self.state["input"] = data[8] + 1

      #Data6 - volume (range 195-255; 0 == max)
      volume = data[9]
      if volume == 0:
        volume = 256
      volume = int((volume - 195.0) / 61.0 * 100.0)
      self.state["volume"] = volume

      #Data7 - treble
      self.state["treble"] = data[10]

      #Data8 - bass
      self.state["bass"] = data[11]

      #Data9 - balance
      self.state["balance"] = data[12]

    #checksum
    self.state["checksum"] = data[13]

  def clone_state(self):
    return copy.copy(self.state)

  def pretty(self):
    #return "zone: "+str(self.zone)+"\n"+json.dumps(self.state, indent=2, separators=(',', ': '))
    return "zone: "+str(self.zone)+" "+json.dumps(self.state)

class MCA66Result(object):
  def __init__(self, zone_states):
    self.data = {}
    for z in zone_states:
      if z.zone != 0:
        self.data[z.zone] = z.clone_state()
        self.data[z.zone]['zone'] = z.zone

  def json(self):
    return json.dumps(self.data)

  def json_data(self):
    return self.data

class MCA66Command(object):
  def __init__(self, command_hex, rx_bytes, name, wait_time = 0):
    self.command = ByteUtils.to_byte_array(command_hex)
    self.rx_bytes = rx_bytes
    self.result = None
    self.name = name
    self.zone_states = []
    self.wait_time = wait_time

  def execute(self, ser):
    """ execute the command and returns the result """
    ser.write(self.command)
    self.result = ser.read(self.rx_bytes)
    self._parse()
    if self.wait_time > 0:
      time.sleep(self.wait_time)
    return MCA66Result(self.zone_states)

  def _parse(self):
    #breakup the result into chunks of 14 characters and create a ZoneState for each one
    i = 0
    while (i+14 <= len(self.result)):
      self.zone_states.append(ZoneState(self.result[i:i+14]))
      i += 14

  def debug(self):
    print "Command: %s (tx_bytes %d)" % (self.name, self.rx_bytes)
    print(ByteUtils.ba2hex(self.command))
    if self.result:
      print "result: (len: "+str(len(self.result))+") "+str(ByteUtils.s2hex(self.result))+" "+str(self.result)
    for i in self.zone_states:
      print i.pretty()
    print

  def diff(self, label, command):
    """ prints out the difference between the 2 command results """
    print "diff> "+label
    ByteUtils.diff(self.result, command.result, self.name, command.name)
    print

  @staticmethod
  def get_model():
    command = (
      "02", #head
      "00", #reserved
      "00", #zone
      "08", #command
      "00", #data
      "00", #checksum
      )
    return MCA66Command(command, 13, "model")

  @staticmethod
  def get_zone_state():
    command = (
      "02", #head
      "00", #reserved
      "00", #zone
      "06", #command
      "00", #data
      "00", #checksum
      )
    return MCA66Command(command, 98, "state")

  @staticmethod
  def set_power(zone, power):
    if power:
      data = "20"
    else:
      data = "21"
    command = (
      "02", #head
      "00", #reserved
      ByteUtils.b2h(zone), #zone
      "04", #command
      data, #data
      "00", #checksum
      )
    sleep_time = 0.25
    if power:
      sleep_time = 2

    return MCA66Command(command, 28, "z"+str(zone)+" power "+str(power), sleep_time)

  @staticmethod
  def vol_up(zone):
    command = (
      "02", #head
      "00", #reserved
      ByteUtils.b2h(zone), #zone
      "04", #command
      "09", #data
      "00", #checksum
      )
    return MCA66Command(command, 28, "z"+str(zone)+" vol_up")

  @staticmethod
  def vol_down(zone):
    command = (
      "02", #head
      "00", #reserved
      ByteUtils.b2h(zone), #zone
      "04", #command
      "0a", #data
      "00", #checksum
      )
    return MCA66Command(command, 28, "z"+str(zone)+" vol_down")

  @staticmethod
  def mute(zone):
    command = (
      "02", #head
      "00", #reserved
      ByteUtils.b2h(zone), #zone
      "04", #command
      "22", #data
      "00", #checksum
      )
    return MCA66Command(command, 28, "z"+str(zone)+" vol_down")

  @staticmethod
  def set_input(zone, input_num):
    """ sets the zone's input to to the input number.  input number is 1 based """
    input_num = int(input_num)
    command = (
      "02", #head
      "00", #reserved
      ByteUtils.b2h(zone), #zone
      "04", #command
      ByteUtils.b2h(input_num+2), #data, input 1 is 0x03, 2 is 0x04
      "00", #checksum
      )
    return MCA66Command(command, 28, "z"+str(zone)+" input"+str(input_num))

if __name__ == '__main__':
    # this was run as a main script

  state = []
  def track_state(ser, label):
    s1 = command = MCA66Command.get_zone_state(5);
    data = command.execute(ser)
    state.append(s1)
    s1.name += " "+label
    s1.debug()


  port = "/dev/ttyUSB0"
  ser = serial.Serial(port, 38400, timeout=2)

  track_state(ser, "init")

  c1 = command = MCA66Command.set_power(3, True);
  data = command.execute(ser)
  #command.debug()

  time.sleep(3)
  #===============================================

  track_state(ser, "after on")

  c2 = command = MCA66Command.set_input(3, 2);
  data = command.execute(ser)
  command.debug()

  time.sleep(2)
  #===============================================

  track_state(ser, "after input 2")

  c2 = command = MCA66Command.set_input(3, 3);
  data = command.execute(ser)
  command.debug()

  time.sleep(2)
  #===============================================

  track_state(ser, "after input 3")

  c2 = command = MCA66Command.set_input(3, 4);
  data = command.execute(ser)
  #command.debug()

  time.sleep(2)
  #===============================================

  track_state(ser, "after input 4")

  c2 = command = MCA66Command.set_input(3, 1);
  data = command.execute(ser)
  command.debug()

  time.sleep(2)
  #===============================================

  track_state(ser, "after input 1")

  c2 = command = MCA66Command.vol_up(3);
  data = command.execute(ser)
  c2.debug()
  c2 = command = MCA66Command.vol_up(3);
  data = command.execute(ser)
  c2.debug()
  c2 = command = MCA66Command.vol_up(3);
  data = command.execute(ser)
  c2.debug()

  track_state(ser, "after volup 1")

  c2 = command = MCA66Command.vol_down(3);
  data = command.execute(ser)
  c2.debug()
  c2 = command = MCA66Command.vol_down(3);
  data = command.execute(ser)
  c2.debug()
  c2 = command = MCA66Command.vol_down(3);
  data = command.execute(ser)
  c2.debug()

  #command.debug()

  time.sleep(2)
  #===============================================

  track_state(ser, "after input vol")

  c4 = command = MCA66Command.mute(3);
  data = command.execute(ser)
  #command.debug()

  time.sleep(1)
  #===============================================

  track_state(ser, "after mute1")

  c4 = command = MCA66Command.mute(3);
  data = command.execute(ser)
  #command.debug()

  time.sleep(1)
  #===============================================

  track_state(ser, "after mute2")

  c4 = command = MCA66Command.set_power(3, False);
  data = command.execute(ser)
  #command.debug()

  time.sleep(1)
  #===============================================

  track_state(ser, "end")

  #for i in range(0, len(state) - 1):
  #  state[i].diff("s%d, s%d" % (i, i+1), state[i + 1])
  #state[0].diff("s%d, s%d" % (0, len(state) - 1), state[len(state) - 1])

  """
  s1 = command = MCA66Command.get_zone_state(3);
  data = command.execute(ser)

  c1 = command = MCA66Command.set_power(3, True);
  data = command.execute(ser)
  command.debug()

  time.sleep(3)

  s2 = command = MCA66Command.get_zone_state(3);
  data = command.execute(ser)

  c2 = command = MCA66Command.vol_up(3);
  data = command.execute(ser)
  command.debug()

  time.sleep(2)

  s3 = command = MCA66Command.get_zone_state(3);
  data = command.execute(ser)

  c3 = command = MCA66Command.vol_down(3);
  data = command.execute(ser)
  command.debug()

  time.sleep(2)

  s4 = command = MCA66Command.get_zone_state(3);
  data = command.execute(ser)

  c4 = command = MCA66Command.set_power(3, False);
  data = command.execute(ser)
  command.debug()

  time.sleep(1)

  s5 = command = MCA66Command.get_zone_state(3);
  data = command.execute(ser)

  s1.diff("s1, s2", s2)
  s2.diff("s2, s3", s3)
  s3.diff("s3, s4", s3)
  s4.diff("s4, s5", s5)
  s1.diff("s1, s5", s5)
  """

  """
  c2 = command = MCA66Command.get_zone_state(5);
  data = command.execute(ser)
  command.debug()

  c3 = command = MCA66Command.set_power(5, True);
  data = command.execute(ser)
  command.debug()

  c4 = command = MCA66Command.set_power(6, True);
  data = command.execute(ser)
  command.debug()

  time.sleep(2)

  c4_1 = command = MCA66Command.get_zone_state(5);
  data = command.execute(ser)
  command.debug()

  c5 = command = MCA66Command.set_power(5, False);
  data = command.execute(ser)
  command.debug()

  c6 = command = MCA66Command.set_power(6, False);
  data = command.execute(ser)
  command.debug()

  c7 = command = MCA66Command.get_zone_state(5);
  data = command.execute(ser)
  command.debug()


  c2.diff("turned on state", c4_1)
  c3.diff("zone 5", c5)
  c4.diff("zone 6", c6)
  c2.diff("final state", c7)
  """

  ser.close()
