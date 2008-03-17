import sys
# Merge the functionalities of positioning, locationrequestor and Bluetooth

DefaultProvider  = None

provider = []

hasPositioning = hasLocationRequestor = False

if sys.platform.startswith("symbian"):
  try:
    from gpslib.gpspos import PositioningProvider
    hasPositioning = True
    provider = [ PositioningProvider ] + provider
  except:
    pass
  
  
  try:
    from gpsloc import LocationRequestorProvider #@UnresolvedImport
    hasLocationRequestor = True
    provider = [ LocationRequestorProvider ] + provider
  except:
    pass
  
# for testing purposes common (simulation on non-Symbian OS):
try:
  from gpslib.gpsnmea import NMEABluetoothProvider
  provider = [ NMEABluetoothProvider ] + provider
except:
  pass

try:
  from gpssirf import SiRFBluetoothProvider #@UnusedImport
  provider = provider + [ SiRFBluetoothProvider ]
  # no default constructor, needs port
except:
  pass


    
if not sys.platform.startswith("symbian"):
  try:
    if not sys.platform.startswith("symbian"):
      from gpsnmea import NMEASerialProvider #@UnusedImport
      provider = [ NMEASerialProvider ] + provider
  except:
    pass

  try:
    from gpssirf import SiRFSerialProvider    #@UnusedImport
    provider = provider + [ SiRFSerialProvider ]
  except:
    pass

# common
try:
  from gpsnmea import NMEAGPSDProvider #@UnusedImport
  # no default constructor, needs address
except:
  pass


def new(*args, **kwargs):
  print provider[0].__name__
  return provider[0](*args, **kwargs)

def defaultProvider():
  return provider[0]
  
