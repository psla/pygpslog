import sys, thread, socket, traceback

if not sys.platform.startswith("symbian"):
  import time
  sleep    =  time.sleep
else:
  import e32 #@UnresolvedImport
  sleep    = e32.ao_sleep

if not sys.platform.startswith("symbian"):
  class Sema(object):
    def __init__(self):
      self.lock = thread.allocate_lock()
      self.lock.acquire()
    def wait(self):
      self.lock.acquire()
    def signal(self):
      self.lock.release()
    def locked(self):
      return self.lock.locked()
else:
  class Sema(object):
    def __init__(self):
      self.__locked = False
      self.lock = e32.Ao_lock()
    def wait(self):
      self.__locked = True
      self.lock.wait()
    def signal(self):
      self.lock.signal()
      self.__locked = False
    def locked(self):
      return self.__locked # Though I'm not sur if this necessary...

class AbstractStreamProvider(object):
  "Abstract GPS Stream Reader Class"
  name  = __doc__
  Super = object
  
  def __init__(self):
    
    self.running = False
    self.stop    = False
    self.stream  = None
    self.exc     = None
    self.ok      = False
    self.sema    = Sema()
    
    self.tid     = thread.start_new_thread(self.__thread, ())
    
    self.sema.wait()

    if not self.ok:
      if self.exc != None:
        raise self.exc[0], None, self.exc[1]
      raise SystemError, "Thread failed to start"

  def __del__(self):
    if self.running:
      self.close()

  def read(self, n=0):
    if not self.stream:
      raise NotImplementedError
    else:
      return self.stream.read(n)
      
  def write(self, buf):
    if not self.stream:
      raise NotImplementedError
    else:
      return self.stream.write(buf)
  
  def close(self):
    if self.running:
      self.stop = True
      self.sema.wait()

  def reopen(self):
    raise NotImplementedError
    
  # All the threadInit() ... threadExit() stuff is for S60, where sockets, files, ...
  # cannot be used by any other thread
  def __thread(self, *_args, **_kwargs):
    if "--gps-debug" in sys.argv:
      sys.path.append(r"E:\Develop\Java\eclipse32\plugins\org.python.pydev.debug_1.3.8\pysrc")
      import pydevd #@UnresolvedImport
      pydevd.settrace(stdoutToServer=True, stderrToServer=True)
    
    try:
        
      self.threadInit()
      self.running = True
      self.ok      = True
      self.sema.signal()

      while not self.stop:
        if not self.process():
          break

    except Exception, exc:
      if not sys.platform.startswith("symbian"):
        traceback.print_exc()
      self.exc = (exc, sys.exc_traceback)

    self.ok  = False
    self.threadExit()
    if self.stream:
      self.stream.close()
      del self.stream
      self.stream  = None
    self.running = False
    if self.sema.locked():
      self.sema.signal()


  def threadInit(self):
    pass

  def threadExit(self):
    pass

  def process(self):
    raise NotImplementedError
  
  def dataAvailable(self):
    raise NotImplementedError


if not sys.platform.startswith("symbian") or e32.in_emulator():
  # simulate bluetooth socket by IP
  AF_DEFAULT  = socket.AF_INET
  AF_BT       = socket.AF_INET
  bt_discover = lambda: ("192.168.1.4", {"gpsd": 2947})
else:
  AF_DEFAULT  = socket.AF_BT #@UndefinedVariable
  AF_BT       = socket.AF_BT #@UndefinedVariable
  bt_discover = socket.bt_discover #@UndefinedVariable
  

class AbstractSocketProvider(AbstractStreamProvider):
  "Abstract GPS socket communication class"
  name  = __doc__
  Super = AbstractStreamProvider
  
  def __init__(self, addr, af=AF_DEFAULT):
    self.af      = af
    self.addr    = addr
    self.end     = False
    AbstractStreamProvider.__init__(self)

  def __del__(self):
    AbstractStreamProvider.__del__(self)

  def read(self, n=0):
    return self.stream.recv(n)

  def write(self, buf):
    return self.stream.send(buf)
  
  def reopen(self):
    self.stream.close()
    sleep(0.33)
    self.stream = socket.socket(self.af, socket.SOCK_STREAM)
    self.stream.connect(self.addr)
    sleep(0.33)
    
  def threadInit(self):
    self.stream = socket.socket(self.af, socket.SOCK_STREAM)
    self.stream.connect(self.addr)
    AbstractStreamProvider.threadInit(self)

GPSD_DEFAULT  = ('localhost', 2947)
GPSD_INIT_NMEA = "r1\r\n" #"r+\n"
GPSD_INIT_RAW  = "r2\r\n"

if not sys.platform.startswith("symbian") or e32.in_emulator():
  # simulate bluetooth socket by IP
  BT_INIT     = GPSD_INIT_RAW
else:
  BT_INIT     = None


class AbstractGPSDProvider(AbstractSocketProvider):
  "Abstract GPS using gpsd server"
  name  = __doc__
  Super = AbstractSocketProvider
  
  def __init__(self, addr=GPSD_DEFAULT, init=GPSD_INIT_NMEA):
    self.gpsdInit = init
    AbstractSocketProvider.__init__(self, addr, af=socket.AF_INET)

  def reopen(self):
    raise NotImplementedError
    
  def threadInit(self):
    AbstractSocketProvider.threadInit(self)
    if self.gpsdInit != None:
      self.write(self.gpsdInit)

class AbstractBluetoothProvider(AbstractSocketProvider):
  "Abstract GPS Bluetooth communication for Symbian S60"
  name  = __doc__
  Super = AbstractSocketProvider
  
  def __init__(self, addr=None):
    if addr == None:
      self.gps_addr,services=bt_discover()
      addr = (self.gps_addr,services.values()[0])
    AbstractSocketProvider.__init__(self, addr=addr, af=AF_BT)

  def threadInit(self):
    AbstractSocketProvider.threadInit(self)
    if BT_INIT:
      self.write(BT_INIT)
  
