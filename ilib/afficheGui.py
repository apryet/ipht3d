import wx
from scipy import sum,linspace,shape
import MyDialogs

class MyTreeCtrl(wx.TreeCtrl):
    
    def __init__(self, parent, id, style):
        wx.TreeCtrl.__init__(self, parent, id, size=(120,400),style=style)

class afficheGui(wx.Panel):

    def __init__(self, parent, model):
        
        self.parent = parent
        self.model = model
        self.traduit = parent.traduit

        tID = wx.NewId()
        wx.Panel.__init__(self,parent,-1)
        self.tree = MyTreeCtrl(self, tID, wx.TR_HAS_BUTTONS)

        isz1 = (14,14);isz2 = (10,10)
        il = wx.ImageList(isz1[0], isz1[1])
        foldrid = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,wx.ART_OTHER, isz1))
        foldropenid = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,wx.ART_OTHER, isz1))
        fileid = il.Add(wx.ArtProvider_GetBitmap(wx.ART_REPORT_VIEW, wx.ART_OTHER, isz1))
        chekid = il.Add(wx.ArtProvider_GetBitmap(wx.ART_TICK_MARK,wx.ART_MENU, isz1))
        self.fileid = fileid
        self.chekid = chekid
        self.tree.SetImageList(il)

        self.il = il
        self.listItem = {}
        self.root = self.tree.AddRoot(self.traduit("VUE"))
        self.tree.SetPyData(self.root, None)
        self.tree.SetItemImage(self.root, foldrid, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.root, foldropenid, wx.TreeItemIcon_Expanded)

        self.groupeTrad = [] # liste des groupes traduite
        self.itemTrad = [[],[]]  # liste des items francais et traduits

        for groupe in self.getGlistK():
            self.groupeTrad.append(self.traduit(groupe))
            child = self.tree.AppendItem(self.root, self.traduit(groupe))
            self.tree.SetPyData(child, None)
            self.tree.SetItemImage(child, foldrid, wx.TreeItemIcon_Normal)
            self.tree.SetItemImage(child, foldropenid, wx.TreeItemIcon_Expanded)
            if groupe == '4.Organiques': self.treeRorg = child
            if groupe == '5.A_electrons': self.treeRmin = child
            if groupe == '6.rt3d': self.treeRt3d = child
            if groupe == '7.pht3d': self.treePht3d = child
            if groupe == '8.reactionIsot': self.treeRisot = child
            for item in self.model.getGlist()[groupe]:
                self.itemTrad[0].append(item);self.itemTrad[1].append(self.traduit(item))
                last = self.tree.AppendItem(child, self.traduit(item))
                self.tree.SetPyData(last, None) #self.modelGetData(item))
                self.listItem[item] = [groupe,last]

        self.tree.Expand(self.root)
        self.tree.SortChildren(self.root)

        wx.EVT_TREE_ITEM_RIGHT_CLICK(self, tID, self.OnSelRClick)
        wx.EVT_TREE_ITEM_ACTIVATED (self, tID, self.OnActivate)


    def getGlistK(self): return self.model.getGlist().keys()
    def getGlist(self,groupe,nom,parm):
        if self.model.getGlist()[groupe].has_key(nom):
            return self.model.getGlist()[groupe][nom][parm]
    def setGlist(self, groupe, nom, parm, valeur):
        if self.model.getGlist()[groupe].has_key(nom):
            self.model.setGlistParm(groupe, nom, parm, valeur)
    
    def OnSelRClick(self,event):
        etat = self.model.getEtat();self.lastNom=""
        item = event.GetItem()
        nomLu = self.tree.GetItemText(item)
        parent = self.tree.GetItemParent(item)
        groupeLu = self.tree.GetItemText(parent)
        groupe = groupeLu;
        if (int(groupe[:1])<4):
            inom = self.itemTrad[1].index(nomLu);nom = self.itemTrad[0][inom]
        else :
            nom = nomLu
        
        n = nom.startswith('temps')
        if n==False:
            gr = self.model.getGlist();bool = 1-gr[groupe][nom]['on']
            self.setGlist(groupe,nom,'on',bool*1)
        
        if nom=='carte': self.parent.Visu.drawMap(self.model.getMapName(),bool)
        elif nom=='grille': self.parent.Visu.drawGrid(bool)
        elif nom == 'zoneImg': self.OnZoneImg(bool)
        elif (nom=='charge')and(etat>1): self.parent.Visu.drawContour('charge',bool)
        elif (nom=='flux')and(etat>1):self.parent.Visu.drawVecteur(bool)
        elif (nom=='particules')and(etat>1):self.parent.Visu.drawParticules('E',bool)
        elif (nom=='tracer')and(etat>2): self.parent.Visu.drawContour('tracer',bool)
        elif (nom=='tracerI')and(etat>2): self.OnTracerI(bool)
        elif (nom=='tubesflux')and(etat>2): self.parent.Visu.drawParticules('tracer',bool)
        elif ((groupe=='6.rt3d')or(groupe=='7.pht3d'))and(etat>2):
            if nom.startswith('temps'):
                ltemps = self.model.rt3d.getListeTemps()
                indx = self.model.getTempsRt3d()+1
                if indx>(len(ltemps)-1): indx=0
                self.model.setTempsRt3d(indx)
                self.tree.SetItemText(item,'temps '+str(ltemps[indx]))
            else:
                if groupe.startswith('6'): self.model.setEspeceRt3d(nom)
                elif groupe.startswith('7'): self.model.setEspecePht3d(nom)
                self.contourRtPht3d(True, groupe,nom)
        else:            
            self.model.setIndxReac(nom)
            if groupe=='8.reactionIsot': nom=nom+'Isot'
            self.parent.Visu.drawContour(nom,True)

    def OnActivate(self,event):
        """ action lors d'un dble-click sur un des elements de l'arborescence
        fait appararaitre un dialogue pour changer l'objet visualise"""
        item = event.GetItem()
        nomLu = self.tree.GetItemText(item)
        parent = self.tree.GetItemParent(item)
        groupeLu = self.tree.GetItemText(parent)
        groupe = groupeLu #self.groupeInit[self.groupeTrad.index(groupeLu)]
        if (int(groupe[:1])<4):
            inom = self.itemTrad[1].index(nomLu);nom = self.itemTrad[0][inom]
        else :
            nom = nomLu
        grpR = ['4.Organiques','5.A_electrons','6.rt3d','7.pht3d','8.reactionIsot']
        if (nom=='charge')or(nom=='tracer')or(groupe in grpR):
            self.OnChangeContour(groupe, nom)
        
    def setAffiche(self):
        """lors de l'import d'un fichier, coche ou decoche selon Glist du
        fichier importe, ca marche pas vraiment"""
        self.updateReacOrg();self.updateReacMin();self.updateReacIsot();
        self.updateRt3d()
        
    def updateReacOrg(self):
        """ remet a jour le contenu du dossier reaction"""
        listReac = self.model.getGlist()['4.Organiques']
        self.tree.CollapseAndReset(self.treeRorg)
        for item in listReac:
            last = self.tree.AppendItem(self.treeRorg, item)
            self.tree.SetPyData(last, None)
    def updateReacMin(self):
        """ remet a jour le contenu du dossier reaction"""
        listReac = self.model.getGlist()['5.A_electrons']
        self.tree.CollapseAndReset(self.treeRmin)
        for item in listReac:
            last = self.tree.AppendItem(self.treeRmin, item)
            self.tree.SetPyData(last, None)
    def updateRt3d(self):
        """ remet a jour le contenu du dossier Rt3d"""
        listRt3d = self.model.getGlist()['6.rt3d']
        self.tree.CollapseAndReset(self.treeRt3d)
        for item in listRt3d:
            last = self.tree.AppendItem(self.treeRt3d, item)
            self.tree.SetPyData(last, None)
    def updatePht3d(self):
        """ remet a jour le contenu du dossier Rt3d"""
        listPht3d = self.model.getGlist()['7.pht3d']
        self.tree.CollapseAndReset(self.treePht3d)
        for item in listPht3d:
            last = self.tree.AppendItem(self.treePht3d, item)
            self.tree.SetPyData(last, None)
    def updateReacIsot(self):
        """ remet a jour le contenu du dossier reaction"""
        listReac = self.model.getGlist()['8.reactionIsot']
        self.tree.CollapseAndReset(self.treeRisot)
        for item in listReac:
            last = self.tree.AppendItem(self.treeRisot, item)
            self.tree.SetPyData(last, None)

    def OnChangeCarte(self, evt):
        pass    
    def OnChangeGrille(self, evt):
        pass
    def OnZoneImg(self,bool):
        if bool:
            ivar = self.parent.parametresAquifere.choix.GetSelection()
            nomv = self.model.aquifere.getVbaseName2()[ivar]
            vbase = self.model.aquifere.getVbase(nomv)
            mat = self.model.aquifere.obj2mat(nomv,vbase)
            self.parent.Visu.createImage('Z',mat)
        self.parent.Visu.drawImage('Z',bool)
    def OnChangeZone(self):
        pass
    
    def OnChangeContour(self,groupe,nom):
        """ modifie la valeur et les couleurs des contours : valeur[0] : min
        [1] : max, [2] nb contours, [3] decimales, [4] : 'lin' log' ou 'fix',
        si [4]:fix, alors [0] est la serie des valeurs de contours """
        valeur = self.getGlist(groupe,nom,'valeur');
        col = self.getGlist(groupe,nom,'col')
        dlgContour = MyDialogs.MyDialogContour(self, "Contours",valeur,col)
        if dlgContour.ShowModal() == wx.ID_OK:
            val = dlgContour.GetStrings()
            log = dlgContour.log.GetValue()
            # creer le vecteur de couleurs
            c = dlgContour.coul
            col=[(c[0].Red(),c[0].Green(),c[0].Blue()),(c[1].Red(),c[1].Green(),c[1].Blue()),
                 (c[2].Red(),c[2].Green(),c[2].Blue())]
        else : return
        valeur = val[:5];valeur[4] = 'lin'
        if len(val[-1])>5 :
            valeur[0] = eval(val[-1]); valeur[4] = 'fix'
        elif log :
            valeur[4] = 'log'
        self.setGlist(groupe,nom,'valeur',valeur)  #nb le Glist de RT3d est le mm que Reaction
        self.setGlist(groupe,nom,'col',col)
        nom2 = nom
        if groupe=='6.rt3d': nom2 = 'rt'+nom
        elif groupe=='7.pht3d': nom2 = 'pht'+nom
        elif groupe=='8.reactionIsot': nom2=nom+'Isot'
        self.parent.Visu.changeContour(valeur=valeur,typC=nom2,col=col)
        self.parent.Visu.drawContour(nom2,True)

    def OnChangeFlux(self,evt):
        pass
    def OnChangeTubes(self):
        pass

    def OnTracerI(self,bool):
        if bool:
            xp, yp = self.model.tracer.getXPYP1()
            Ct = self.model.tracer.getCt()
            mat = self.parent.model.aquifere.irreg2mat(xp,yp,Ct)
            self.parent.Visu.createImage('T',mat[::-1,:]) # on inverse l'image
        self.parent.Visu.drawImage('T',bool)        
    def OnChangeTracerI(self):
        pass
    
    def contourRtPht3d(self, bool, groupe,nom):
        if groupe=='6.rt3d':
            typ = 'rt';indespece = self.model.rt3d.getIespece()
        elif groupe=='7.pht3d':
            typ = 'pht';indespece = self.model.getIndxPht3d();print indespece
        else : print 'erreur groupe'
        if bool:
            temps = self.model.getTempsRt3d()  # c'est l'index du temps dans la liste          
            X,Y = self.model.ecoulement.getXYmesh()
            Z = self.model.rt3d.lireEspece(typ, temps, indespece)
            if typ=='pht': Z = Z*self.model.reaction.getMmFromName(nom)*1000
            valeur = self.getGlist('4.Organiques',nom,'valeur')
            col = self.getGlist('4.Organiques',nom,'col')
            self.parent.Visu.createContour(X,Y,Z,typC=typ+nom,valeur=valeur,col=col)
            self.parent.Visu.drawContour(typ+nom,True)
        else:
            self.parent.Visu.drawContour(typ+nom,False)
