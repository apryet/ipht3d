import wx
from iPht3dModel import *
from Visualisation import *
from visuGui import *
from parametresGui import *
from TopBar import *
from Controller import *
import MyDialogs
from Menus import *
from Addins import *
import os
from langue import *

class iPht3dGui(wx.Frame):
    ID_CHRONIQUE = 122
    ID_PROFIL = 123
    ID_OPTIONS = 125
    ID_RT3D = 126
    
    def __init__(self,titre,lang="fr"):
        wx.Frame.__init__(self, None, 1, title = titre, style = wx.DEFAULT_FRAME_STYLE)
        self.Maximize(True)
        self.titre = titre;self.demo=False
        self.icones = self.creerIcones()
        self.mainDir = os.getcwd()
        self.model = iPht3dModel(self,self.mainDir)
        self.lg = langue() #dico contient les mots et leur traduction
        self.invdico = dict()
        for i in self.lg.dict.iteritems(): self.invdico[i[1][0]]=i[0]  # dictionneir inverse
        self.LANG = lang # nom de la langue

        self.creerPanelMatplotlib()
        self.creerTopBar()
        self.creerPanelParametres()
        self.creerPanelAffiche()
        self.creerMenus()
        
        self.afficheSizer = wx.BoxSizer(wx.VERTICAL)
        self.afficheSizer.Add(self.affiche,0,wx.EXPAND)

        frameSizer = wx.BoxSizer(wx.HORIZONTAL)
        frameSizer.Add(self.paramSizer, 12, wx.EXPAND)
        frameSizer.Add(self.matplot, 76, wx.EXPAND)
        frameSizer.Add(self.afficheSizer, 15, wx.EXPAND)

        globalSizer = wx.BoxSizer(wx.VERTICAL)
        globalSizer.Add(self.barSizer,4)
        globalSizer.Add(frameSizer, 96,wx.EXPAND)
        
        globalSizer.SetSizeHints(self)
        self.SetSizer(globalSizer)
        self.control = Controller(self)
        wx.EVT_CLOSE(self,self.OnExit)

    def traduit(self,mot):
        mot2 = []
        if self.LANG == 'fr': return mot
        if type(mot)==type('abc') :
            return self.lg.getMot(mot)  # pour l'instant que anglais donc pas choix
        else:
            for m in mot : mot2.append(self.lg.getMot(m)) # pour des listes
            return mot2

    def tradinverse(self,mot):
        if self.invdico.has_key(mot):
            return str(self.invdico[mot])  # pour l'instant que anglais donc pas choix
        else : return mot
        
    def OnRepondre(self,texte):
        texte = self.traduit(texte)
        message = wx.MessageDialog(self, texte,"Attention",style = wx.ICON_INFORMATION|wx.CENTRE|wx.OK|wx.CANCEL)
        retour = message.ShowModal()
        message.Destroy()
        return retour
    
    def OnMessage(self,text):
        if text==None: return
        text = self.traduit(text)
        if type(text)==type('ab'):
            w=max(len(text)*5,80);h=1;text=[text]
        elif type(text)==type([3,4]):
            h=len(text);w=80
            for i in range(len(text)): w=max(w,len(text[i])*5)
        dlg = wx.Dialog(self, -1, "",size=(min(w+30,450),h*30+80));
        dlgSizer = wx.BoxSizer(wx.VERTICAL)
        for i in range(len(text)):
            dlgSizer.Add(wx.StaticText(dlg,-1,text[i]))
        dlgSizer.Add(dlg.CreateButtonSizer( wx.OK ), -1, wx.ALIGN_BOTTOM|wx.ALIGN_CENTER)
        dlg.SetSizer(dlgSizer);dlg.ShowModal();dlg.Destroy()

    ####################################################
    #                   creer menus
    ####################################################
    def creerMenus(self):
        self.menus = Menus(self)
        #file menu
        menuFichier = wx.Menu()
        menuFichier.Append(wx.ID_NEW,"&"+self.traduit('Nouveau')+"\tCTRL+n")
        menuFichier.AppendSeparator()
        menuFichier.Append(wx.ID_OPEN, "&"+self.traduit('Ouvrir')+"\tCTRL+o")
        menuFichier.Append(wx.ID_SAVE, "&"+self.traduit('Enregistrer')+"\tCTRL+s")
        menuFichier.Append(wx.ID_SAVEAS, "&"+self.traduit('Enregistrer sous'))
        menuFichier.AppendSeparator()
        menuFichier.Append(wx.ID_EXIT, "&"+self.traduit('Quitter')+"\tCTRL+q")

        wx.EVT_MENU(self, wx.ID_NEW, self.menus.OnNew)
        wx.EVT_MENU(self, wx.ID_OPEN, self.menus.OnOpen)
        wx.EVT_MENU(self, wx.ID_SAVE, self.menus.OnSave)
        wx.EVT_MENU(self, wx.ID_SAVEAS, self.menus.OnSaveAs)
        wx.EVT_MENU(self, wx.ID_EXIT, self.OnExit)

        listeVar=self.model.Aquifere.getParm('Variable')[1]
        listeVar.extend(['Transport','Tr_Rech','PHT3D','PH_Rech','Observation'])
        
        # Import
        menuImport = wx.Menu()
        submenu = wx.Menu()
        for i in range(len(listeVar)):
            id=submenu.Append(-1,self.traduit(listeVar[i]))
            self.Bind(wx.EVT_MENU, self.menus.OnImportVar,id)
        menuImport.AppendMenu(710, "Grid",submenu)
        submenu = wx.Menu()
        for i in range(len(listeVar)):
            id=submenu.Append(-1,self.traduit(listeVar[i]))
            self.Bind(wx.EVT_MENU, self.menus.OnImportZones,id)
        menuImport.AppendMenu(730, "Zones",submenu)
        id=menuImport.Append(-1,self.traduit('Donnees'))
        self.Bind(wx.EVT_MENU,self.menus.OnImportData,id)
        id=menuImport.Append(-1,self.traduit('Solutions'))
        self.Bind(wx.EVT_MENU,self.menus.OnImportSolutions,id)
        #Export
        menuExport = wx.Menu()
        submenu = wx.Menu()
        for i in range(len(listeVar)):
            submenu.Append(751+i,self.traduit(listeVar[i]))
        menuExport.AppendMenu(750, "Variables",submenu)
        menuExport.Append(771, self.traduit("Vitesses"))
        menuExport.Append(772, "Transport")
        menuExport.Append(773, "PHT3D")
        for i in range(len(listeVar)):
            wx.EVT_MENU(self, 751+i, self.menus.OnExportResultat)
        for i in range(771,774):
            wx.EVT_MENU(self, i, self.menus.OnExportResultat)

        #Outils
        menuOutils = wx.Menu()
        oc=menuOutils.Append(-1, "Options calcul")
        ov=menuOutils.Append(-1, "Options Visu")
        of=menuOutils.Append(-1,"Options Modflow")
        omt=menuOutils.Append(-1,"Options Mt3dms")
        opht=menuOutils.Append(-1,"Options Pht3d")
        oim=menuOutils.Append(-1, self.traduit("Import Donnees"))
        self.Bind(wx.EVT_MENU,self.menus.OnCalcOpt,oc)
        self.Bind(wx.EVT_MENU,self.menus.OnVisuOpt,ov)
        self.Bind(wx.EVT_MENU,self.menus.OnModflowOpt,of)
        self.Bind(wx.EVT_MENU,self.menus.OnMt3dmsOpt,omt)
        self.Bind(wx.EVT_MENU,self.menus.OnPht3dOpt,opht)
        self.Bind(wx.EVT_MENU,self.menus.OnImportData,oim)
    #Add-ins
        self.menuAddins = wx.Menu()

        #Aide
        menuAide = wx.Menu()
        if self.LANG=="fr":menuAide.Append(131, "Aide")
        if self.LANG=="en":menuAide.Append(131, "Help")
        wx.EVT_MENU(self, 131, self.menus.OnAide)
##        menuAide.Append(132,"Video1 Tutorial")
##        menuAide.Append(133,"Video2 Zones")
##        wx.EVT_MENU(self, 132, self.menus.OnVideo)        
##        wx.EVT_MENU(self, 133, self.menus.OnVideo)        
        menuAide.Append(133,"&Donwload new")
        wx.EVT_MENU(self, 133, self.menus.OnDownload)
        menuAide.Append(134,"&Back to old")
        wx.EVT_MENU(self, 134, self.menus.OnBackVersion)
        self.menuBarre = wx.MenuBar()
        
        self.menuBarre.Append(menuFichier, "&"+self.traduit('Fichier'))
        self.menuBarre.Append(menuImport, "&Import")
        self.menuBarre.Append(menuExport, "&Export")
        self.menuBarre.Append(menuOutils, "&"+self.traduit('Outils'))
        self.menuBarre.Append(self.menuAddins, "&Add-in")
        self.menuBarre.Append(menuAide, "&?")
        self.SetMenuBar(self.menuBarre)
        addin=Addins(self)
        addin.build()

    def enableMenu(self,nomM,bool):
        id=self.menuBarre.FindMenu(nomM)
        if id!=-1:self.menuBarre.EnableTop(id,bool)  # pour les griser
                               
    def OnExit(self,evt):
        self.menus.askSave(evt)
        self.Destroy()

    #####################################################
    #                   Panel Matplotlib
    ######################################################
    def creerPanelMatplotlib(self):

        #initialisation de la visualisation
        self.Visu = Visualisation(self, self.model.Aquifere.getVarList())
        sizerVisu = wx.BoxSizer(wx.VERTICAL)

        #ajout d'un item avec une proportion dans le sizer (95% et 5% ici) avec comme flag wxExpand
        sizerVisu.Add(self.Visu, 95, wx.EXPAND)
        basSizer = wx.BoxSizer(wx.HORIZONTAL)
        basSizer.Add(self.Visu.GetToolBar(),0)
        self.pos = wx.StaticText(self,-1,' x: y:',size=(100,40))
        self.pos.SetOwnBackgroundColour('LIGHT GRAY')
        basSizer.Add(self.pos,5,wx.EXPAND)
        self.notify = wx.StaticText(self,-1,'')
        font = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
        self.notify.SetFont(font)
        self.notify.SetOwnForegroundColour('RED')
        basSizer.AddSpacer((0, 5), 0)
        basSizer.Add(self.notify,5,wx.EXPAND)
        sizerVisu.Add(basSizer, 5,wx.EXPAND)
        self.matplot = sizerVisu
        self.model.setVisu(self.Visu)
        self.Visu.setVisu(self.model,self.model.getGlist())

        # On Windows, default frame size behaviour is incorrect
        # you don't need this under Linux
        #tw, th = self.Visu.GetToolBar().GetSizeTuple()
        #fw, fh = self.Visu.GetSizeTuple()
        #self.Visu.GetToolBar().SetSize(wx.Size(fw, th))
        
    def getModel(self): return self.model
    def getVisu(self): return self.Visu
    def onNotify(self,text): self.notify.SetLabel(text)
    def onPosition(self,text): self.pos.SetLabel(text)
    # affiche le titre ainsi que le path complet du projet
    def updateTitle(self):
        self.SetTitle(self.titre + " - " + self.model.getProjectName())
        
    #####################################################
    #                   Panel Top et Parametres
    #####################################################
    def creerTopBar(self):
        self.barSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.zoneBox = zoneBox(self)
        self.barSizer.Add(self.zoneBox, 0)
        self.barSizer.Add(wx.StaticLine(self,-1), 0, wx.ALIGN_CENTER|wx.EXPAND)
        self.modifBox = modifBox(self)
        self.barSizer.Add(self.modifBox, 0)

    def creerPanelParametres(self):
        #Creation des differents Panels
        self.paramSizer = wx.BoxSizer(wx.VERTICAL)
        self.parametresGui = parametresGui(self,self.model)
        self.paramSizer.Add(self.parametresGui)
    #####################################################
    #                   Panel Vue
    #####################################################
    def creerPanelAffiche(self):
        self.afficheTree = visuGui(self, self.model)
        self.affiche = wx.BoxSizer(wx.VERTICAL)
        self.affiche.Add(self.afficheTree, -1, wx.EXPAND)

    ######################## ICONES ############################
    import sys
    os.path.join(os.path.dirname(sys.executable), 'utils')
    def creerIcones(self):
        noms=['blanc','bBleu','Mo_zList',
              'Mo_Carte','Mo_Domaine','Mo_Grille','Mo_GriVar','Mo_Unites',
              'Aq_Zone','Aq_layLock','Aq_layUnlock',
              'Top_Point','Top_Ligne','Top_Rect','Top_Poly','Top_PolyV',
              'Top_Interp','Top_move','Top_modifPoly','Top_modifPolyRed','Top_supprime',
              'Top_zoneLay','Top_Histo','Top_supprimeAll',
              'Ec_SolvListe','Ec_Solver','Ec_Temps','Ec_Write','Ec_Run','Ec_Particule',
              'Tr_ZoneT','Tr_Transp','Tr_Temps','Tr_Methodes','Tr_Recharge',
              'Tr_Solver','Tr_Particules','Tr_Write','Tr_Run',
              'PH_Import','PH_Chemistry','PH_ZoneP','PH_Write','PH_Run',
              'PH_PHparm','PH_Recharge','PH_Immobile','PH_ImmobileDisable',
              'Ob_ZoneO',
              'Vis_OriX','Vis_OriY','Vis_OriZ','Vis_SwiImg','Vis_SwiCont']
        dIcones = {}
        for n in noms:
            img = 'utils'+os.sep+ n+'.gif'
            dIcones[n] = wx.Bitmap(img, wx.BITMAP_TYPE_GIF)
        return dIcones

            
