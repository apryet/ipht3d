import wx
import wx.lib.colourselect as csel
import wx.grid as wgrid
from wx.lib import plot
import  wx.lib.scrolledpanel as scrolled
from pylab import savetxt
from os import sep
from scipy import *
from time import sleep

# classe permettant de definir une fonction recuperant les valeurs des TxtCtrl
class GeneralDialog(wx.Dialog):

    def __init__(self, parent, title, mysize):
        wx.Dialog.__init__(self, parent, -1, title, size = mysize)
        self.listCtrl = [];self.parent = parent
        self.traduit = parent.traduit;self.tradinverse = parent.tradinverse

    def GetValues(self): #renvoie un tuple avec nouvelles valeurs
        l1 = self.listCtrl; listResult = []
        for i in range(len(l1)):
            if type(self.listIn[i][1])==type(['a','b']):
                sel = str(self.tradinverse(str(l1[i].GetStringSelection())))
                tupl=(self.listIn[i][0],[sel,self.listIn[i][1][1]])
                listResult.append(tupl)
            else :
                val0=l1[i].GetValue();
                typIn=type(self.listIn[i][1]); messg=0;#print 'mydlg',val0,typIn
                if typIn==type(5):
                    try: val=int(val0)
                    except ValueError: messg=1
                elif typIn==type(5.):
                    try: val=float(val0)
                    except ValueError: messg=1
                else: val = val0
                if messg==1:
                    self.parent.OnMessage('erreur de type');return self.listIn
                listResult.append((self.listIn[i][0],val))
        return listResult

    def GetListTrue(self):
        lstResult = []
        for i in range(len(self.listCtrl)):
            if self.listCtrl[i][0].GetValue()==True:
                lstResult.append(self.listCtrl[i][1])
        return lstResult

class MyGenericCtrl(GeneralDialog):

    def __init__(self, parent, title, listIn):
        self.listIn = listIn
        size=(250,min(500,(len(listIn)+2)*22+40))
        a=str(title).split('(');ti1=parent.traduit(a[0].strip());
        if len(a)>1: ti1=ti1+' ('+a[1]
        GeneralDialog.__init__(self, parent, ti1, size)
        dlgSizer = wx.BoxSizer(wx.VERTICAL)        
        p=MyGenericPanel(self,size,listIn,self.listCtrl)
        dlgSizer.Add(p,0)
        dlgSizer.AddSpacer((0,0), -1)
        buttonSizer = self.CreateButtonSizer( wx.OK | wx.CANCEL ) 
        dlgSizer.Add(buttonSizer, 0, wx.ALIGN_CENTER|wx.ALIGN_BOTTOM)
        self.SetSizer(dlgSizer)

class MyGenericPanel(scrolled.ScrolledPanel):
    def __init__(self,parent,size,listIn,listCtrl):
        size=(235,min(440,(len(listIn)+2)*22-20))
        scrolled.ScrolledPanel.__init__(self,parent,-1,size=size)
        self.listCtrl,self.coul=listCtrl,None;sizeTextCtrl = (60,20)
        ContentSizer = wx.GridSizer(len(listIn),2,vgap = 6, hgap = 10)
        for i in range(len(listIn)):
            a=str(listIn[i][0]);b=a.split('(');ti1=parent.traduit(b[0].strip());
            if len(b)>1: ti1= ti1+' ('+b[1]
            text = wx.StaticText(self, -1,ti1, style = wx.ALIGN_CENTER)
            ContentSizer.Add(text, 0, wx.ALIGN_CENTER)
            if type(listIn[i][1])==type(['a','b']):
                chlist=[parent.traduit(n) for n in listIn[i][1][1] ]
                ch = parent.traduit(listIn[i][1][0])
                cho=wx.Choice(self, -1, choices=chlist)
                self.listCtrl.append(cho)
                ContentSizer.Add(self.listCtrl[i], 0, wx.ALIGN_CENTER)
                self.listCtrl[i].SetSelection(chlist.index(ch))
            elif type(listIn[i][1])==type(False):
                chk = wx.CheckBox(self, -1, '')
                self.listCtrl.append(chk)
                self.listCtrl[i].SetValue(listIn[i][1])
                ContentSizer.Add(self.listCtrl[i], 0, wx.ALIGN_CENTER)
            elif type(listIn[i][1])==type(wx.Color()):
                butC=csel.ColourSelect(self,-1,label='color',colour=listIn[i][1])
                self.listCtrl.append(butC)
                ContentSizer.Add(self.listCtrl[i], 0, wx.ALIGN_CENTER)
                csel.EVT_COLOURSELECT(butC, butC.GetId(), self.OnSelectColour)
            else:
                ctr = wx.TextCtrl(self,-1,str(listIn[i][1]),size = sizeTextCtrl)
                self.listCtrl.append(ctr)
                ContentSizer.Add(self.listCtrl[i], 0, wx.ALIGN_CENTER)
        self.SetSizer(ContentSizer)
        self.SetAutoLayout(1)
        self.SetupScrolling()
    def OnSelectColour(self, event): self.coul=event.GetValue()
    
class MyListDialog(GeneralDialog):
    """ a dialog to get a list of values"""
    def __init__(self, parent, title, listIn):
        lg=max(len(listIn),5)*16;lg=min(lg,500);size1=(240,lg+80);
        self.listIn=listIn
        GeneralDialog.__init__(self, parent, title, size1)
        self.parent = parent
        size2 = (180,lg)
        dlgSizer = wx.BoxSizer(wx.VERTICAL)
        list2=""
        for n in listIn: list2 = list2+str(n)+"\n"
        if list2=="":list2="\n \n \n"
        self.txt = wx.TextCtrl(self,-1,list2,size=size2,style=wx.TE_MULTILINE)
        dlgSizer.Add(self.txt,0);dlgSizer.AddSpacer((0,5), 0)
        buttonSizer = self.CreateButtonSizer( wx.OK | wx.CANCEL ) 
        dlgSizer.Add(buttonSizer, 0, wx.ALIGN_CENTER|wx.ALIGN_BOTTOM)
        self.SetSizer(dlgSizer)

    def GetStrings(self):
        lst = self.txt.GetValue().split("\n");
        n1=lst.count('');n2=lst.count(' ')
        if len(lst)==n1+n2:
            self.parent.OnMessage('pas de valeurs');return None
        for i in range(n1):lst.remove('')
        for i in range(n2):lst.remove(' ')
        return [str(a) for a in lst]
    
    def GetValues(self):
        lst=self.GetStrings()
        return [float(a) for a in lst]
    
class MyTextDialog(GeneralDialog):
    """ a dialog to get a list of values"""
    def __init__(self, parent, title, header,txtIn=''):
        size=(340,400);
        self.txtIn=txtIn;self.parent = parent
        GeneralDialog.__init__(self, parent, title, size)
        dlgSizer = wx.BoxSizer(wx.VERTICAL)
        hd=wx.StaticText(self,-1,header, style = wx.ALIGN_CENTER)
        dlgSizer.Add(hd,0);dlgSizer.AddSpacer((0,5), 0)
        size2=(300,320);
        self.txt = wx.TextCtrl(self,-1,txtIn,size=size2,style=wx.TE_MULTILINE)
        dlgSizer.Add(self.txt,0);dlgSizer.AddSpacer((0,5), 0)
        buttonSizer = self.CreateButtonSizer( wx.OK | wx.CANCEL ) 
        dlgSizer.Add(buttonSizer, 0, wx.ALIGN_CENTER|wx.ALIGN_BOTTOM)
        self.SetSizer(dlgSizer)
        
    def GetTextAsList(self):
        lst = self.txt.GetValue().split("\n");
        return lst
    def GetText(self):
        return self.txt.GetValue()
    
class MyArrayDialog(GeneralDialog):

    def __init__(self, parent, title, arr1, rTitre, cTitre):
        size=(max((len(cTitre)+1)*60+5,170),(len(rTitre)+3)*25+20)
        GeneralDialog.__init__(self, parent, title, size)
        self.parent = parent
        [nRow,nCol] = shape(arr1);self.listCtrl.append([nRow,nCol])
        dlgSizer = wx.BoxSizer(wx.VERTICAL)
        sizeTextCtrl = (40,20)
        grdSizer = wx.GridSizer(nRow+1,nCol+1,vgap = 5,hgap = 5)
        txt = wx.StaticText(self, -1,' ',size=(55,20));grdSizer.Add(txt, 0)
        for j in range(nCol): #titre des colonnes
            txt = wx.StaticText(self, -1, cTitre[j],size=(55,20))
            grdSizer.Add(txt, 0)
        for i in range(nRow):
            txt = wx.StaticText(self, -1, rTitre[i])
            grdSizer.Add(txt, 0, wx.TE_RIGHT)
            for j in range(nCol): # contenu de l'array
                textCtrl = wx.TextCtrl(self, -1, str(arr1[i,j]), style = wx.TE_RIGHT|wx.ALIGN_TOP, size = sizeTextCtrl)
                self.listCtrl.append(textCtrl)
                grdSizer.Add(textCtrl, 0, wx.ALIGN_CENTER)
        dlgSizer.Add(grdSizer,0);dlgSizer.AddSpacer((0,5), 0)
        buttonSizer = self.CreateButtonSizer( wx.OK | wx.CANCEL ) 
        dlgSizer.Add(buttonSizer, 0, wx.ALIGN_CENTER|wx.ALIGN_BOTTOM)
        self.SetSizer(dlgSizer)
        
    def GetArrayValues(self):
        [nRow,nCol] = self.listCtrl[0];arr2 = zeros((nRow,nCol))+0.;
        n=1
        for i in range(nRow):
            for j in range(nCol):
                arr2[i,j] = float(self.listCtrl[n].GetValue());n+=1
        return arr2

class MyGriVarDialog(wx.Dialog):
    def __init__(self,parent,title,dic):
        self.parent,self.dicIn=parent,dic
        wx.Dialog.__init__(self,parent,-1,title,size=(300,200))
        sizer= wx.BoxSizer(wx.VERTICAL|wx.EXPAND)
        siz1= wx.BoxSizer(wx.HORIZONTAL|wx.EXPAND)
        tit=dic.keys();self.but=[]
        for i in range(len(tit)):
            self.but.append(wx.Button(self,-1,parent.traduit(tit[i]),name=tit[i]))
            siz1.Add(self.but[i]);sizer.AddSpacer((0,10),0)
            wx.EVT_BUTTON(self.but[i],self.but[i].GetId(),self.OnListUser)
        sizer.Add(siz1,0)
        buttonSizer = self.CreateButtonSizer( wx.OK | wx.CANCEL) 
        sizer.Add(buttonSizer, 0,wx.ALIGN_BOTTOM)
        self.SetSizer(sizer)

    def GetValues(self):
        return self.dicIn
        
    def OnListUser(self,evt):
        """ ouvre un dialogue pour rentrer plusieurs valeurs et les renvoie"""
        item = self.FindWindowById(evt.GetId());n = item.GetName()
        lst1=self.dicIn[n]
        dialg = MyListDialog(self.parent,"",lst1)
        if dialg.ShowModal() == wx.ID_OK:
            self.dicIn[n]=dialg.GetStrings();#print 'lstuser',self.listuser
        return

class MyNoteBook(wx.Dialog):    
    def __init__(self,parent,title,dic):
        self.gui=parent.gui
        wx.Dialog.__init__(self,parent,-1,title,size=(550,500))
        self.pages,self.dicIn ={},dic
        sizer= wx.GridSizer(2,1)
        self.SetSizer(sizer)
        siz1=wx.BoxSizer(wx.VERTICAL)
        nb=wx.Notebook(self,-1,size=(450,400))
        for n in dic.keys():
            if len(dic[n]['rows'])==0 and n!='Species': continue
            if len(dic[n]['cols'])>0: pg=MyNBpanelGrid(parent.gui,nb,dic[n])
            else : pg=MyNBlist(parent.gui,nb,dic[n])
            self.pages[n]=pg;nb.AddPage(pg,n)
        siz1.Add(nb);sizer.Add(siz1)
        buttonSizer = self.CreateButtonSizer( wx.OK | wx.CANCEL) 
        sizer.Add(buttonSizer,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM);
        
    def OnCancel(self): pass #return None  
    def OnOK(self): pass # return 'OK'
    
    def GetValues(self):
        dic=self.dicIn.copy();#print dic
        for n in self.pages.keys():
            dic[n]=self.pages[n].GetValues()
        return dic
    
class MyNBlist(wx.Panel):
    def __init__(self,gui,parent,dic):
        wx.Panel.__init__(self,parent,-1, size=(400,300))
        self.dic=dic;lg=len(dic['rows']);listIn=dic['rows']
        dlgSizer = wx.BoxSizer(wx.VERTICAL)
        list2=""
        for n in listIn: list2 = list2+str(n)+"\n"
        #if list2=="":list2="\n \n \n"
        self.txt = wx.TextCtrl(self,-1,list2,style=wx.TE_MULTILINE)
        dlgSizer.Add(self.txt,0)
        self.SetSizer(dlgSizer)
        
    def GetValues(self) :
        txt=self.txt.GetValue().strip().split('\n')
        self.dic['rows']=[n.strip() for n in txt]
        self.dic['data']=[]
        for i in range(len(txt)):
            self.dic['data'].append(['True',0.])
        return self.dic
        
class MyNBpanelGrid(wgrid.Grid):
    def __init__(self,gui,parent,dic):
        self.traduit,self.tradinverse=gui.traduit,gui.tradinverse
        wgrid.Grid.__init__(self,parent,-1)
        rowString,colString,data=dic['rows'],dic['cols'],dic['data']
        ln=[len(i) for i in rowString]
        self.SetRowLabelSize(max(ln)*8);self.chkTrue=[]
        for c in range(len(colString)):
            #sleep(0.01)
            #print dic['rows'][0],c,type(data[0][c])
            if type(data[0][c])==type(True):
                self.chkTrue.append(True)
##                attr = wgrid.GridCellAttr()
##                attr.SetEditor(wgrid.GridCellBoolEditor())
##                attr.SetRenderer(wgrid.GridCellBoolRenderer())
##                self.SetColAttr(c,attr)
            else:
                self.chkTrue.append(False)
        self.table=CustTable(rowString,colString,data)
        self.SetTable(self.table,True)
        self.AutoSizeColumns(True)
        #self.Bind(wgrid.EVT_GRID_CELL_LEFT_CLICK,self.onMouseLeft)
        #self.Bind(wgrid.EVT_GRID_SELECT_CELL,self.onCellSelected)
        #self.Bind(wgrid.EVT_GRID_EDITOR_SHOWN, self.onEditorCreated)
        #self.EnableCellEditControl
        
    def GetValues(self) : return self.table.GetValues()
    #below : code to have direct check of checkboxes
    def onMouseLeft(self,evt):
        if self.chkTrue[evt.Col]:
            cb = self.GetCellValue(evt.Row,evt.Col)
            sleep(0.1)
            self.SetCellValue(evt.Row,evt.Col,str(1-int(cb)))
        evt.Skip()
       
class CustTable(wgrid.PyGridTableBase):
    def __init__(self,rowString,colString,data):
        wgrid.PyGridTableBase.__init__(self)
        self.rows,self.cols= rowString,colString
        nrow,ncol,self.colType=len(rowString),len(colString),[bool]
        self.colLabels=colString;self.rowLabels=rowString;
        self.dataTypes=[]
        self.data = data*1
        for c in range(ncol):
            if type(data[0][c])==type(True):
                self.dataTypes.append(wgrid.GRID_VALUE_BOOL)
            else:
                self.dataTypes.append(wgrid.GRID_VALUE_STRING)
                
    def GetNumberRows(self): return len(self.data)
    def GetNumberCols(self): return len(self.data[0])
    def GetColLabelValue(self,col):return self.colLabels[col]
    def GetRowLabelValue(self,row):return self.rowLabels[row]
    def GetTypeName(self,row,col): return self.dataTypes[col]
    def IsEmptyCell(self,row,col):
        try : return not self.data[row][col]
        except IndexError : return True
    def GetValue(self,row,col):
        try : return self.data[row][col]*1
        except IndexError : return ''
    def GetValueAsBool(self,row,col): return bool(self.data[row][col])
    def SetValue(self,row,col,value):self.data[row][col]= value
    def SetValueAsBool(self,row,col,value):self.data[row][col]= bool(value)
       
    def GetValues(self):
        dic={};dic['rows'],dic['cols']=self.rows,self.cols
        nrow,ncol,data=len(self.rows),len(self.cols),[]
        for ir in range(nrow):
            data.append([])
            for ic in range(ncol):
                val=self.GetValue(ir,ic)
                if self.dataTypes[ic]==wgrid.GRID_VALUE_BOOL: val=bool(val)
                data[ir].append(val)    
        dic['data']=data;
        return dic

# Dialogue sur les periodes
# renvoie le nombre de periodes et la duree des periodes
class TransitoireDialog(wx.Frame):
    ID_BPLOT = 300
    ID_CHOIX = 301
    ID_OKESPECE = 302
    ID_BOK = 303
    ID_CANCEL = 304

    def __init__(self,parent,title,especes,periods,Cinj):
        self.parent, self.especes,self.click = parent, especes,0
        nper = len(periods)
        tmax = max(periods)
        #Cmax = max(Cinj)
        self.periods, self.Cinj = periods, Cinj;
        wx.Frame.__init__(self,parent,-1, title,wx.DefaultPosition,size=(300,300))
        self.SetBackgroundColour('#EDFAFF')
        self.Limit = []
        # partie du haut avec boutons
        titre1 = wx.StaticText(self, -1, "Nombre de periodes",style=wx.RIGHT)
        self.Limit.append(wx.TextCtrl(self,-1,str(nper),style=wx.TE_RIGHT,size=(40,20)))        
        titre2 = wx.StaticText(self, -1, "Temps final")
        self.Limit.append(wx.TextCtrl(self,-1,str(tmax),style=wx.TE_RIGHT,size=(40,20)))        
        titre3 = wx.StaticText(self, -1, "Conc. maximale",style=wx.RIGHT)
        self.Limit.append(wx.TextCtrl(self,-1,str(1.),style=wx.TE_RIGHT,size=(40,20)))        
        # choix de l'espece
        titre4 = wx.StaticText(self, -1, "espece",style=wx.RIGHT)
        self.choix = wx.Choice(self, self.ID_CHOIX, choices = self.especes)
        self.choix.SetSelection(0)
        buttSizer2 = wx.GridSizer(4,2,hgap=10,vgap=5)
        buttSizer2.AddMany([(titre1,0,wx.RIGHT),(self.Limit[0],0),(titre2,0),
                (self.Limit[1],0),(titre3,0),(self.Limit[2],0),(titre4,0),
                (self.choix,0)])        
        # fin de la zone d'input
        but = wx.Button(self,self.ID_BPLOT,"Change period")
        buttSizer1 = wx.BoxSizer(wx.HORIZONTAL)
        buttSizer1.Add(buttSizer2,0)
        buttSizer1.Add(but,0,wx.ALIGN_CENTER_VERTICAL|wx.LEFT)
        # canvas pour faire le graphe
        self.cnv = plot.PlotCanvas(self);self.cnv.SetSizeWH(400,300)
        #boutons du bas
        basSizer = wx.BoxSizer(wx.HORIZONTAL)
        butOK = wx.Button(self,self.ID_BOK,"Fermer")
        butEspece = wx.Button(self,self.ID_OKESPECE,"OK_espece")
        butCancel = wx.Button(self, self.ID_CANCEL, "Cancel")
        basSizer.AddMany([(butOK, 0),(butEspece, 0),(butCancel,0)])
        #assembler le tout
        frameSizer = wx.BoxSizer(wx.VERTICAL)
        frameSizer.Add(buttSizer1, 0)
        frameSizer.AddSpacer((0,10),0)
        frameSizer.Add(self.cnv, 0)
        frameSizer.Add(basSizer, 0, wx.ALIGN_BOTTOM|wx.ALIGN_CENTER)

        wx.EVT_BUTTON(self, self.ID_BPLOT, self.OnModif)
        wx.EVT_CHOICE(self, self.ID_CHOIX, self.OnPlotE)
        wx.EVT_BUTTON(self, self.ID_OKESPECE, self.OnEspece)
        wx.EVT_BUTTON(self, self.ID_BOK, self.OnClose)
        wx.EVT_BUTTON(self, self.ID_CANCEL, self.OnCancel)
        self.cnv.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
        self.cnv.Bind(wx.EVT_MOTION, self.OnMove)
        self.cnv.Bind(wx.EVT_LEFT_UP, self.OnRelease)

        frameSizer.SetSizeHints(self)
        self.SetSizer(frameSizer)
        self.plot(0);self.choix.SetSelection(0)
    
    def OnModif(self,evt):
        self.plot(-1)  # remettre plot a zero
        
    def OnPlotE(self,evt):
        self.plot(self.choix.GetSelection())
        
    def plot(self, esp):
        nper = float(self.Limit[0].GetValue())
        tmax = float(self.Limit[1].GetValue())
        Cmax = float(self.Limit[2].GetValue())
        if esp>=0: # dessin a partir de Cinj, evt num espece
            per = array(self.periods)
            conc = self.Cinj[:,esp]
            dt, Cmax = per[0], max(float(max(conc)),Cmax)
            if len(per)>1: dt = per[1]-per[0]
            t2 = self.periods-dt/2.
        else : # dessin a partir de modifier plot
            self.choix.SetSelection(0)
            self.Cinj = ones((nper,len(self.especes)))*1.
            dt = tmax/nper; t2 = arange(dt/2.,tmax,dt)+0.;self.periods = t2+dt/2.
            conc = t2*0.+Cmax/2.
        # crer les lignes de l'histogramme
        self.lignes = []
        for i in range(len(t2)):
            t3 = [t2[i]-dt/2.,t2[i]-dt/2.,t2[i]+dt/2.,t2[i]+dt/2.]
            c3 = [0.,conc[i],conc[i],0.]
            dataL = transpose(array([t3,c3]))
            self.lignes.append(plot.PolyLine(dataL))
        # creer les points
        self.data = transpose(array([t2,conc]))
        self.poly = plot.PolyMarker(self.data, marker='circle', colour='red')
        lli = self.lignes*1;lli.append(self.poly)
        drawObj = plot.PlotGraphics(lli, "source", "temps", "concentration")
        self.cnv.Draw(drawObj, xAxis= (0,tmax),yAxis= (0,Cmax*1.1))
        self.Cmax=Cmax

    def OnClick(self, evt):
        """quaund on clique sur le diagramme on selectionne le numero du point
        qui est le plus proche"""
        self.click = 1
        x,y = self.cnv.GetXY(evt)
        retour = self.cnv.GetClosetPoint([x,y],pointScaled=False)
        self.indxPt = retour[2]

    def OnMove(self,evt):
        """ lors du mouvement de la souris apres avoir clique le point selectionne
        est deplace verticalement"""
        if self.click ==0 : return
        x,y = self.cnv.GetXY(evt)
        self.poly.points[self.indxPt,1] = max(0.,y) # on ne change que le y
        self.lignes[self.indxPt].points[1:3,1] = max(0.,y) # pour les lignes aussi
        self.cnv.Redraw()

    def OnRelease(self,event):
        """ quand on relache le bouton de la souris, on arrete le onmove et on
        renvoie l'indice du point et sa coord y"""
        self.click = 0

    def OnEspece(self,evt):
        """quand on clicke, on conserve les conc pour l'espece donnee dans choix"""
        iesp = int(self.choix.GetSelection());
        dec = int(round(log10(self.Cmax)))
        self.Cinj[:,iesp]=around(self.poly.points[:,1],decimals=dec)

    def OnClose(self,evt):
        t = self.poly.points[:,0];t = t+t[0]  # temps
        self.parent.setTransit(self.especes,t,self.Cinj)
        self.Destroy()

    def OnCancel(self,evt):
        self.Destroy()

#//////////////////////////////////////////////////////////////////////
class MyDialogContour(GeneralDialog):
    ID_COLOR1 = 307
    ID_COLOR2 = 308
    ID_COLOR3 = 309

    def __init__(self, parent, title, valeur, col):
        """ liste contient les attributs actuels des contours : val : [0]min, 1:max,
        2: intervalles, [3]decimales, 4:log, 5:user puis couleurs et transparence"""
        self.listCtrl = [];self.valeur = valeur;
        size=(150,10*35+50)
        GeneralDialog.__init__(self, parent, title, size)
        sizeTextCtrl = (40,20)        
        dlgSizer = wx.BoxSizer(wx.VERTICAL)        
        Sizer1 = wx.GridSizer(5,2,vgap=10,hgap=10)
        # boite pour calcul automatique
        Sizer1.Add(wx.StaticText(self, -1, 'Automatique'), 0, wx.ALIGN_CENTER)
        self.auto = wx.CheckBox(self, -1, '');self.auto.SetValue(True)
        if valeur!=None:
            self.auto.SetValue(valeur[4]=='auto')
            self.listuser=valeur[5]
        Sizer1.Add(self.auto, 0, wx.ALIGN_CENTER)
        # intervalles
        label = ['Mini', 'Maxi', 'intervalle','decimales']
        if col==None : col=[(0,0,255),(0,255,0),(255,0,0),10]
        self.coul = [wx.Color(col[0][0],col[0][1],col[0][2]),
                     wx.Color(col[1][0],col[1][1],col[1][2]),
                     wx.Color(col[2][0],col[2][1],col[2][2]),col[3]]
        if valeur==None: valeur=[0.,10.,1.,2,False,False]
        for i in range(4):
            text = wx.StaticText(self, -1, label[i], style = wx.ALIGN_LEFT)
            self.listCtrl.append(wx.TextCtrl(self, -1, str(valeur[i]), style = wx.TE_RIGHT, size = sizeTextCtrl))
            Sizer1.Add(text, 0, wx.ALIGN_CENTER)
            Sizer1.Add(self.listCtrl[i], 0, wx.ALIGN_CENTER)
            
        Sizer1.Add(wx.StaticText(self, -1, 'log'), 0, wx.ALIGN_CENTER)
        self.log = wx.CheckBox(self, -1, '')
        self.log.SetValue(valeur[4]=='log')
        Sizer1.Add(self.log, 0, wx.ALIGN_CENTER)
        self.butlist = wx.Button(self,-1,'listes valeurs')
        Sizer1.Add(self.butlist,0)
        self.user = wx.CheckBox(self, -1, '')
        self.user.SetValue(valeur[4]=='fix')
        Sizer1.Add(self.user, 0, wx.ALIGN_CENTER)
        # dialogue couleurs
        Sizer3 = wx.GridSizer(3,2,vgap=10,hgap=10)
        but0=csel.ColourSelect(self,-1,label='color',colour=col[0],size=sizeTextCtrl)
        but1=csel.ColourSelect(self,-1,label='color',colour=col[1],size=sizeTextCtrl)
        but2=csel.ColourSelect(self,-1,label='color',colour=col[2],size=sizeTextCtrl)
        Sizer3.Add(wx.StaticText(self, -1,'Couleur 1'),0,wx.ALIGN_CENTER)
        Sizer3.Add(but0,0)
        Sizer3.Add(wx.StaticText(self, -1,'Couleur 2'),0,wx.ALIGN_CENTER)
        Sizer3.Add(but1,0)
        Sizer3.Add(wx.StaticText(self, -1,'Couleur 3'),0,wx.ALIGN_CENTER)
        Sizer3.Add(but2,0)
        Sizer3.Add(wx.StaticText(self, -1,'Opacite '),0,wx.ALIGN_CENTER)
        self.transp=wx.TextCtrl(self, -1, str(col[3]), size = sizeTextCtrl)
        Sizer3.Add(self.transp,0)
        
        wx.EVT_BUTTON(self.butlist,self.butlist.GetId(),self.OnListUser)
        csel.EVT_COLOURSELECT(but0, but0.GetId(), self.OnSelectColour0)
        csel.EVT_COLOURSELECT(but1, but1.GetId(), self.OnSelectColour1)
        csel.EVT_COLOURSELECT(but2, but2.GetId(), self.OnSelectColour2)

        dlgSizer.Add(Sizer1, 0, wx.ALIGN_CENTER|wx.EXPAND)
        dlgSizer.Add(wx.StaticLine(self, -1), 0, wx.ALIGN_CENTER|wx.EXPAND)
        dlgSizer.Add(Sizer3, 0, wx.ALIGN_CENTER|wx.EXPAND)
        dlgSizer.AddSpacer((0,0), -1)
        buttonSizer = self.CreateButtonSizer( wx.OK | wx.CANCEL ) 
        dlgSizer.Add(buttonSizer, 0, wx.ALIGN_CENTER|wx.ALIGN_BOTTOM)
        self.SetSizer(dlgSizer);self.valeur=valeur

    def GetStrings(self):
        """renvoie les valeurs des boites et ajoute la liste user a la fin """
        v=self.valeur
        if v==None: v=[0.,10.,1.,2,'auto',None]
        for i in range(4):
            v[i]=self.listCtrl[i].GetValue()
            try: float(v[i])
            except ValueError:
                self.parent.OnMessage('erreur de type');return self.valeur
        v[4]='lin'
        if self.user.GetValue():
            v[4]='fix';v[5]=self.listuser
        if self.log.GetValue(): v[4]='log'
        if self.auto.GetValue(): v[4]='auto'
        self.coul[3]=self.transp.GetValue();
        return v
    
    def OnListUser(self,event):
        """ ouvre un dialogue pour rentrer plusieurs valeurs et les renvoie"""
        if self.user.GetValue()==False: return
        lst1 =[]
        if self.valeur!=None:
            if type(self.valeur[5])==type([5]): lst1=self.valeur[5]
        dialg = MyListDialog(self.parent,"",lst1)
        if dialg.ShowModal() == wx.ID_OK:
            self.listuser=dialg.GetValues();#print 'lstuser',self.listuser
        else : return
        return
        
    def OnSelectColour0(self, event): self.coul[0]=event.GetValue()
    def OnSelectColour1(self, event): self.coul[1]=event.GetValue()
    def OnSelectColour2(self, event): self.coul[2]=event.GetValue()

#----------------------------------------------------
class plotxy(wx.Frame):
    ID_AXES = 306
    ID_EXPORT = 308
    
    def __init__(self,parent,id,title="plot",pos=wx.DefaultPosition):
        self.gui = parent
        self.toglX= 0; self.toglY = 0
        wx.Frame.__init__(self,parent, id, title,pos=wx.DefaultPosition,size=(350,450))
        self.SetBackgroundColour('#EDFAFF');self.CenterOnScreen()
        hautSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.butAxes = wx.Button(self, self.ID_AXES, label = "Axes")
        self.butExport = wx.Button(self,self.ID_EXPORT, label = "Export")
        self.cnv = plot.PlotCanvas(self);
        self.cnv.SetInitialSize(size=(300, 400))
        hautSizer.AddMany([(self.butAxes,0),(self.butExport,0)])
        plotSizer = wx.BoxSizer(wx.VERTICAL)
        plotSizer.AddMany([(hautSizer,0),(self.cnv,0,wx.EXPAND)])
        #plotSizer.SetSizeHints(self)
        self.SetSizer(plotSizer)
        
        wx.EVT_BUTTON(self, self.ID_AXES, self.OnAxes)    
        wx.EVT_MENU(self, wx.ID_EXIT, self.OnExit)
        wx.EVT_BUTTON(self, self.ID_EXPORT, self.OnExport)
        
    def draw(self,x,arry,legd,title,Xtitle,Ytitle,typ='-',axes=None):
        x,arry=transpose(array(x,ndmin=2)),array(arry) # x en vertical
        self.x, self.arry, self.legd, self.title = x, arry, legd, title
        self.Xtitle,self.Ytitle,self.typ = Xtitle, Ytitle,typ
        self.xlog, self.ylog = False, False
        self.lignes = [];cols=['red','blue','green','orange','cyan','black']*5
        # verifier dimensions des vecteurs entree
        if len(shape(x))==1:
            x1 = ones((len(x),1))+0.;
        if len(shape(arry))==1:
            arry1 = ones((len(arry),1))+0.; arry1[:,0]=arry; arry=arry1*1.;ny=1
        else :
            [nt,ny] = shape(arry)
        if axes!=None: a,b,self.xlog,c,d,self.ylog = axes
        x2 = x*1.; arry2 = arry*1.;
        if self.xlog:
            x2[x2<=0.]=1e-7;x2 = log10(x)
        if self.ylog:
            arry2[arry2<=0.]=1e-7;arry2 = log10(arry)
        # creer les lignes
        if ny==1:
            dataL = concatenate([x2,arry2],axis=1)
            if typ=='-': gobj = plot.PolyLine(dataL,colour='red')
            else : gobj = plot.PolyMarker(dataL,colour='red')
            self.lignes.append(gobj)
        else :
            #print 'mydlg',ny,cols,legd
            for i in range(ny):
                dataL = concatenate([x2,arry2[:,i:i+1]],axis=1)
                if typ=='-': gobj = plot.PolyLine(dataL,colour=cols[i],legend=legd[i])
                else : gobj = plot.PolyMarker(dataL,colour=cols[i],legend=legd[i])
                self.lignes.append(gobj)
        drawObj = plot.PlotGraphics(self.lignes,title,Xtitle,Ytitle)
        # limite des axes
        if axes==None or self.xlog:
            xmn = amin(amin(x2)); xmx = amax(amax(x2));
            dmx = xmx-xmn; self.xmx=xmx+dmx/20.; self.xmn=xmn-dmx/20.
        else :
            self.xmn,self.xmx,a,b,c,d = axes
        if axes==None: # or self.ylog:
            ymn = amin(amin(arry2));ymx = amax(amax(arry2));#print 'dlg',ymn,ymx
            dmy = ymx-ymn; self.ymx=ymx+dmy/20.; self.ymn=ymn-dmy/20. 
        else :
            a,b,c,self.ymn,self.ymx,d = axes
        if self.ymn==self.ymx:
            self.ymn=self.ymn*.99;self.ymx=self.ymx*1.01
        #self.ymn = max(self.ymn,0.);self.xmn = max(self.xmn,0.)
        self.cnv.SetEnableLegend(True);self.cnv.SetEnableGrid(True)
        self.cnv.Draw(drawObj,xAxis=(float(self.xmn),float(self.xmx)),
            yAxis=(float(self.ymn),float(self.ymx)))
        
    def OnAxes(self,evt):
        lst = [('X_min',self.xmn),('X_max',self.xmx),('X_log',self.xlog),
               ('Y_min',self.ymn),('Y_max',self.ymx),('Y_log',self.ylog)]
        dlg = MyGenericCtrl(self.gui,'Axes',lst)
        if dlg.ShowModal() == wx.ID_OK:
            axes = zip(*dlg.GetValues())[1];
        else : return
        self.draw(self.x,self.arry,self.legd,self.title,self.Xtitle,
                self.Ytitle,typ=self.typ,axes=axes)

    def OnExport(self,evt):
        arr = self.lignes[0].points[:,:1]
        for i in range(len(self.lignes)):
            arr=c_[arr,self.lignes[i].points[:,1:2]]
        pPath,pName = self.gui.model.getProject();
        fname=pPath+sep+pName+self.title+'.txt'
        dlg = wx.FileDialog(self.gui,"Sauvegarder","",fname,"*.txt",wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:            
            fname = dlg.GetDirectory()+sep+dlg.GetFilename()
            f1 = open(fname,'w')
            f1.write(self.Xtitle)
            for n in self.legd: f1.write(' '+n)
            f1.write('\n')
            savetxt(f1,arr)
            f1.close()
    def OnExit(self,evt):
        print 'bye' #marche pas

#-----------------------------------------------------------
class MyGrid(GeneralDialog):
    ID_OK = 286
    ID_CANCEL =287
    
    def __init__(self,parent, title,rowString,colString,data,nrow=2):
        """data array"""
        self.parent=parent
        if data!=None :
            [nrow,ncol] = shape(data)
        else :
            ncol = len(colString);nrow=len(rowString)
        size=((ncol+1)*100,(nrow+1)*30+120)
        GeneralDialog.__init__(self, parent, title, size)
        dlgSizer = wx.BoxSizer(wx.VERTICAL)
        #fabriaction de la grille elle meme
        self.grid = wgrid.Grid(self,-1,size=((ncol+1)*90,(nrow+1)*30))
        self.grid.CreateGrid(nrow,ncol)
        #self.grid.SetColSize(0,50);self.grid.SetMargins(20,20)
        for i in range(ncol): self.grid.SetColLabelValue(i,colString[i])
        if len(rowString)>1:
            for i in range(nrow): self.grid.SetRowLabelValue(i,rowString[i])
        if data!=None:
            for col in range(ncol):
                for row in range(nrow):
                    self.grid.SetCellValue(row,col,str(data[row,col]))
        self.grid.AutoSize()
        dlgSizer.Add(self.grid,0,wx.EXPAND)
        dlgSizer.AddSpacer((0,10),-1)

        buttonSizer = self.CreateButtonSizer( wx.OK | wx.CANCEL ) 
        dlgSizer.Add(buttonSizer, 0, wx.ALIGN_CENTER|wx.ALIGN_BOTTOM)
        self.SetSizer(dlgSizer)
