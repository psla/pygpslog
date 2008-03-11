# SIS_VERSION="0.1.8"
# SYMBIAN_UID=0xA0005B76

import sys, os, traceback
import appuifw, e32

e32._stdo(u"C:\\pygpslog.err.txt")

try:   import      envy
except:envy =      None


localpath = str(os.path.split(appuifw.app.full_name())[0])
sys.path  = [localpath] + sys.path

class MyStdout(object):
  def __init__(self):
    stdio.color = 0
  def write(self, text):
    stdio.add(unicode(text))
  def flush(self):
    pass
  def close(self):
    pass
    
class MyStderr(MyStdout):
  def write(self, text):
    c = stdio.color
    stdio.color = 0xf00000
    MyStdout.write(self, text)
    stdio.color = c
  
lck = e32.Ao_lock()

def close():
  lck.signal()

appuifw.app.body = stdio = appuifw.Text()
appuifw.app.exit_key_handler = close

sys.stdout = MyStdout()
sys.stderr = MyStderr()

if envy != None:
  try:    envy.set_app_system(True)
  except: pass

try:
  import gpslog
  gpslog.GpsLog().run(True)
except:
  traceback.print_exc()

appuifw.app.body = stdio;
appuifw.app.exit_key_handler = close

if stdio.get() == u'':
  close()
else:
  appuifw.app.menu = [ (u'Exit', close) ]

lck.wait()
appuifw.app.exit_key_handler = None
appuifw.app.set_exit()

if envy != None:
  try:    envy.set_app_system(False)
  except: pass
