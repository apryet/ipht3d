import wx
import MyDialogs
from pylab import loadtxt,savetxt
from scipy import *
from Pest import *

class Addins():
    def __init__(self,gui):
        self.gui=gui
        self.lastBatch=''
    def build(self):
        a1=self.gui.menuAddins.Append(801, "Batch")
        wx.EVT_MENU(self.gui, 801, self.BaDialog)
        a2=self.gui.menuAddins.Append(802, "write Pest Files")
        wx.EVT_MENU(self.gui, 802, self.Pest)        
        
    def BaDialog(self,evt):
        head='insert python commands below'
        dialg = MyDialogs.MyTextDialog(self.gui,'Batch program',head,self.lastBatch)
        retour = dialg.ShowModal()
        if retour == wx.ID_OK:
            txt = dialg.GetText() #dialg.GetTextAsList()
            self.lastBatch=txt
            txt1=txt.replace('model','self.gui.model')
            exec(txt1)
##             for t in lst:
##                 self.lastBatch+=t+'\n'
##                 t1=t.replace('model','self.gui.model')
##                 exec(t1)
        else : return
        dialg.Destroy()

    def Pest(self,evt):
        pest=Pest(self.gui.model)
        pest.readPst()
        pest.writeTpl()
        pest.writeBat()
        pest.getObsPt()
        pest.writeInst()
        pest.writePyscript()
        pest.writePst()