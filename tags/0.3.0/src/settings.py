# settings.py
#
# Generic way to store settings in a PyS60 program.
# Author: Kari Kujansuu (kari.kujansuu@operamail.com)
#
# Usage example:
#
#     settings_fname = "my.settings"        # select a unique file name; settings are stored here
#                                           # This file will be in the same directory as the application
#
#     settings_desc = [                     # list of setting descriptors: (name,type,choices,default-value)
#        ("Name",    'text',   None, "")
#       ,("Gender",  'combo',  [u"Female",u"Male"], u"Male")
#       ,("Age",     'number', None,                0 )
#     ]
#     self.settings = Settings( settings_desc, settings_fname )
#
#     # later:
#     self.settings.execute_dialog()         # allows the user to edit settings
#     ...
#     name = self.settings.Name              # get a value
#

import os
import e32dbm
try: import appuifw; svc = False
except: svc = True

class Settings:
    def __init__(self,desc_list,fname):
        dl = []
        self.disp = {}
        for (nm,tp,ls,vl) in desc_list:
          if type(nm) in [tuple, list]:
            nm, dsp = nm
            self.disp[nm] = dsp
          dl += [(nm,tp,ls,vl)]
        desc_list = dl
        self.desc_list = desc_list
        for t in ["E:\\Python", "C:\\Python", "C:\\"]:
          testf = os.path.join(t, "PyEditor.Settings.Test")
          try:
            try:
              f = file(testf, "wb"); f.write("May I?\n"); f.close()
              this_dir = t
              break
            except: pass
          finally:
            if os.path.exists(testf): os.remove(testf)

        self.fname = os.path.join(this_dir,fname)
        for (name,tp,lst,value) in self.desc_list:
            if tp == 'text':
                exec "self." + name + " = unicode(value)"
            else:
                exec "self." + name + " = value"
        self.get_settings()

    def get_settings(self):
        db = e32dbm.open(self.fname,"c")
        for (name,tp,lst,value) in self.desc_list:
            if tp == 'text':
                if db.has_key(name): exec "self." + name + " = unicode(db[name])"
            if tp == 'number':
                if db.has_key(name): exec "self." + name + " = int(db[name])"
            if tp == 'combo':
                if db.has_key(name): exec "self." + name + " = db[name]"
        db.close()

    def execute_dialog(self, menu=None):
        if svc :
          raise SystemError, 'No dialogs in server processes'
        dlg = appuifw.Form(fields=[],flags=appuifw.FFormEditModeOnly | appuifw.FFormDoubleSpaced)
        saved_title = appuifw.app.title
        appuifw.app.title = u"Settings"
        
        if menu != None:
          dlg.menu = menu

        # build dialog fields
        n=0; forcechg = False
        for (name,tp,lst,defvalue) in self.desc_list:
          if name in self.disp:
            disp=self.disp[name]
          else:
            disp = name
          if tp == 'combo': 
            value = eval("self."+name)
            try: x = lst.index(value)
            except ValueError: x = lst.index(defvalue); forcechg = True
            dlg.insert(n,(unicode(disp),'combo', (lst,x) ))
          else:
            dlg.insert(n,(unicode(disp),tp,eval("self."+name)))
          n=n+1

        dlg.save_hook = self.save_hook
        self.settings_changed = False

        scr = appuifw.app.screen
        appuifw.app.screen = 'normal'
        
        dlg.execute()
        
        if forcechg:
          self.settings_changed = True

        appuifw.app.screen = scr

        appuifw.app.title = saved_title

        if self.settings_changed:
          self.save_settings(dlg)
    
    def save_settings(self, dlg=None):
        # retrieve values from dialog fields and save to dbm
        db = e32dbm.open(self.fname,"c")
        n = 0
        for (name,type,lst,value) in self.desc_list:
          if dlg:
            if type == 'text':
                exec "self." + name + " = dlg[n][2]"
            if type == 'number':
                exec "self." + name + " = int(dlg[n][2])"
            if type == 'combo':
                (lst,index) = dlg[n][2]
                exec "self." + name + " = lst[index]"
          db[name] = str(eval("self." + name))
          n = n+1
            
        db.reorganize()
        db.close()

    def save_hook(self,lst):
        self.settings_changed = True
        return True


