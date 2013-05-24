import wx
import os
import webbrowser as web
import MyDialogs
from scipy import *
import zipfile as zp
import urllib as url

class Menus:
    def __init__(self,parent):
        self.gui = parent;self.traduit = parent.traduit;
        self.tradinverse= parent.tradinverse
        self.visu,self.afficheTree = parent.Visu, parent.afficheTree
        self.model = parent.model
        self.OnMessage=parent.OnMessage

    def OnNew(self,evt):
        self.askSave(evt)
        dlg = wx.FileDialog(self.gui,self.traduit('Nouveau Modele'),"","","*.ipht",wx.OPEN)
        retour = dlg.ShowModal()
        if retour == wx.ID_OK:
            # on recupere le chemin complet
            chemin = dlg.GetDirectory()
            fullName = dlg.GetFilename()
            filename = fullName.split(os.extsep)[0];  # filename sans extension
            #modification du projet
            self.model.initModel()
            self.model.setProject([chemin,filename])                                 
            self.visu.setVisu(self.model,self.model.getGlist())
            self.gui.updateTitle()
            self.OnMessage("Projet cree")

    def OnOpen(self,evt):
        if self.model.getProjectName()!='':
            self.askSave(evt)
        dlg = wx.FileDialog(self.gui,self.traduit('Ouvrir'),"","","*.ipht",wx.OPEN)
        retour = dlg.ShowModal();

        if retour == wx.ID_OK:            
            chemin = dlg.GetDirectory()
            fullName = dlg.GetFilename()
            temp = fullName.split(os.extsep); filename = temp[0]
            # mise a jour du nom du projet            
            self.model.setProject([chemin,filename])
            self.model.openModel()
            #self.changeEtat(m['etat'])
            self.gui.updateTitle()
            self.OnMessage("Fichier iPht3d importe")

    def OnSave(self,evt):
        if len(self.model.getProjectName())<1 :
            self.OnSaveAs(evt); return
        self.model.saveModel()
        self.OnMessage("Sauvegarde Reussie")
        
    def OnSaveAs(self,evt):
        dlg = wx.FileDialog(self.gui,"Sauvegarder","",self.model.getProjectName(),"*.ipht",wx.SAVE)
        retour = dlg.ShowModal()

        if retour == wx.ID_OK:            
            chemin = dlg.GetDirectory();#dsk,chemin=chemin.split(':')
            fullName = dlg.GetFilename()
            temp = fullName.split(os.extsep); filename = temp[0]
            # mise a jour du nom du projet
            self.model.setProject([chemin,filename])
            # mettre etat modele a 0 puis sauvegarde
            self.OnSave(evt)
            self.gui.updateTitle()

    def askSave(self,evt):
        message = wx.MessageDialog(self.gui,self.traduit("Voulez-vous sauvegarder le projet?"),"Sauvegarde",style = wx.ICON_QUESTION|wx.YES_NO|wx.CENTRE,pos=wx.DefaultPosition)
        retour = message.ShowModal()
        if retour == wx.ID_YES:
            self.OnSave(evt)
        else : return
        message.Destroy()

    def OnImportVar(self,evt):
        id = evt.GetId();
        item = self.gui.menuBarre.FindItemById(id);
        dlg = wx.FileDialog(self.gui,self.traduit('Ouvrir'),"","","",wx.OPEN)
        retour = dlg.ShowModal();
        if retour == wx.ID_OK:            
            longName = dlg.GetPath()
        self.model.impVar(longName,self.tradinverse(str(item.GetText())))

    def OnImportZones(self,evt):
        id = evt.GetId();
        item = self.gui.menuBarre.FindItemById(id);
        dlg = wx.FileDialog(self.gui,self.traduit('Ouvrir'),"","","",wx.OPEN)
        retour = dlg.ShowModal();
        if retour == wx.ID_OK:            
            longName = dlg.GetPath()
        self.model.impZones(longName,self.tradinverse(str(item.GetText())))
        
    def OnExportResultat(self,evt):
        id = evt.GetId();
        item = self.gui.menuBarre.FindItemById(id);
        nom=self.tradinverse(str(item.GetText()));self.model.export(nom)

    def OnCalcOpt(self,evt):
        """permet de fixer un certain nombre d'options du programme"""
        lst = self.model.getParm('calcOpt','')
        dialg = MyDialogs.MyGenericCtrl(self.gui,'options',lst)
        retour = dialg.ShowModal()
        if retour == wx.ID_OK:
            lst2 = dialg.GetValues();
            self.model.setParm('calcOpt','',lst2)
            bool=(lst2[1][1][0]=='oui')  # DUAL PORO
            self.gui.parametresGui.setDualPoro(bool)
        dialg.Destroy()

    def OnVisuOpt(self,evt):
        """permet de fixer un certain nombre d'options du programme"""
        lst = self.model.getParm('visuOpt','')
        dialg = MyDialogs.MyGenericCtrl(self.gui,'options',lst)
        retour = dialg.ShowModal()
        if retour == wx.ID_OK:
            lst2 = dialg.GetValues();
            self.model.setParm('visuOpt','',lst2)
            self.model.visu.redraw()
        dialg.Destroy()

    def OnModflowOpt(self,evt):
        """allow to set some modflow parameters"""
        lst = self.model.getParm('Ecoulement','options')
        dlg = MyDialogs.MyGenericCtrl(self.gui,'Modflow options',lst)
        retour = dlg.ShowModal();
        if retour == wx.ID_OK:      
            lst2 = dlg.GetValues();self.model.setParm('Ecoulement','options',lst2)
        dlg.Destroy()
    def OnMt3dmsOpt(self,evt):
        """allow to set some mt3dms parameters"""
        lst = self.model.getParm('Transport','options');print lst
        dlg = MyDialogs.MyGenericCtrl(self.gui,'Mt3dms options',lst)
        retour = dlg.ShowModal();
        if retour == wx.ID_OK:      
            lst2 = dlg.GetValues()
            dlg.Destroy()
            if lst2[0][1][0]=='multiple':
                if type(lst[1][1])==type((5,6)): lstin=lst[1][1]*1
                else : lstin=['all '+str(lst[1][1])]
                dlg=MyDialogs.MyListDialog(self.gui,'multiple diffusion',lstin)
                retour = dlg.ShowModal();
                if retour == wx.ID_OK:
                    lstout=dlg.GetStrings()
                    lst2[1]=('Diffusion coeff (m2/s)',tuple(lstout))
            print lst2
            self.model.setParm('Transport','options',lst2)        
        dlg.Destroy()
        
    def OnPht3dOpt(self,evt):
        """allow to set some pht3d parameters"""
        lst = self.model.getParm('PHT3D','options')
        dlg = MyDialogs.MyGenericCtrl(self.gui,'Pht3d options',lst)
        retour = dlg.ShowModal();
        if retour == wx.ID_OK:      
            lst2 = dlg.GetValues(); self.model.setParm('PHT3D','options',lst2)
        dlg.Destroy()
                                                                       
    def OnImportData(self,evt):
        """import d'un fichier de type texte"""
        dlg = wx.FileDialog(self.gui,self.traduit('Ouvrir'),"","","*.txt",wx.OPEN)
        retour = dlg.ShowModal();
        if retour == wx.ID_OK:            
            fullName = dlg.GetPath()
            dicData = self.model.openTabFile(fullName)
            self.model.setBase('Data',dicData)
            self.model.doAction('Data','Data')
            self.OnMessage("Fichier donnees importe")
    def OnImportSolutions(self,evt):
        """import d'un fichier de type texte"""
        dlg = wx.FileDialog(self.gui,self.traduit('Ouvrir'),"","","*.txt",wx.OPEN)
        retour = dlg.ShowModal();
        if retour == wx.ID_OK:            
            fullName = dlg.GetPath()
            dicData = self.model.openTabFile(fullName)
            self.model.setChemSolutions(dicData)
            self.OnMessage("Fichier donnees importe")
            
    def OnGrapheXY(self,evt):
        """permet de fair eune graphe xy de la vairable representee et des
        donnees"""
        dicData=self.model.getBase('Data');
        groupe, nom, obj = self.visu.getCurrentVisu();#print groupe,nom
        nom = nom.split('_')[-1]
        # recupere les coords des forages et data mesures
        lZone=self.model.Aquifere.getZoneList('Forages')
        nF = len(lZone);mesu=[];lxy=[]  # nb forages dans interface
        if (len(dicData['cols'])!=0)and(nom in dicData['cols']):
            iC=dicData['cols'].index(nom);n=0
            for z in lZone:
                nomF=z.getNom()
                if nomF in dicData['lignes']:
                    n += 1;iR = dicData['lignes'].index(nomF)
                    mesu.append(dicData['data'][iR,iC])
                    lxy.append(z.getXy()[0]);
        else :
            self.OnMessage("pas de donnees");return
        # recupere les donnees simulees (vue actuelle)
        calc = [];
        if len(obj)>=2:  # objet de type contour
            for xy in lxy:
                i,j=self.getIndexPt(xy,obj) # coord du forage ds grille
                calc.append(obj[2][i,j]) # obj contient x,y,z
        self.plt=MyDialogs.plotxy(self.model.gui,-1);self.plt.Show(True)
        self.plt.draw(mesu,calc,nom,"Comparaison", "mesure", "calcul",'+')

    def OnAide(self,evt): #,lang):
        """appelle l'aide"""
        uDir = self.gui.mainDir
        if self.gui.LANG=="fr": os.startfile(uDir+os.sep+"iPht3dDoc_Fr.chm")
        if self.gui.LANG=="en": os.startfile(uDir+os.sep+"iPht3dDoc_En.chm")
        
    def OnVideo(self,evt):
        id = evt.GetId();item = self.gui.menuBarre.FindItemById(id)
        num=int(str(item.GetText())[5]);#os.chdir('utils')
        uDir = self.gui.mainDir
        if num==1: web.open(uDir+os.sep+'utils'+os.sep+'Tuto1.htm')
        elif num==2: web.open(uDir+os.sep+'utils'+os.sep+'zones.htm')
        os.chdir('..')

    def OnDownload(self,evt):
        dirutil=self.gui.mainDir+os.sep+'utils'
        dirlib=self.gui.mainDir+os.sep+'ilib'
        lf=os.listdir(dirutil)
        if 'newlib.zip' in lf:
            os.system('copy '+dirutil+os.sep+'newlib.zip '+dirutil+os.sep+'oldlib.zip')
        f2=dirutil+os.sep+'newlib.zip'
        lb=url.urlretrieve('http://www.pht3d.org/ipht3d/iliblast.zip',f2)
        zin=zp.ZipFile(f2,'r')
        zin.extractall(dirlib)
        for n in os.listdir(dirlib):
            if '.gif' in n: os.system('move '+dirlib+os.sep+n+' '+dirutil)
        self.OnMessage('lib changed, iPht3D will stop, then restart')
        self.gui.Destroy()
        
    def OnBackVersion(self,evt):
        dirutil=self.gui.mainDir+os.sep+'utils'
        lf=os.listdir(dirutil)
        if 'oldlib.zip' not in lf: self.OnMessage('sorry no old lib')
        zin=zp.ZipFile(dirutil+os.sep+'oldlib.zip','r')
        zin.extractall(self.gui.mainDir+os.sep+'ilib')
        self.OnMessage('lib changed, iPht3D will stop, then restart')
        self.gui.Destroy()

