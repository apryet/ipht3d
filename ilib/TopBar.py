from Aquifere import Zone
from os import sep
import wx
import MyDialogs

class boites(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,-1,size=(-1,25))
        #self.SetBackgroundColour('#EDFAFF')
        self.aquifere = parent.model.Aquifere
        self.visu = parent.getVisu()
        self.gui,self.model = parent,parent.model
        self.traduit = parent.traduit;self.tradinverse=parent.tradinverse
        self.OnMessage = parent.OnMessage
        self.icones = parent.icones
        #self.troisD=1
        self.milist=self.model.getParm('Aquifere','Milieux')[1]

class zoneBox(boites):

    ID_POINT = Zone.POINT
    ID_LIGNE = Zone.LIGNE
    ID_RECT =  Zone.RECT  
    ID_POLY = Zone.POLY
    ID_POLYV = Zone.POLYV
    ID_INTERP = 25
    ID_TOGGLE = 26

    def __init__(self,parent):
        # icones pour choisir les zones
        boites.__init__(self,parent)
        zoneSizer = wx.BoxSizer(wx.HORIZONTAL)
        titre = wx.StaticText(self, -1, "Zones", style = wx.ALIGN_CENTER)
        zoneSizer.AddSpacer((10, 0), 0)
        zoneSizer.Add(titre, 0, wx.ALIGN_CENTER)
        zoneSizer.AddSpacer((10, 0), 0)

        but1 = wx.BitmapButton(self, self.ID_POINT, self.icones['Top_Point'],size=(25,24),name='POINT')
        but2 = wx.BitmapButton(self, self.ID_LIGNE, self.icones['Top_Ligne'],size=(25,24),name='LIGNE')
        but3 = wx.BitmapButton(self, self.ID_RECT, self.icones['Top_Rect'],size=(25,24),name='RECT')
        but4 = wx.BitmapButton(self, self.ID_POLY, self.icones['Top_Poly'],size=(25,24),name='POLY')
        but5 = wx.BitmapButton(self, self.ID_POLYV, self.icones['Top_PolyV'],size=(25,24),name='POLYV')        
        but7 = wx.BitmapButton(self, self.ID_INTERP, self.icones['Top_Interp'],size=(25,24))        

        but1.SetToolTipString(self.traduit('Ajout point'))
        but2.SetToolTipString(self.traduit('Ajout ligne'))
        but3.SetToolTipString(self.traduit('Ajout rectangle'))
        but4.SetToolTipString(self.traduit('Ajout polygone'))
        but5.SetToolTipString(self.traduit('Ajout polygone variable'))
        but7.SetToolTipString(self.traduit('Interpolation'))
        
        zoneSizer.AddMany([(but1,0),(but2,0),(but3,0),(but4,0),(but5,0)])
        zoneSizer.AddSpacer((10, 0), 0);#zoneSizer.Add(self.togBut,0)
        zoneSizer.AddSpacer((10, 0), 0);zoneSizer.Add(but7,0)
        zoneSizer.AddSpacer((10, 0), 0)
        zoneSizer.Add(wx.StaticLine(self, -1,style=wx.LI_VERTICAL), 0, wx.EXPAND)
        self.SetSizer(zoneSizer)
                
        wx.EVT_BUTTON(self, self.ID_POINT, self.OnForme)
        wx.EVT_BUTTON(self, self.ID_LIGNE, self.OnForme)
        wx.EVT_BUTTON(self, self.ID_RECT, self.OnForme)
        wx.EVT_BUTTON(self, self.ID_POLY, self.OnForme)
        wx.EVT_BUTTON(self, self.ID_POLYV, self.OnForme)
        wx.EVT_BUTTON(self, self.ID_INTERP, self.OnInterpol)

    def OnForme(self, evt):
        nomv = self.gui.parametresGui.getCurrentVar()
        item = self.FindWindowById(evt.GetId());forme = item.GetName()
        if nomv==None:
            self.OnMessage("choisissez une variable");return
        self.model.doAction('Top','zoneStart')
        exec('self.visu.setZoneReady(Zone.'+forme+',\"'+nomv+'\")')

    def OnInterpol(self,evt):
        lstDialg = self.model.getParm('Aquifere','Interpol')
        dialg = MyDialogs.MyGenericCtrl(self,'Interpoler',lstDialg)
        retour = dialg.ShowModal()
        if retour == wx.ID_OK:
            lst2 = dialg.GetValues()
            self.model.setParm('Aquifere','Interpol',lst2)
        dialg.Destroy()                


    #####################################################################
    #                            GESTION Zone

    def OnZoneCreate(self, typeZone, xy, listeVal):
        """ la zone a ete dessinnee dans la visu, on retourne les coordonnees
        ici on ouvre le dialogue pour les infos sur la zone et on modifie le
        modele
        """
        var = self.gui.parametresGui.getCurrentVar();
        units = self.aquifere.getUnits(var)
        nom_val='Valeur ('+units+')';v0=0.;maxmil=len(self.milist)
        if var=='PHT3D':
            dlist=[('Nom','z'),('Type',['B.Condition',['Initial','B.Condition','Transient']]),
                 ('Solution nb',1),('Phase nb',0),('Exchange nb',0),
                 ('Surface nb',0)]
        elif var in ['Potentiel','Transport']:
            dlist=[('Nom','z'),('Type',['B.Condition',['Initial','B.Condition','Transient']]),
                 (nom_val,v0)]
        elif var=='Observation': dlist=[('Nom','z')]
        else : dlist=[('Nom','z'),(nom_val,v0)]
        if self.aquifere.getDim()=='3D':
            dlist.extend([('Milieu Haut',0),('Milieu Bas',0)])
        dlgZoneInfo = MyDialogs.MyGenericCtrl(self,"Infos sur les zones",dlist)
        retour = dlgZoneInfo.ShowModal()

        if retour == wx.ID_OK:
            listVal = dlgZoneInfo.GetValues()
            nameZone = listVal[0][1];typz='B.Condition'
            if typeZone == 4:  # cas polyV
                if var in ['Potentiel','Transport']: listeVal.append(float(listVal[2][1]))
                else : listeVal.append(float(listVal[1][1]))
                valueZone = listeVal*1
            elif var in ['Potentiel','Transport']:
                valueZone = float(listVal[2][1])
                if listVal[1][1][0] in ['Initial','Transient']: typz='Initial' 
            elif var=='PHT3D':
                a=str(listVal[2][1])+str(listVal[3][1])+str(listVal[4][1])+str(listVal[5][1])
                valueZone=int(a) # 1210 : solu 1, min 2, exchan 1 surf 0
                if listVal[1][1][0] in ['Initial','Transient']: typz='Initial' # if inital put a negative value
            elif var=='Observation': valueZone =0
            else :
                valueZone = float(listVal[1][1])

            if self.aquifere.getDim()=='3D':
                mil = range(listVal[-2][1],listVal[-1][1]+1)
            else: mil=[0]
            # traiter nb milieu et zone source (index zon cree pour chaque layer)     
            info = [var,self.aquifere.getNbzone(var),mil,typz]
            # ajout de la (des) zone au model et du texte a la visu
            self.model.Aquifere.addZone(var,nameZone,valueZone,typeZone,info,xy)
            self.visu.addZone(mil,nameZone, valueZone,typeZone,info,xy)
            self.visu.redraw()
            # mise a jour du choix des zones pour la variable courante
            self.gui.modifBox.updateChoice2OnChange(var,mil)
            if var=='Observation':
                zlist=self.aquifere.getZoneList(var)
                znames=[z.getNom() for z in zlist]
                self.gui.afficheTree.setNames('Observation_Zone_L',znames)
            flag=True
        else:
            self.visu.deconnecte();self.visu.redraw()
            flag=False

        dlgZoneInfo.Destroy();self.model.doAction('Top','zoneEnd')
        return flag

#////////////////////////////////////////////////////////////////////////////

class modifBox(boites):
    ID_CHOIX = 26
    ID_VALEUR = 27
    ID_ZONEMIL = 28
    ID_HISTO = 29
    ID_MODIFZONE = 30
    ID_MOVEZONE = 31
    ID_COPY = 32
    ID_PASTE = 33
    ID_DELZONE = 34
    
    
    def __init__(self,parent):
        # icones pour choisir les zones
        boites.__init__(self,parent)
        modifSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.zmodif,self.zmove,self.zindex=0,0,[]
        self.copyXy,self.copyVal=[],0.
        self.currentZone = None;
        self.var = wx.StaticText(self, -1,"variable :",size=(60,20),style = wx.ALIGN_CENTER_VERTICAL)
        titre = wx.StaticText(self, -1,self.traduit("Modifier"), style = wx.ALIGN_CENTER)
        # choix de la zone
        self.choix = wx.Choice(self, self.ID_CHOIX, choices = [],size=(60,20))                
        
        modifSizer.AddSpacer((10, 0), 0)
        modifSizer.Add(self.var, 0, wx.ALIGN_CENTER)
        modifSizer.AddSpacer((10, 0), 0)
        modifSizer.Add(titre, 0, wx.ALIGN_CENTER)
        modifSizer.AddSpacer((10, 0), 0)
        modifSizer.Add(self.choix, 0, wx.ALIGN_CENTER_VERTICAL)
        #modifSizer.AddSpacer((10, 0), 0)

        # valeur de la zone selectionnee
        self.valZ = wx.Button(self, self.ID_VALEUR, "Val : 0", size = (80,20))        
        #bouton  milieu pour zone, puis deplacer, puis modif
        self.butZoneMil=wx.BitmapButton(self, self.ID_ZONEMIL, self.icones['Top_zoneLay'],size=(25,24))
        self.butHisto=wx.BitmapButton(self, self.ID_HISTO, self.icones['Top_Histo'],size=(25,24))
        self.butMove=wx.BitmapButton(self, self.ID_MOVEZONE, self.icones['Top_move'],size=(25,24))
        self.butMod=wx.BitmapButton(self,self.ID_MODIFZONE,self.icones['Top_modifPoly'],size=(25,24))
        butCopy=wx.Button(self,self.ID_COPY,'C',size=(25,24))
        butPaste=wx.Button(self,self.ID_PASTE,'P',size=(25,24))
        # Bouton supprimer zone
        butX=wx.BitmapButton(self,self.ID_DELZONE,self.icones['Top_supprime'],size=(25,24))
        butXX=wx.BitmapButton(self,-1,self.icones['Top_supprimeAll'],size=(25,24))
        
        self.butZoneMil.SetToolTipString(self.traduit('Changer milieux'))
        self.butHisto.SetToolTipString(self.traduit('Zones transitoires'))
        self.butMove.SetToolTipString(self.traduit('Deplacer zone'))
        self.butMod.SetToolTipString(self.traduit('Modifier polygone'))
        butX.SetToolTipString(self.traduit('Detruire zone'))
        butXX.SetToolTipString(self.traduit('Detruire toutes zones'))
        
        modifSizer.Add(self.valZ,0,wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border = 5)
        modifSizer.AddMany([(self.butZoneMil,0),(self.butHisto,0),(self.butMove,0),(self.butMod,0),
                (butCopy,0),(butPaste,0),(butX, 0),(butXX, 0)])
        self.SetSizer(modifSizer)

        wx.EVT_CHOICE(self, self.ID_CHOIX, self.OnChoice)
        wx.EVT_BUTTON(self, self.ID_VALEUR, self.OnValeurZ)
        wx.EVT_BUTTON(self, self.ID_ZONEMIL, self.OnZoneMil)
        wx.EVT_BUTTON(self, self.ID_HISTO, self.OnHisto)
        wx.EVT_BUTTON(self, self.ID_MOVEZONE, self.OnMoveZ)
        wx.EVT_BUTTON(self, self.ID_MODIFZONE, self.OnModifZone)
        wx.EVT_BUTTON(self, self.ID_COPY, self.OnCopyZone)
        wx.EVT_BUTTON(self, self.ID_PASTE, self.OnPasteZone)
        wx.EVT_BUTTON(self, self.ID_DELZONE, self.OnDelZone)
        self.Bind(wx.EVT_BUTTON,self.OnDelAllZones,butXX)
  
    def updateChoice2OnChange(self,nomv,mil):
        # mise a jour de la liste de zone pour la nouvelle variable selectionnee
        # sur un milieu donne
        self.currentVar = nomv;self.currentMil=mil
        if nomv==None: return
        self.var.SetLabel(self.traduit(nomv)+' :')
        self.currentZone = None
        zoneList = self.aquifere.getZoneList(nomv)        
        self.choix.Clear();self.zindex=[]
        for i in range(len(zoneList)):
            if self.currentMil in zoneList[i].getInfo()[2]:
                self.choix.Append(zoneList[i].getNom());self.zindex.append(i)
        self.valZ.SetLabel("Val : ")
   
    def OnChoice(self, evt):  #choix de la zone
        self.izone = self.zindex[self.choix.GetSelection()];
        self.currentZone = self.aquifere.getZone(self.currentVar,self.izone)
        self.valZ.SetLabel("Val : "+str(self.currentZone.getVal())[:5])

    def OnValeurZ(self, evt):
        #changer la valeur, faire apparaitre le dialogue
        z=self.currentZone
        if z==None : return
        val = z.getVal()
        if type(val)==type([5,6]): val='liste'
        nom = z.getNom();info=z.getInfo()
        l0=[(nom,val)];typz='B.Condition'
        if self.currentVar in ['Potentiel','Transport','PHT3D']:
            typz=info[3]
            if typz=='Constant': typz='B.Condition'  # pb with old versions
            l0.append(('Type',[typz,['Initial','B.Condition','Transient']]))
        dialg = MyDialogs.MyGenericCtrl(self,"modifier zone",l0)
        if dialg.ShowModal() == wx.ID_OK:
            lst2 = dialg.GetValues()
            if lst2[0][1]!='liste':
                val=lst2[0][1];z.setVal(val);
                self.visu.modifValZone(self.currentVar, self.izone, val) 
                self.valZ.SetLabel("Val : "+ str(val))
        # changer la valeur pour la zone selectionnee
            if self.currentVar in ['Potentiel','Transport','PHT3D']:
                z.setInfo(3,lst2[1][1][0]) 
            self.aquifere.createZoneTransient()
                       
        dialg.Destroy()               

    def OnZoneMil(self,evt):
        """ dialogue pour modifier les milieux que recouvre une zone"""
        if self.currentZone==None : return
        mil = self.currentZone.getInfo()[2]
        dialg = MyDialogs.MyGenericCtrl(self,"couches zone",[('couche Haut',mil[0]),('couche Bas',mil[-1])])
        if dialg.ShowModal() == wx.ID_OK:
            mil = dialg.GetValues();millist=range(mil[0][1],mil[1][1]+1);
            self.currentZone.setInfo(2,millist)
            self.visu.modifLayZone(self.currentVar, self.izone, millist)            
        dialg.Destroy()               

    def OnHisto(self,evt):
        """dialogue pour rentrer un historique sur une zone"""
        z = self.currentZone
        if z==None : return
        li0 = []
        if z.getForme()!=4 and type(z.getVal())==type([5,6]): li0 = z.getVal()# ne pas prendre polyV
        dialg = MyDialogs.MyListDialog(self,self.traduit('Historique Zone'),li0)
        retour = dialg.ShowModal()
        if retour == wx.ID_OK:
            li1 = dialg.GetStrings()
            z.setVal(li1);self.aquifere.createZoneTransient()
        else : return
        dialg.Destroy()
        self.visu.modifValZone(self.currentVar, self.izone, li1)            

    def OnMoveZ(self,evt):
        """ demarre deplacemnt d'une zone"""
        if self.currentZone != None:
            self.model.doAction('Top','zoneStart') 
            self.visu.startMoveZone(self.currentVar, self.izone)
        else :
            self.OnMessage ("Veuillez selectionner une zone")
        
    def OnModifZone(self, evt):
        """" demarre la modification de zone de visu apres des tests"""
        if self.currentZone != None:
            self.model.doAction('Top','zoneStart') 
            self.visu.modifZone(self.currentVar, self.izone)
        else :
            self.OnMessage ("Veuillez selectionner une zone")
            
    # Recupere les coordonnees de la zone modifiee ou move pour mettre a jour le model
    def OnModifZoneCoord(self, var, index, coord):
        self.model.doAction('Top','zoneEnd')
        self.aquifere.getZone(var, index).setXy(coord)
        if self.currentVar=='PHT3D': self.model.doAction('PHT3D','Source') 
        else : self.model.doAction('Aquifere','ValBase')                
        
    def OnCopyZone(self,evt):
        var = self.currentVar;
        if self.currentZone != None:
            self.copyXy = self.currentZone.getXy()
            self.copyShape = self.currentZone.getForme()
        
    def OnPasteZone(self,evt):
        var = self.currentVar; mil=self.currentMil
        info = [var,self.aquifere.getNbzone(var),[mil]]
        units = self.aquifere.getUnits(var)
        l0=[('nom','z'),('Valeur ('+units+')',0.0)]
        if len(self.copyXy)>0:
            xy=self.copyXy;shapeZone=self.copyShape
            dialg = MyDialogs.MyGenericCtrl(self,"coller",l0)
            if dialg.ShowModal() == wx.ID_OK:
                lst2 = dialg.GetValues()
                nameZone=lst2[0][1]
                valueZone = lst2[1][1];self.valZ.SetLabel("Val : "+ str(valueZone))
                self.model.Aquifere.addZone(var,nameZone,valueZone,shapeZone,info,xy)
                self.visu.addZone(mil,nameZone, valueZone,shapeZone,info,xy)
                self.aquifere.createZoneTransient();self.visu.redraw()
            dialg.Destroy()               
            # mise a jour du choix des zones pour la variable courante
            self.gui.modifBox.updateChoice2OnChange(var,mil)
        else :
            self.OnMessage("pas de zone copiee")
        
    def OnDelZone(self, evt):
        var = self.currentVar; mil=self.currentMil;dd=0
        nomz=self.aquifere.getZone(var, self.izone).getNom()
        # si pas de zone selectionnee, on ne supprime pas...
        if self.currentZone != None:
            self.aquifere.delZone(var, self.izone)
            self.visu.delZone(var, self.izone)
            self.updateChoice2OnChange(var,self.currentMil)
        else :
            self.OnMessage("Veuillez selectionner une zone")

    def OnDelAllZones(self,evt):
        var = self.currentVar;
        zList=self.aquifere.getZoneList(var)
        dlg= wx.MessageDialog(self,"Caution you will destroy all zones","Attention",style = \
                wx.ICON_INFORMATION|wx.CENTRE|wx.OK|wx.CANCEL)
        retour=dlg.ShowModal()
        if retour==wx.ID_OK:
            self.aquifere.delAllZones(var)
            self.visu.delAllZones(var) 
            self.updateChoice2OnChange(var,self.currentMil)

    def getZonesByName(self, var, nom):
        zList=self.aquifere.getZoneList(var); zLout=[]
        for i in range(len(zList)):
            if zList[i].getNom()==nom:
                zLout.append(zList[i].getInfo()[1])
        return zLout
