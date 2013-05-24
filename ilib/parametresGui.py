import wx
import MyDialogs
from Aquifere import Zone
from os import sep
import os
from scipy import *

class parametresGui(wx.Panel):

    def __init__(self,gui,model):

        self.gui = gui
        self.visu, self.model = gui.Visu, model
        self.OnMessage = gui.OnMessage
        self.OnRepondre = gui.OnRepondre
        self.traduit = gui.traduit
        self.tradinverse = gui.tradinverse
        self.langue  = gui.LANG
        self.currentVar, self.currentMil, self.milList = None,0,[]
        wx.Panel.__init__(self,gui,-1,size=(-1,400))
        self.panelSizer = wx.BoxSizer(wx.VERTICAL)
        #self.SetBackgroundColour('#1CFAFF')
        self.icones = gui.icones
        self.groupes={'Modele':[0,'Type','Unites','Domaine','Grille','GriVar','Carte','Milieu'],
            'Ecoulement':[1,'V_Ecoul','SolvListe','Solver','Temps','Write','Run','Particule'],
            'Transport':[2,'V_Transp','Transp','Methodes','Particules',
                    'Solver','Write','Run'],
            'PHT3D':[3,'V_Pht3d','Import','Chemistry','PHparm','Immobile','Write','Run'],
            'Observation':[4,'ZoneO']}
        self.tipNames={'Modele':['','','Unites','Domaine','Grille','Grille variable',
                                'Choisir Carte'],
            'Ecoulement':['','V_Ecoul','Choix du solveur','Parametres','Temps pour calcul',
                          'Ecrire fichiers','Lancer','Lancer Particule'],
            'Transport':['','V_Transp','Parameters','Methodes','Particules',
                         'Solver','Ecrire fichiers','Lancer'],
            'PHT3D':['','V_Pht3d','Import BDonnee','Chimie','Parametres',\
                     'Chimie domaine immobile','Ecrire fichiers','Lancer'],
            'Observation':['','Affiche zones']}
        self.creerBox();self.setDualPoro(False)
        self.SetSizer(self.panelSizer);
    def initParm(self):
        self.currentVar, self.currentMil, self.milList = None,0,[]
    def getCurrentVar(self):return self.currentVar
    def getCurrentMil(self):return self.currentMil

    def unitsForDialog(self,nom):
        u = self.model.getParm('Aquifere','Unites');d=u[0][1][0];t=u[1][1][0]
        if nom=='K': return ' ('+t+'-1)'
        elif nom in ['Domaine','Grille']: return ' ('+d+')'
        else : return ' '

    def creerBox(self):
        self.numBouton = 100
        self.dictBox={}
        for ig in range(len(self.groupes)): 
            for g0 in self.groupes: #pour ordonner
                if self.groupes[g0][0]==ig: g=g0
            self.dictBox[g] = Boite(self,g);
            #if g!='Modele': self.dictBox[g].Enable(False)
            self.panelSizer.Add(self.dictBox[g],0) #,wx.EXPAND)
            self.panelSizer.AddSpacer((0, 5), 0)
        # disable bitmap for immobile
        but = self.FindWindowByName('PHT3D_Immobile')
        but.SetBitmapDisabled(self.gui.icones['PH_ImmobileDisable'])

    def boxVisible(self,nomBox,bool):
        if nomBox in self.dictBox.keys():
            self.dictBox[nomBox].Enable(bool)

    def boutonVisible(self,nomBut,bool):
        item = self.FindWindowByName(nomBut);item.Enable(bool)
        
    def setDualPoro(self,bool):
        #self.boutonVisible('PHT3D_DualPoro',bool)
        self.boutonVisible('PHT3D_Immobile',bool)
        
    def setVbase(self,groupe,item):
        nomv = self.currentVar;mil=self.currentMil;#print nomv
        v = self.model.Aquifere.getVbase(nomv,mil)
        but=self.FindWindowByName(groupe+'_ValBase')
        but.SetLabel(str(v))
##        if type(v)==type(5.): self.vbase.SetLabel("Val : "+ str(v))
##        else : self.vbase.SetLabel("Val : grid ")
        self.txtunit.SetLabel(self.model.Aquifere.getUnits(nomv))
        self.visu.showVar(nomv,mil)

    def OnButton(self,evt):
        item = self.FindWindowById(evt.GetId());n = item.GetName(); #getName ou getLabelText
        [groupe,nom]=n.split('_');
        if groupe=='Modele': groupe='Aquifere' #car toute donnes dans aqui
        retour = self.gui.control.valide(groupe,nom)
        if retour =='Stop' : return
        aqui=self.model.Aquifere
        ### AQUIFERE
        if nom=='GriVar':
            dic1=self.model.getParm(groupe,nom)
            dialg = MyDialogs.MyGriVarDialog(self,self.traduit(str(nom)),dic1)
            retour = dialg.ShowModal()
            if retour == wx.ID_OK:
                dic2 = dialg.GetValues();
                self.model.setParm(groupe,nom,dic2)
            dialg.Destroy()               
        elif nom=='zList': # liste des z de couches
            li1=self.model.getParm(groupe,nom)
            dialg = MyDialogs.MyListDialog(self,self.traduit(str(nom)),li1)
            retour = dialg.ShowModal()
            if retour == wx.ID_OK:
                li2 = dialg.GetValues()
                self.model.setParm(groupe,nom,li2)
            dialg.Destroy()                           
        elif nom=='Variable':
            s=str(item.GetStringSelection())
            if s=='Tr_Source': s='Transport'
            if s=='PH_Source': s='PHT3D'
            self.currentVar = self.tradinverse(s);
            self.setVbase(groupe,item) # met vbase actuel sur bouton
        elif nom=='Milieux':
            self.currentMil=int(item.GetStringSelection())
            #self.setVbase(groupe,item)
        elif nom=='ValBase':
            if self.currentVar==None: return
            mil = self.currentMil
            v = aqui.getVbase(self.currentVar,mil)
            u = ' ('+aqui.getUnits(self.currentVar)+')'
            if self.currentVar=='Mur' or (self.currentVar=='Toit' and int(mil)==0):
                dialg = MyDialogs.MyGenericCtrl(self,nom+u,[(self.currentVar,v)])
                if dialg.ShowModal() == wx.ID_OK:
                    lst2 = dialg.GetValues()
                    if lst2 != None:
                        v = lst2[0][1]
                        aqui.setVbase(self.currentVar,v,[mil])
            elif self.currentVar=='Toit' and int(mil)>0:
                return
            else :
                lst=[(self.currentVar,v)]
                if aqui.getDim()=='3D':
                    lst.extend([('Milieu Haut',0),('Milieu Bas',0)])
                dialg = MyDialogs.MyGenericCtrl(self,nom+u,lst)
                if dialg.ShowModal() == wx.ID_OK:
                    lst2 = dialg.GetValues()
                    if lst2 != None:
                        v = lst2[0][1];llist=[self.currentMil]
                        if aqui.getDim()=='3D':
                            llist= range(lst2[1][1],lst2[2][1]+1) #range of media 
                        aqui.setVbase(self.currentVar,v,[int(l)for l in llist])
            dialg.Destroy()               
            but=self.FindWindowByName(groupe+'_ValBase')
            but.SetLabel(str(v))
            #self.vbase.SetLabel(str(v))
        elif nom=='Carte' :
            dlg = wx.FileDialog(self,self.traduit("Choisir une carte"),"","","*.png",wx.OPEN)
            retour = dlg.ShowModal()
            if retour == wx.ID_OK:
                path = dlg.GetPath()            
                self.model.setMap(path)
            else : return
            dlg.Destroy()
        ### ECOULEMENT
        elif nom=='Particule':
            pName = self.model.getProjectName();
            if pName=='':  # pas de projet
                self.OnMessage('creez ou sauvez votre projet')
                return
            self.visu.startParticules(); self.startP = True;
            self.model.doAction('Top','zoneStart')
        ### Transport
        elif nom in ['Import','Write']: pass
        elif nom=='Chemistry':
            dic = self.model.getParm(groupe,nom)
            dialg = MyDialogs.MyNoteBook(self,"Chemistry",dic)
            retour = dialg.ShowModal()
            if retour == wx.ID_OK:
                dic2 = dialg.GetValues()
                if dic2 != None:
                    self.model.setParm(groupe,nom,dic2)
            dialg.Destroy()                         
        elif nom=='PH_Source':
            nomv ='PHT3D';self.currentVar=nomv;
            self.visu.changeAxesOri('Z',self.currentMil)
            self.visu.showVar(nomv,self.currentMil)
        elif nom=='Immobile':
            dic = self.model.getParm(groupe,nom)
            dialg = MyDialogs.MyNoteBook(self,"Chemistry Immobile",dic)
            retour = dialg.ShowModal()
            if retour == wx.ID_OK:
                dic2 = dialg.GetValues()
                if dic2 != None:
                    self.model.setParm(groupe,nom,dic2)
            dialg.Destroy()                                     
        ### Observation
        elif nom=='ZoneO':
            nomv ='Observation';self.currentVar=nomv;
            self.visu.changeAxesOri('Z',self.currentMil)
            self.visu.showVar(nomv,self.currentMil)
            zlist=aqui.getZoneList(nomv);znames=[z.getNom() for z in zlist]
            self.gui.afficheTree.setNames('Observation_Zone_L',znames)
        ### GENERIQUES
        elif nom[:3]=='Run': pass
        else :
            lstDialg = self.model.getParm(groupe,nom)
            if lstDialg==None: return
            u = self.unitsForDialog(nom)
            dialg = MyDialogs.MyGenericCtrl(self,str(nom)+u,lstDialg)
            retour = dialg.ShowModal()
            if retour == wx.ID_OK:
                lst2 = dialg.GetValues()
                if lst2 != None:
                    self.model.setParm(groupe,nom,lst2)
            dialg.Destroy()               
        self.model.doAction(groupe,nom) 
        
    def setTransit(self,especes,per,Cinj):
        """ pour retour du dialogue transitoire"""
        #print 'ds param',per,Cinj
        if especes[0]=='Traceur':
            self.model.setParm('Traceur','inj',[list(per),list(Cinj[:,0])])
        else :
            self.model.Reaction.setInjPeriodes(list(per))
            self.model.Reaction.setInjConcentr(Cinj)            

    def setList(self,groupe,nom,lnew):
        item = self.FindWindowByName(groupe+'_'+nom);item.Clear()
        for i in range(len(lnew)):item.Append(lnew[i])
        
    def setListChoix(self,groupe,nom,index):
        item = self.FindWindowByName(groupe+'_'+nom)
        item.SetSelection(index)
        
class Boite(wx.Panel):
    def __init__(self,parent,gr):
        self.parent=parent
        wx.Panel.__init__(self,parent,-1,size=(-1,350))
        bxSizer=wx.StaticBoxSizer(wx.StaticBox(self, -1, parent.traduit(gr)),
                wx.VERTICAL)
        grdSizer = wx.GridSizer(2,4,vgap=3,hgap = 3)
        bx2=wx.BoxSizer(wx.HORIZONTAL)
        for i in range(len(parent.groupes[gr][1:])):
            n=parent.groupes[gr][i+1]
            nomCourt = gr[:2]+'_'+n;nom = gr+'_'+n;
            if n=='Type':
                but = wx.Button(self, parent.numBouton,parent.traduit("Type de Modele"),name=nom)
                bxSizer.Add(but, 0) #,wx.EXPAND)
                bxSizer.AddSpacer((0,5), 0)
                wx.EVT_BUTTON(self, parent.numBouton, parent.OnButton)
            elif n[:2]=='V_':
                s1=wx.BoxSizer(wx.HORIZONTAL)
                tx1=wx.StaticText(self,-1,parent.traduit('Var.'))
                n='Variable';liste = parent.model.getParm(gr,n);nom=gr+'_'+n
                chlist=[parent.traduit(n) for n in liste]
                choix = wx.Choice(self, parent.numBouton, choices=chlist, name=nom)
                wx.EVT_CHOICE(self, parent.numBouton, parent.OnButton)        
                parent.numBouton += 1
                s1.AddMany([(tx1,0),(choix,0)])
                s2=wx.BoxSizer(wx.HORIZONTAL)
                tx2=wx.StaticText(self,-1,parent.traduit('Backg.'))
                ti1 = " 0 ";n='ValBase';nomCourt = gr[:2]+'_'+n;nom=gr+'_'+n;
                vbase = wx.Button(self, parent.numBouton,ti1, name = nom, size = (50,20))        
                parent.numBouton += 1
                self.Bind(wx.EVT_BUTTON, parent.OnButton,vbase)
                s2.AddMany([(tx2,0),(vbase,0)])
                if gr=='Ecoulement':
                    parent.txtunit = wx.StaticText(self,-1,"",style = wx.ALIGN_CENTER_VERTICAL)
                    s2.Add(parent.txtunit,0)
                bxSizer.AddMany([(s1,5),(s2,5)])
            elif n=='Milieu':
                n='Milieux';liste = parent.model.getParm(gr,n);nom=gr+'_'+n;
                chlist=['z','n'];#[parent.traduit(n) for n in liste[1]]
                choix = wx.Choice(self, parent.numBouton, choices=chlist, name=nom)
                #if liste[0] in liste[1]:
                #    num=liste[1].index(liste[0]);choix.SetSelection(num)
                wx.EVT_CHOICE(self, parent.numBouton, parent.OnButton)        
                parent.numBouton += 1
                bx2.AddMany([(wx.StaticText(self,-1,parent.traduit('Milieu')),5),(choix,0)]) #,(parent.togBut,0)
            else :
                but = wx.BitmapButton(self,parent.numBouton,parent.icones[nomCourt],size=(25,24),name=nom)
                grdSizer.Add(but, 0);
                if parent.tipNames[gr][i+1]!='':
                    but.SetToolTipString(parent.traduit(parent.tipNames[gr][i+1]))
                wx.EVT_BUTTON(self, parent.numBouton, parent.OnButton)
            parent.numBouton += 1
        bxSizer.AddMany([(grdSizer, 0),(bx2,0)])
        self.SetSizer(bxSizer)

