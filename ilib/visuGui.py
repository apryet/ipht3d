import wx
import MyDialogs
from scipy import *
from calcAquifere import zone2index

class visuGui(wx.Panel):
    ID_SWITCH = 199
    def __init__(self,parent,model):

        self.gui = parent
        self.visu, self.model = parent.Visu, model
        self.OnMessage = parent.OnMessage
        self.traduit = self.gui.traduit
        self.tradinverse = self.gui.tradinverse
        self.langue  = self.gui.LANG
        wx.Panel.__init__(self,self.gui,-1,size=(-1,400))
        self.panelSizer = wx.BoxSizer(wx.VERTICAL)
        self.icones = parent.icones
        #self.SetBackgroundColour('#EDFAFF')
        self.groupes={
            'Aquifere':[0,['Plan',['X','Y','Z']],['Couche',['___']],['Tstep',['_____']],
                        'Grille','Carte','ZoneImg'],
            'Ecoulement':[1,'Charge','Vitesse','Particules'],
            'Data':[2,'Visible'],
            'Transport':[3,'Traceur'],
            'PHT3D':[4,['Especes',['_______']],
                     ['Units',['mol/L','mmol/L','umol/L','nmol/L']],
                     ['User',['_______']]],
            'Observation':[5,['Type',['Profile','Breakthrough','XYplot']],
                           ['Zone',['_______']]]}
        self.change={'Grille':[['Couleur',wx.Color(0,0,0)]],
            'Vitesse':[['Couleur',wx.Color(0,0,0)],['Echelle',1.]],
            'Particules':[['Couleur',wx.Color(0,0,0)],['temps',10.]],
            'Visible':[['Couleur',wx.Color(0,0,0)],['Taille',10]]}
        self.curGroupe, self.curNom,self.curItemps,self.curPlan,self.curOri = '', '',0,0,'Z'
        self.curTypO,self.curPlot='Profile',None
        self.listNameVisu=['Charge','Vitesse','Traceur','Especes','User']; # names that can be visualised
        self.creerBox()
        #self.panelSizer.SetSizeHints(self)
        self.SetSizer(self.panelSizer)
        
    def creerBox(self):
        self.numCtrl = 200;self.swiImg='cont';
        grdSizer = wx.FlexGridSizer(1,3,vgap=3,hgap=3)
        self.icOri=wx.BitmapButton(self,-1,self.icones['Vis_OriZ'],size=(60,25))
        self.icSwiImg=wx.BitmapButton(self,self.ID_SWITCH,self.icones['Vis_SwiCont'],size=(25,25))
        grdSizer.Add(self.icOri,0);grdSizer.Add(self.icSwiImg,0)
        self.panelSizer.Add(grdSizer,0)
        self.dictBox={}
        for ig in range(len(self.groupes)): 
            for g0 in self.groupes: #pour ordonner
                if self.groupes[g0][0]==ig: g=g0
            self.dictBox[g] = Boite(self,g)
            self.panelSizer.Add(self.dictBox[g],0) #,wx.EXPAND)
            self.panelSizer.AddSpacer((0, 5), 0)
        wx.EVT_BUTTON(self,self.ID_SWITCH,self.switchImg)

    def changeIcOri(self,ori):
        if ori=='Z':self.icOri.SetBitmapLabel(self.icones['Vis_OriZ'])
        if ori=='X':self.icOri.SetBitmapLabel(self.icones['Vis_OriX'])
        if ori=='Y':self.icOri.SetBitmapLabel(self.icones['Vis_OriY'])

    def switchImg(self,evt):
        if self.swiImg=='cont':
            self.icSwiImg.SetBitmapLabel(self.icones['Vis_SwiImg'])
            self.swiImg='img'
        else :
            self.icSwiImg.SetBitmapLabel(self.icones['Vis_SwiCont'])
            self.swiImg='cont'

    def resetVisu(self):
        for n in ['Aquifere_Couche','Aquifere_Tstep','PHT3D_Especes','PHT3D_User','Observation_Zone']:
            self.FindWindowByName(n+'_L').Clear()
        for n in ['Grille','Carte','ZoneImg']: self.FindWindowByName('Aquifere_'+n+'_B').SetValue(False)
        for n in ['Charge','Vitesse','Particules']: self.FindWindowByName('Ecoulement_'+n+'_B').SetValue(False)

    def resetGlist(self,event):
        """permet de remettre tout Glist a 0 qd pbs"""
        self.model.resetGlist()
    def OnClick(self,evt):
        """action qd on clicke une boite. tag L : liste """
        item = self.FindWindowById(evt.GetId());n = item.GetName(); #getName ou getLabelText
        [groupe,nom,tag]=n.split('_');
        self.curGroupe,self.curNom=groupe,nom
        if tag=='L': retour = item.GetStringSelection()
        else: retour = evt.Checked() # cas ou c'est un checkbox (defaut)
        self.OnClick2(groupe,nom,tag,retour)
        
    def OnClick2(self,groupe,nom,tag,retour):
        """suite de dessus, nom titre de la boite, retour nom de
        la variable ds boite"""
        obj=True;
        if groupe==('Data'):
            self.visu.setDataOn(retour);return
        if groupe==('Observation'):
            if nom=='Type': self.curTypO=retour
            else:
                self.curZoneO=retour;self.onObservation()
            return
        if nom=='Plan':
            self.curOri=retour;typObj='Couche';obj=False
            self.changeIcOri(retour)
            grd=self.model.Aquifere.getFullGrid()
            nbZ=self.model.Aquifere.getNbCouches()
            if retour=='Z': self.setNames('Aquifere_Couche_L',range(nbZ))
            if retour=='X': self.setNames('Aquifere_Couche_L',range(grd['nx']))
            if retour=='Y': self.setNames('Aquifere_Couche_L',range(grd['ny']))
        elif nom=='Couche':
            self.curPlan=int(retour);typObj='Couche';obj=False
        elif nom=='Tstep':
            self.curItemps=self.getIndexInList('Aquifere_Tstep_L')
            typObj='Couche';obj=False
        elif nom=='Grille': typObj='Grille'
        elif nom in ['Carte','ZoneImg']:typObj='Image'
        elif nom=='Particules':
            typObj='Particules';self.curPlot=nom
        elif nom=='Vitesse':
            typObj='Vecteur';self.curPlot=nom
        else :
            if self.swiImg=='cont': typObj='Contour'
            else : typObj='Image'
            if retour==True: self.curPlot=nom
            else : self.curPlot=retour
        # print 'visuGui',plt
        # mettre a false les boites qui ne sont plus utilisees
        if (nom=='Carte') and tag: self.onTickBox('Aquifere','ZoneImg','B',False)
        if (nom=='ZoneImg') and tag: self.onTickBox('Aquifere','Carte','B',False)
        if (typObj=='Contour') and (nom!='Charge'):self.onTickBox('Ecoulement','Charge','B',False)
        if (typObj=='Contour') and (nom!='Traceur'):self.onTickBox('Transport','Traceur','B',False)
        if (typObj=='Contour') and (nom!='Especes'):self.setListPos0('PHT3D_Especes_L')
        if obj and retour!=False:
            obj = self.model.getObject(groupe,nom,retour,self.curItemps,self.curPlan,self.curOri);
        self.visu.showObject(obj,str(typObj),str(groupe),str(nom),retour,self.curItemps,self.curPlan,self.curOri) 
        
    def OnChange(self,evt):
        """ change les caracteristiques d'un affichage"""
        item = self.FindWindowById(evt.GetId());n = item.GetName(); #getName ou getLabelText
        [groupe,nom,tag]=n.split('_')
        item2=self.FindWindowByName(groupe+'_'+nom+'_L');
        if item2!=None: nom=item2.GetStringSelection()
        col = self.model.getGlistParm(groupe,nom,'col');
        valeur = self.model.getGlistParm(groupe,nom,'valeur')
        if nom in self.change.keys(): # cas autres que contours
            if col==None: col = self.change[nom][0][1]
            if valeur==None and len(self.change[nom])>1:
                valeur = self.change[nom][1][1]
            lst0=self.change[nom];lst0[0][1]=col
            if nom in ['Vitesse','Particules']: lst0[1][1]=valeur
            dlg = MyDialogs.MyGenericCtrl(self,nom,lst0)
            if dlg.ShowModal() == wx.ID_OK:
                lst1 = zip(*dlg.GetValues())[1];col=lst1[0];
                if len(lst1)>1: valeur=lst1[1]
            else : return
        else: # cas contour
            dlgContour = MyDialogs.MyDialogContour(self.gui, "Contours",valeur,col)
            if dlgContour.ShowModal() == wx.ID_OK:
                valeur = dlgContour.GetStrings()
                # creer le vecteur de couleurs
                c = dlgContour.coul;
                col=[(c[0].Red(),c[0].Green(),c[0].Blue()),(c[1].Red(),c[1].Green(),c[1].Blue()),
                     (c[2].Red(),c[2].Green(),c[2].Blue()),int(c[3])]
            else : return
        self.model.setGlistParm(groupe,nom,'valeur',valeur)
        self.model.setGlistParm(groupe,nom,'col',col);
        self.onTickBox(groupe,nom,tag,True)
        self.visu.changeObject(groupe,nom,valeur,col)
        
    def onObservation(self):
        group=self.visu.curGroupe
        if group not in ['Ecoulement','Transport','PHT3D']: return
        typ=self.curTypO[0]  # B or P
        t=self.curItemps;
        if group=='PHT3D': lesp=self.getNames('PHT3D_Especes_L');
        elif group=='Ecoulement': lesp=['Charge','Flux']
        else : lesp=['Transport']
        lst0=zip(lesp,[False]*len(lesp))
        #dialog to choose species to graph
        if len(lesp)>1: 
            dlg = MyDialogs.MyGenericCtrl(self,'species',lst0)
            if dlg.ShowModal() == wx.ID_OK: 
                lst1=dlg.GetValues();lesp=[]
                for i in range(len(lst1)):
                    if lst1[i][1]:lesp.append(lst1[i][0])
            else :return
        # dialog for type of graph, for flow tis dialog is useless
        lst0=['Valeur','Valeur ponderee','Flux'];
        if group!='Ecoulement': 
            dlg = MyDialogs.MyGenericCtrl(self,'type',[('Choisir :',['Valeur',lst0])])
            if dlg.ShowModal() == wx.ID_OK: #dialog to choose type of graph
                val=dlg.GetValues()[0][1][0];
                typ+=str(lst0.index(val));
            else :return
        dist,val,lab=self.model.onPtObs(typ,t,group,self.curZoneO,lesp)
        plt = MyDialogs.plotxy(self.gui,-1);plt.Show(True)
        znam=self.curZoneO
        if typ[0]=='X': plt.draw(dist,val,lab[1:],znam,lab[0],"val",typ='+');
        else : plt.draw(dist,val,lab[1:],znam,lab[0],"val");
        plt.Raise()
        
    def boxVisible(self,nomBox,bool):
        if nomBox in self.dictBox.keys():
            box=self.dictBox[nomBox];
            box.Show(bool);box.Enable(bool);
            box.Layout();self.panelSizer.Layout()
    def boutonVisible(self,nomBut,bool):
        item = self.FindWindowByName(nomBut);item.Enable(bool)
    def OnSetItem(self,groupe,nom,tag,bool):
        """to set an item in a specific state from outside"""
        item=self.FindWindowByName(groupe+'_'+nom+'_'+tag);
        if tag=='B':
            item.SetValue(bool)
            self.OnClick2(groupe,nom,tag,bool)

    def onTickBox(self,groupe,nom,tag,bool):
        """ pour mettre a jour un bouton sans faire l'action corresp"""
        item=self.FindWindowByName(groupe+'_'+nom+'_'+tag);
        if tag=='B': item.SetValue(bool)
            
    def getNames(self,nomBoite):
        item = self.FindWindowByName(nomBoite);
        return item.GetItems()
    def setNames(self,nomBoite,noms):
        item = self.FindWindowByName(nomBoite);item.Clear();
        if nomBoite[:3]=='PHT':item.Append(' ')
        for n in noms: item.Append(str(n))

    def getIndexInList(self,nomBoite):
        item = self.FindWindowByName(nomBoite);#print item.GetString()
        return item.GetCurrentSelection()
    def setListPos0(self,nomBoite):
        item = self.FindWindowByName(nomBoite);
        item.SetSelection(0);

class Boite(wx.Panel):
    def __init__(self,parent,gr):
        wx.Panel.__init__(self,parent,-1,size=(-1,400))
        bxSizer=wx.StaticBoxSizer(wx.StaticBox(self, -1, parent.traduit(gr)), wx.VERTICAL)
        Ctrl = parent.groupes[gr][1:]
        grdSizer = wx.FlexGridSizer(len(Ctrl),3,vgap=3,hgap=3)
        for n in Ctrl:
            if type(n)==type([1,2]): #cas liste -> choix
                nom = gr+'_'+n[0]+'_L';
                text = wx.StaticText(self, -1, parent.traduit(n[0]))
                grdSizer.Add(text,0)
                liste = n[1]
                choix = wx.Choice(self, parent.numCtrl, choices=liste, name=nom)
                grdSizer.Add(choix, 0)
                wx.EVT_CHOICE(self, parent.numCtrl, parent.OnClick)        
            else : # cas simple : checkbox
                nom = gr+'_'+n+'_B';
                text = wx.StaticText(self, -1, parent.traduit(n))
                grdSizer.Add(text, 0)
                chk = wx.CheckBox(self, parent.numCtrl, "",name=nom)
                grdSizer.Add(chk, 0)
                wx.EVT_CHECKBOX(self, parent.numCtrl, parent.OnClick)
            but = wx.Button(self, parent.numCtrl+1,"C",name=nom[:-2]+'_C',size=(16,16))
            grdSizer.Add(but, 0,wx.ALIGN_LEFT)
            wx.EVT_BUTTON(self, parent.numCtrl+1, parent.OnChange)
            if n in ['Carte','ZoneImg','Visible','Type','Zone']:but.Enable(False)
            if n[0] in ['Plan','Couche','Tstep','Units']:but.Enable(False)
            parent.numCtrl += 2
        bxSizer.Add(grdSizer, 0, wx.ALIGN_CENTER)
        self.SetSizer(bxSizer)
     
