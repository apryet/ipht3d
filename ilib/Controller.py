import wx

class Controller:
    """Classe qui permet de controler le lien entre les differents composants
    vue, fenetre parametres, visu, modele"""

    def __init__(self,gui):
        self.gui = gui
        self.model = gui.model
        self.menus = gui.menuBarre
        self.visu = gui.Visu
        self.zoneBox = gui.zoneBox
        self.modifBox = gui.modifBox
        self.parametresGui = gui.parametresGui
        self.afficheTree = gui.afficheTree
        self.OnMessage,self.OnRepondre = gui.OnMessage,gui.OnRepondre
        ## variables locales
        self.ZoneEnable,self.ZoneTEnable = 0,0
        #self.etat = ''
        self.groupes = self.model.groupes
        self.setOptions();#self.setupBoites();

    def valide(self,groupe,nom):
        """classe permettant de valider les donnees et etat du systeme
        avant de faire un calcul"""
        # tester si variable selectionnee avant dessinner zone
        if (groupe=='Ecoulement')and(nom=='Run'):
            if self.model.getProjectName()=='':
                self.OnMessage('Veuillez sauver le projet avant le calcul')
                return 'Stop'
            if self.model.Aquifere.getVbase('Mur')>self.model.Aquifere.getVbase('Toit'):
                self.OnMessage('Mur > Toit !!')
                return 'Stop'                
            #tester si presence de zones dan spotentiel??
        if (groupe=='PHT3D')and(nom=='Chemistry'):
            if self.model.PHT3D.Base['Chemistry']['Solutions']==None:
                self.OnMessage('importez la base de donnees')
                return 'Stop'                

    def majour(self,groupe,nom,text):
        """classe permettant de mettre a jour l'interface apres une aciton"""
        nomv = self.parametresGui.getCurrentVar()
        if groupe=='Aquifere': # attention ne pas changer etat si uniqut regarder donnees
            if nom=='Type':
                self.setOptions();#self.setupBoites()  # on ne doit pas modifier les calculs faits
                l0=self.model.getParm('Aquifere','Milieux')[1] # modif paramgui
                self.parametresGui.setList('Modele','Milieux',l0);
                l1=self.model.getParm('Aquifere','Couches')[1] # modif visu
                self.afficheTree.setNames('Aquifere_Couche_L',l1);
                if self.model.Aquifere.getDim()=='2D':
                    #self.parametresGui.boutonVisible('Aquifere_Milieux',False)
                    self.afficheTree.boutonVisible('Aquifere_Plan_L',False)
                else:
                    #self.parametresGui.boutonVisible('Aquifere_Milieux',True)
                    self.afficheTree.boutonVisible('Aquifere_Plan_L',True)
                return
##            elif ((nom=='ValBase')or(self.etat=='')):
##                self.etat='Aquifere';self.model.setEtat('Aquifere');self.setupBoites()
            elif nom=='ValBase':
                var=self.parametresGui.currentVar
                self.model.tmpImport[var]=''
            elif nom=='Grille' or nom=='GriVar':
                a=self.model.Aquifere.getNbCouches();laylist=range(a)
                self.afficheTree.setNames('Aquifere_Couche_L',laylist);
        if groupe=='Top' and nom=='zoneStart':
            self.panelsEnable(False);self.gui.onNotify('click-droit pour arreter')
        if groupe=='Top' and nom=='zoneEnd':
            self.panelsEnable(True);self.gui.onNotify('')
            self.modifBox.updateChoice2OnChange(nomv,self.parametresGui.getCurrentMil())
        if groupe=='Ecoulement' and (nom=='Temps' or nom=='Run'):
            tlist=self.model.Ecoulement.getListTemps();
            self.afficheTree.setNames('Aquifere_Tstep_L',tlist[1:]);
##        if groupe in ['Ecoulement','PHT3D'] and nom[:3]=='Run':
##            self.etat=groupe;self.model.setEtat(groupe);self.setupBoites()
        if groupe=='Data':
            self.afficheTree.boxVisible('Data',True)
        if nom=='Carte':
            self.afficheTree.OnSetItem('Aquifere','Carte','B',True)
        if nom in ['Variable','Milieux']:
            self.modifBox.updateChoice2OnChange(nomv,self.parametresGui.getCurrentMil())
        if nom=='Particule':
            self.afficheTree.onTickBox('Ecoulement','Particules','B',True)
        if nom in ['ZoneT','ZoneP','ZoneO']:
            self.modifBox.updateChoice2OnChange(nomv,self.parametresGui.getCurrentMil())
        self.visu.delZone("Profil",0) #to remove profile line after seen
        #message 
        self.OnMessage(text)

    def setOptions(self):
        self.options = self.model.getParm('Aquifere','Type')[2:]
        
    def panelsDisable(self):
        self.parametresGui.Disable();self.afficheTree.Disable()
        self.zoneBox.Disable();self.modifBox.Disable()
    def panelsEnable(self,bool):
        self.parametresGui.Enable(bool);self.afficheTree.Enable(bool)
        self.zoneBox.Enable(bool);self.modifBox.Enable(bool)
