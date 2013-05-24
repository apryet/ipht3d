#import matplotlib
#matplotlib.use('WX')
from matplotlib.backends.backend_wx import Toolbar, StatusBarWx, FigureCanvasWx
from matplotlib.backends.backend_wx import FigureManager, NavigationToolbar2Wx
# on cree un FigureCanvasWxAgg et non un FigureCanvasWx
# car sinon l'affichage de la carte de fond ne marche pas
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.artist import Artist
from matplotlib.axes import Subplot
from matplotlib import rcParams
import matplotlib.pylab as pl
from matplotlib.mlab import dist_point_to_segment
from matplotlib.patches import RegularPolygon,Polygon
from matplotlib.lines import Line2D
from matplotlib.collections import PolyCollection,LineCollection

#pour l'affichage d'une carte de fond
import matplotlib.image as Im
import matplotlib as mpl
import time
import wx
#import iphtC1

from scipy import *
from scipy.interpolate import interp1d
import numpy.ma as ma

from Aquifere import Zone
import MyDialogs

def smoo(v):
    """ fonction qui permet de lisser une matrice par des moyennes mobiles"""
    [l,c] = shape(v)
    v1 = concatenate([v[:1,:],(v[:-2,:]+v[1:-1,:]+v[2:,:])/3,v[l-1:l,:]],axis=0)
    v2 = concatenate([v1[:,:1],(v1[:,:-2]+v[:,1:-1]+v1[:,2:])/3,v1[:,c-1:c]],axis=1)
    return v2

"""
classe representant un objet graphique qui sera ajoute aux axes (a l'objet Axes
du canvas en fait)
type : type de l'objet graphique, pour une zone le type est dans la liste de
    constante listeNomZone de Visualisation, sinon c'est une string, 'imshow'
    pour une image par exemple ou 'grille', 'contour'
object : l'objet graphique en lui-meme cree par python
visible : booleen qui indique si l'objet est visible (True) ou non (False)
color : couleur ou ensemble de couleurs de l'objet graphique
"""
class GraphicObject:
    def __init__(self, typ, obj, visible, color):
        self.type = typ
        self.object = obj
        self.name = ''
        self.color = color  # dictionnaire de proprietes
        self.data = None
        self.visible = visible
        
    # Accesseurs
    def getType(self): return self.type    
    def getObject(self): return self.object    
    def getColor(self): return self.color
    def getData(self): return self.data
    def getVisible(self): return self.visible
    
    #Mutateurs
    def setType(self, typ): self.type = typ    
    def setObject(self, obj): self.object = obj    
    def setColor(self, color): self.color = color
    def setData(self,data): self.data = data
    def setVisible(self,bool):
        obj = self.object;self.visible=bool
        if type(obj)==type([1,2]) : # cas liste
            for j in range(len(obj)):
                obj[j].set_visible(bool)
        else: # cas classique
            obj.set_visible(bool)                
        
#/////////////////////////////////////////////////////////////////////
class Visualisation(FigureCanvasWxAgg):

    def __init__(self,parent,tuplNomVar):
    
        self.fig = pl.figure() #(9,8), 90)
        FigureCanvasWxAgg.__init__(self, parent, -1, self.fig)
        self.xlim, self.ylim, self.dataon = (), (),False
        #ion()  #pour faire animation??
                
        # c'est la GUI e tle modele
        self.parent = parent
        self.model = parent.model
        self.traduit = parent.traduit;self.tradinverse=parent.tradinverse
        # liste de GraphicObject selon les types
        self.listeObject = []        
        # polygone d'interaction sur une zone (pour pouvoir la modifier)
        self.polyInteract = None
        
        # liste de variables, sert pour la GUI et le combobox sur les variables
        self.listeNomVar = list(tuplNomVar);
        self.listeNomVar.extend(['PHT3D','Transport','Observation','Tr_Rech','PH_Rech']);  
        self.curVar,self.curContour = None,'Charge' # variable courante selectionne       
        self.curLayer,self.curOri, self.curPlan,self.curGroupe=0,'Z',0,None
        # liste des types de zones (des constantes)
        self.listeNomZone = [Zone.POINT,Zone.LIGNE,Zone.RECT,Zone.POLY,Zone.POLYV]
        # variable pour savoir si on est en cours de tracage d'une zone
        self.typeZone = -1
        
        # coordonnees et zone de la zone que l'on est en train de creer
        self.curZone = None  # objet graphique (ligne, point, rect..)
        self.x1, self.y1 = [], []
        self.tempZoneVal = []  # liste de valeurs pour polyV
        self.calcE=0;self.calcT=0;self.calcR=0; # dit si calcule effectue ou non
        
        # dictionnaire qui est compose des variables de l'Aquifere
        # a chaque variable est associe une liste de zones
        self.listeZone, self.listeZoneText, self.listeZlayer = {},{},{}
        for i in range(len(self.listeNomVar)):
            #print self.listeNomVar[i]
            self.listeZone[self.listeNomVar[i]] = []
            self.listeZoneText[self.listeNomVar[i]] = []
            self.listeZlayer[self.listeNomVar[i]] = []

        # toolbar de la visu, de type NavigationToolbar2Wx
        self.toolbar = NavigationToolbar2Wx(self)
        self.toolbar.Realize()
        # ajout du subplot a la figure
        self.cnv = self.fig.add_axes([.05,.05,.9,.88]) #left,bottom, wide,height     
        self.toolbar.update()    
        self.pos = self.mpl_connect('motion_notify_event', self.onPosition)
    #####################################################################
    #                     Divers accesseur/mutateurs
    #####################################################################
    
    def GetToolBar(self):return self.toolbar
    def getcurVisu(self): return [self.curGroupe,self.curNom,self.curObj]
    def onPosition(self,evt):
        self.parent.onPosition(' x: '+str(evt.xdata)[:6]+' y: '+str(evt.ydata)[:6])
    # methode d'ajout d'un GraphicObject a la VISUALISATION (pas le canvas !)
    def addGraphicObject(self, gObject):
        """permet d'ajouter un objet ou une liste d'objet graphique qui on
        un type contour, particules..."""
        typO = gObject.getType()
        if typO in self.listeNomZone:
            # ajout du GraphicObject dans la liste de zones de la variable qu'il faut
            lay = gObject.getData()
            if self.listeZone.has_key(self.curVar) :
                self.listeZone[self.curVar].append(gObject)
            else :
                self.listeZone[self.curVar] = [gObject]
            self.listeZlayer[self.curVar].append(lay)
        elif typO == 'zoneText':
            if self.listeZoneText.has_key(self.curVar) :
                self.listeZoneText[self.curVar].append(gObject)
            else :
                self.listeZoneText[self.curVar] = [gObject]
        elif typO == 'data':
            self.listeZoneText['data']=(gObject)
        else :
            obj = self.getObjFromType(typO);
            if obj==None: self.listeObject.append(gObject)  # type obj n'existe pas
            else:
                self.listeObject.pop(self.listeObject.index(obj))
                self.listeObject.append(gObject)               

    def delGraphicObject(self, typO):
        for obj in self.listeObject:
            if obj.getType()== typO :
                self.listeObject.pop(self.listeObject.index(obj))

    def getObjFromType(self,typO):
        for obj in self.listeObject:
            if obj.getType()== typO : return obj
        return None
        
    def delAllObjects(self):
        for v in self.listeZone:
            self.listeZone[v]=[]
            self.listeZoneText[v]=[]                
        self.listeObject=[]
        self.cnv.lines=[]
        self.cnv.collections = []
        self.cnv.artists = []
        self.cnv.images = []
        self.cnv.cla()
        self.draw()
        
    def setVisu(self, model, Glist):
        """creer les objets graphiques a partir des caracteristiques d'un modele
        importe.
        creer les zones avec setAllzones, puis le contour et les vecteurs ecoult,
        les lignes etle contour pour tracer, contour pour reaction
        depend de l'etat du systeme de la liste graphique
        comme ca tout ca pourra etre visualise sans faire de nouveau calcul
        """
        self.delAllObjects();self.start=time.time()
        self.setAllZones(model.getParm('Aquifere','Zones'))
        self.initDomain()
        self.drawGrid(Glist['Aquifere']['Grille']['calc'])
        self.Glist = Glist
        self.draw()
    def setDataOn(self,bool):
        """definit l'affichage ou non des donnees qaund contour"""
        self.dataon=bool
        
    def redraw(self):
        self.cnv.set_xlim(self.xlim)
        self.cnv.set_ylim(self.ylim)
##        if self.model.getOptEchelle():
##            pl.axis('scaled');# axis('tight')
##        else : pl.axis('normal')
        self.draw()

    def changeTitre(self,titre):
        s='';ori=self.curOri
        if ori in ['X','Y','Z']:
            plan=self.curPlan;
            x1,y1 = self.model.Aquifere.getXYticks()
            zl = self.model.Aquifere.getParm('zList')
        if ori=='Z': s=' Z = '+ str(zl[plan])
        if ori=='X': s=' X = '+ str(x1[plan])
        if ori=='Y': s=' Y = '+ str(y1[plan])
        pl.title(self.traduit(str(titre))+s[:9],fontsize=20)

    def showObject(self,obj,typObj,groupe,nomIn,tag,temps,plan,ori):
        """ a partir d'un objet obtenu dans le model et de son type, on dessine
        dans la vue cet objet. On peut afficher les donnees lies a cet objet
        quand on affiche les contours. tag : ds le cas d'une checkbox nom de la variable
        nomIn : si une liste nom dans la liste."""
        self.curObj= obj;self.curTypImg='Contour'
        if groupe!='Aquifere': self.curGroupe= groupe
        if self.listeZoneText.has_key('data'):
            for z in self.listeZone['Forages']: z.setVisible(False)
            for z in self.listeZoneText['data']: z.setVisible(False)  # enlever les donnees presentes
        if type(tag)==type(True):  # case list of choice
            self.curNom = nom = nomIn; bool = tag
        else :  # case of simple case checkbox
            self.curNom = nom = tag; bool=True

        if nom in ['Particules','Vitesse']:
            val = self.model.getGlistParm(groupe,nom,'valeur')
            col = self.model.getGlistParm(groupe,nom,'col')
        else:
            val = self.model.getGlistParm(self.curGroupe,self.curContour,'valeur')
            col = self.model.getGlistParm(self.curGroupe,self.curContour,'col');#print 'show val col',val,col

        if typObj=='Grille': self.drawGrid(bool)
        elif typObj=='Image':
            if nom=='Carte': # for maps
                if bool: self.createMap(obj);
                else : self.drawMap(bool)
            elif nom=='ZoneImg': # for zoneImg 
                if bool: self.createZoneImg(obj);
                else : self.removeZoneImg()
            else:
                self.createZoneImg(obj[2]);#self.effaceContour();
                self.curContour=nom;self.curTypImg='Image'

        elif typObj=='Vecteur':
            if bool: self.createVecteur(obj[0],obj[1],obj[2],obj[3]);
            self.drawVecteur(bool)
            
        elif typObj=='Contour':
            if bool:
                self.coreContour(obj[0],obj[1],obj[2],'0',val,col); # nom -> 0
                self.curContour=nom;self.curTypImg='Contour'#self.changeTitre(nom)
            else: self.effaceContour()
            # rajouter donnees a visualiser
            dicData=self.model.getBase('Data');#print dicData,nom
            if (len(dicData['cols'])!=0)and (self.dataon) and bool:
                if nom in dicData['cols']:
                    iCol=dicData['cols'].index(nom)
                    self.showData(dicData['lignes'],dicData['data'][:,iCol])
            else : # effacer les donnees
                if self.listeZoneText.has_key('data'):
                    for z in self.listeZone['Forages']: z.setVisible(False)
                    for z in self.listeZoneText['data']: z.setVisible(False)  # enlever les donnees presentes

        elif typObj=='Particules': # particules 
            self.drawParticules(bool,valeur=val,col=col);

        elif typObj=='Couche': # changer de couche ou de temps
            self.changeAxesOri(ori,plan);self.curOri=ori;#self.changeTitre(nom)
            if ori!='Z': self.setUnvisibleZones()
            self.curPlan=plan
            # si contour, trouver obj contour ,dessiner
            #if self.curTypImg=='Contour':
            oc = self.getObjFromType('contour')
            #else : oc = self.getObjFromType('ZoneImg')
            if oc!=None: 
                obj=self.model.getObject(self.curGroupe,self.curContour,'',temps,plan,ori)
                oc.setData([obj[0],obj[1],obj[2]])
                #if self.curTypImg=='Contour':
                self.coreContour(obj[0],obj[1],obj[2],'0',val,col)
                #else : self.createZoneImg(obj[2])
            # si vecteur, trouver vecteur selon lay actuel,dessiner
            ov = self.getObjFromType('vecteur');#print ov
            if ov!=None:
                if ov.getVisible():
                    obj=self.model.getObject('Ecoulement','Vitesse','',temps,plan,ori)
                    self.createVecteur(obj[0],obj[1],obj[2],obj[3]);
                    self.drawVecteur(True)
                
    def changeObject(self,groupe,nom,valeur,col):
        if nom=='Grille':self.changeGrid(col)
        elif nom=='Particules': self.drawParticules(True,valeur=valeur,col=col)
        elif nom=='Vitesse': self.changeVecteur(valeur,col)
        elif nom=='Visible': self.changeData(valeur,col)
        else :self.changeContour(nom,valeur,col)
        
    #####################################################################
    #             Gestion de l'affichage de la grille/map
    #####################################################################
    # methode qui change la taille du domaine d'etude (les valeurs de l'axe 
    # de la figure matplotlib en fait) et la taille des cellules d'etude
    def initDomain(self):
        # changement de la valeur des axes
        grd = self.model.Aquifere.getFullGrid()
        self.xlim = (grd['x0'],grd['x1']);
        self.ylim = (grd['y0'],grd['y1']);
        p,= pl.plot([0,1],'b');self.transform=p.get_transform()
        obj = GraphicObject('grille', p, True, None)
        self.addGraphicObject(obj)
        self.changeDomain()
        
        # add basic vector as a linecollection
        dep=rand(2,2)*0.;arr=dep*1.;ech=1.;
        lc1 = LineCollection(zip(dep,arr));
        lc1.set_transform(self.transform);pl.setp(lc1,linewidth=.5);
        self.cnv.collections=[lc1];#self.cnv.add_patch(lc1);
        obj = GraphicObject('vecteur', lc1, False, None);
        obj.setData([dep,arr,ech]);self.addGraphicObject(obj)
        self.draw()

    def changeDomain(self):
        self.changeAxesOri('Z',0)
        
    def changeAxesOri(self,ori,plan):
        # change orientation de la visu
        #self.cnv.collections,self.cnv.artists = [],[]; # enlever contour actuel
        aqui = self.model.Aquifere;
        obj = self.getObjFromType('grille');p = obj.getObject()
        [grx,gry,xlim,ylim] = self.calcGrid(aqui,ori,plan);
        self.xlim,self.ylim=xlim,ylim         
        self.cnv.set_xlim(self.xlim);self.cnv.set_ylim(self.ylim)
        p.set_data(grx,gry);#self.drawGrid(True)
        self.draw()
        
    def calcGrid(self, aqui,ori,plan):
        xv,yv=aqui.getMesh(ori,plan);#print 'visu calcgr',shape(xv),shape(yv)
        xlim=(amin(amin(xv)),amax(amax(xv)))
        ylim=(amin(amin(yv)),amax(amax(yv)))
        xv1=xv[:,::-1]*1;xv1[::2,:]=xv[::2,:]*1
        xv2=transpose(xv);xv2=flipud(xv2)
        yv1=yv[::-1,:]*1;yv1[:,::2]=yv[:,::2]*1;
        yv2=transpose(yv1);yv2=flipud(yv2)
        grx=concatenate([reshape(xv2[:,::-1],(1,-1)),reshape(xv1,(1,-1))],axis=0);
        gry=concatenate([reshape(yv2[:,::-1],(1,-1)),reshape(yv,(1,-1))],axis=0) # yv ok
        return [grx,gry,xlim,ylim]

    # methodes d'affichage/suppression de grille
    def drawGrid(self, bool):
        obj = self.getObjFromType('grille')
        p = obj.getObject()
        p.set_visible(bool)
        self.redraw()
        
    def changeGrid(self,col):
        obj = self.getObjFromType('grille');p = obj.getObject()
        a=col.Get();col=(a[0]/255,a[1]/255,a[2]/255)
        p.set_color(col);
        self.redraw()
    #####################################################################
    #             Affichage d'une variable sous forme d'image
    #####################################################################
    # l'image se met en position 1 dans la liste des images
    def createMap(self, obj):
        mat=Im.imread(obj)
        org='upper';ext=(self.xlim[0],self.xlim[1],self.ylim[0],self.ylim[1])
        img=pl.imshow(mat,origin=org,extent=ext,aspect='auto',interpolation='nearest');
        self.cnv.images=[img] #
        self.cnv.images[0].set_visible(True)
        self.redraw()
        
    def drawMap(self, bool):
        self.cnv.images[0].set_visible(bool)
        self.redraw()

    def createZoneImg(self,obj):
        mat=obj;xt,yt=self.model.Aquifere.getXYticks()
        img=pl.pcolormesh(xt,yt,mat) #,norm='Normalize')
        obj = GraphicObject('ZoneImg', img, False, None)
        self.addGraphicObject(obj) # ne pas stocker zoneimage
        self.redraw()
    def removeZoneImg(self):
        obj = self.getObjFromType('ZoneImg')
        p = obj.getObject();p.set_visible(False);#self.delGraphicObject('ZoneImg')
        self.redraw()

    #####################################################################
    #             Gestion de l'affichage des contours
    #####################################################################
        
    def coreContour(self,X,Y,Z,typC,valeur,col):
        """ calcul des contour sa partir de valeur : valeur[0] : min
        [1] : max, [2] nb contours, [3] decimales, [4] : 'lin' log' ou 'fix',
        si [4]:fix, alors [5] est la serie des valeurs de contours"""
        self.cnv.collections=[];self.cnv.artists = []
        V = 11;Zmin=amin(amin(Z));Zmax=amax(amax(Z*(Z<1e5)));
        if Zmax==Zmin : # test min=max -> pas de contour
            #obj = GraphicObject('contour', Zmin, False, None)
            #obj.setData([X,Y,Z]);self.addGraphicObject(obj)
            self.parent.OnMessage(str(typC)+': valeurs toutes egales a '+str(Zmin))
            return
        if valeur == None : valeur = [Zmin,Zmax,(Zmax-Zmin)/10.,2,'auto',[]]
        # adapter le nombre et la valeur des contours
        val2=[float(a) for a in valeur[:3]]
        if valeur[4]=='log':  # cas echelle log
            n = int((log10(val2[1])-log10(max(val2[0],1e-4)))/val2[2])+1
            V = logspace(log10(max(val2[0],1e-4)),log10(val2[1]),n)
        elif (valeur[4]=='fix') and (valeur[5]!=None) : # fixes par l'utilisateur
            V = valeur[5]*1;V.append(V[-1]*2.);n=len(V)
        elif valeur[4]=='lin' :  # cas echelle lineaire
            n = int((val2[1]-val2[0])/val2[2])+1
            V = linspace(val2[0],val2[1],n)
        else : # cas automatique
            n=11;V = linspace(Zmin,Zmax,n)
        # ONE DIMENSIONAL
        r,c=shape(X);
        if r==1: 
            X=concatenate([X,X]);Y=concatenate([Y-Y*.45,Y+Y*.45]);Z=concatenate([Z,Z])
        Z2=ma.masked_where(Z.copy()>1e5,Z.copy());#print valeur,n,V
        # definir les couleurs des contours
        if (col==None): # or (col==[(0,0,0),(0,0,0),(0,0,0),10]):
            cf = pl.contourf(pl.array(X),pl.array(Y),Z2,V)
            c = pl.contour(pl.array(X),pl.array(Y),Z2,V)
            col=[(0,0,255),(0,255,0),(255,0,0),10]
        else :
            r,g,b=[],[],[];
            lim=((0.,1.,0.,0.),(.1,1.,0.,0.),(.25,.8,0.,0.),(.35,0.,.8,0.),(.45,0.,1.,0.),\
                 (.55,0.,1.,0.),(.65,0.,.8,0.),(.75,0.,0.,.8),(.9,0.,0.,1.),(1.,0.,0.,1.))
            for i in range(len(lim)):
                c1=lim[i][1]*col[0][0]/255.+lim[i][2]*col[1][0]/255.+lim[i][3]*col[2][0]/255.
                r.append((lim[i][0],c1,c1))
                c2=lim[i][1]*col[0][1]/255.+lim[i][2]*col[1][1]/255.+lim[i][3]*col[2][1]/255.
                g.append((lim[i][0],c2,c2))
                c3=lim[i][1]*col[0][2]/255.+lim[i][2]*col[1][2]/255.+lim[i][3]*col[2][2]/255.
                b.append((lim[i][0],c3,c3))
            cdict={'red':r,'green':g,'blue':b}
            my_cmap=mpl.colors.LinearSegmentedColormap('my_colormap', cdict, 256)
            cf = pl.contourf(pl.array(X),pl.array(Y),Z2,V, cmap=my_cmap)
            c = pl.contour(pl.array(X),pl.array(Y),Z2,V, cmap=my_cmap)

        for cl in cf.collections:
            cl.set_alpha(int(col[3])/100.);#print cl
        obj = GraphicObject('contour', [c,cf], False, None);
        obj.setData([X,Y,Z]);#obj.setVisible(True)
        self.addGraphicObject(obj);
        if valeur==None: fmt = '%1.3f' 
        else : fmt = '%1.'+ str(valeur[3])+'f'
        cl = pl.clabel(c,color='black',fontsize=9,fmt=fmt)
        obj = GraphicObject('contLabel', cl, False, None)
        self.addGraphicObject(obj)
        self.redraw()
            
    def changeContour(self,typC,valeur,col):
        """ modifie les valeurs d'un contour existant"""
        obj = self.getObjFromType('contour')
        if obj==None: return
        X,Y,Z = obj.getData()
        self.coreContour(X,Y,Z,typC,valeur,col)

    def effaceContour(self):
        self.cnv.collections=[];self.cnv.artists = []
        self.draw()
        #obj = self.getObjFromType('contour')
        #obj.setVisible(False)
    #####################################################################
    #             Gestion de l'affichage de vecteurs
    #####################################################################
    """vector has been created as the first item of lincollection list
    during domain intialization"""
    def createVecteur(self,X,Y,U,V,ech=1.,col=None):
        """ modifie les valeurs de vecteurs existants"""
        self.drawVecteur(False);#print shape(X),shape(Y),shape(U),shape(V)
        # new coordinates
        #vm = mean(median(median(U)),median(median(V)));
        #dmx = max(X[0,1]-X[0,0],Y[0,1]-Y[0,0]) 
        u, v = U, V #/vm*dmx*ech/2
        l=len(ravel(X))
        dep=concatenate([X.reshape((l,1)),Y.reshape((l,1))],axis=1)
        b=X+u;c=Y+v;
        arr=concatenate([b.reshape((l,1)),c.reshape((l,1))],axis=1)
        lc1 = LineCollection(zip(dep,arr));lc1.set_transform(self.transform)
        obj = GraphicObject('vecteur', lc1, False, None)
        obj.setData([dep,arr,ech])
        self.addGraphicObject(obj)
        if len(self.cnv.collections)>0:self.cnv.collections[0]=lc1
        else : self.cnv.collections=[lc1]
        self.redraw()

    def drawVecteur(self, bool):
        """ dessine les vecteurs vitesse a partir de x,y,u,v et du
        booleen qui dit s'il faut dessiner ou non """
        obj = self.getObjFromType('vecteur');
        if obj==None: return
        lc = obj.getObject();lc.set_visible(bool);obj.setVisible(bool)
        self.redraw()
        
    def changeVecteur(self,ech=1.,col=None):
        """ modifie les valeurs de vecteurs existants"""
        self.drawVecteur(False)
        if type(ech)==type((3,4)):
            if len(ech)>=1: ech=ech[0]
        # previous object
        obj = self.getObjFromType('vecteur')
        if obj==None: return
        #change coordinates
        dep,arr_old,ech_old = obj.getData();
        arr=dep+(arr_old-dep)*ech/ech_old
        # new object
        lc1 = LineCollection(zip(dep,arr));lc1.set_transform(self.transform)
        if col==None : col=wx.Color(0,0,255)
        a=col.Get();col=(a[0]/255,a[1]/255,a[2]/255)
        lc1.set_color(col);
        obj = GraphicObject('vecteur', lc1, False, None)
        obj.setData([dep,arr,ech])
        self.addGraphicObject(obj)
        self.cnv.collections[0]=lc1;self.redraw()
    
    #####################################################################
    #             Gestion de l'affichage de particules
    #####################################################################
    def startParticules(self):
        self.mpl_disconnect(self.toolbar._idPress)
        self.mpl_disconnect(self.toolbar._idRelease)
        self.mpl_disconnect(self.toolbar._idDrag)
        # on capte le clic gauche de la souris
        self.m3 = self.mpl_connect('button_press_event', self.mouseParticules)
        self.createParticules()
        #wx.EVT_LEAVE_WINDOW(self,self.finParticules)  # arrete particules qd on sort de visu

    def mouseParticules(self, evt):
        #test pour savoir si le curseur est bien dans les axes de la figure
        if evt.inaxes is None: return
        if evt.button==1:
            [xp,yp,tp]=self.parent.model.Ecoulement.calcParticule(evt.xdata,evt.ydata)
            self.updateParticules(xp,yp,tp)
        elif evt.button==3:
            self.finParticules(evt)
            
    def finParticules(self,evt):
        """fin du dession des particules"""
        self.mpl_disconnect(self.m3)
        self.model.doAction('Top','zoneEnd')

    def createParticules(self):
        """ cree un graphique de lignes representant le passage de particules"""
        obj = self.getObjFromType('particules')
        if obj != None : self.drawParticules(False) #cache les anciennes part
        lignes = [];txt = []
        obj = GraphicObject('particules', lignes, False, None)
        self.addGraphicObject(obj)

    def updateParticules(self,X,Y,T,freq=10):
        """ rajouter une ligne dans le groupe de particules"""
        l0 = self.getObjFromType('particules');
        lignes = l0.object; d = l0.getData()
        if d==None: data=[]
        else : data= d*1
        t = self.getObjFromType('partTime')
        if t!= None: txt=t.object*1
        else : txt=[]
        p, = pl.plot(pl.array(X),pl.array(Y),'r');
        lignes.append(p)
        obj = GraphicObject('particules', lignes, True, None);
        data.append([X,Y,T]);obj.setData(data)
        self.addGraphicObject(obj)
        if freq>0:
            tx,ty,tt = X[0::freq],Y[0::freq],T[0::freq]
            for i in range(len(tx)):
                a=str(tt[i]);b=a.split('.');ln=max(4,len(b[0]))
                txt.append(pl.text(tx[i],ty[i],a[:ln],fontsize='8'))
            obj = GraphicObject('partTime', txt, False, None)
            self.addGraphicObject(obj)
        self.gui_repaint() # bug matplotlib v2.6 for direct draw!!!
        self.draw()
        
    def drawParticules(self,bool,col=wx.Color(255,0,0),valeur=None):
        obj = self.getObjFromType('particules');txt=[]
        if obj==None: return
        lignes = obj.getObject();data=obj.getData()
        if type(valeur)==type((3,4)):
            if len(valeur)>=1: valeur=valeur[0]
        if col==None : col=wx.Color(255,0,0)
        a=col.Get();col=(a[0]/255,a[1]/255,a[2]/255)
        for i in range(len(lignes)):
            lignes[i].set_visible(bool);lignes[i].set_color(col)
        obj = self.getObjFromType('partTime');
        if obj==None : return
        if (valeur==None) or (bool==False):obj.setVisible(bool)
        elif (valeur>0) and bool:
            obj.setVisible(False)
            for p in data:
                X,Y,T = p
                tx,ty,tt = self.ptsPartic(X,Y,T,valeur)
                for i in range(len(tx)):
                    a=str(tt[i]);b=a.split('.');ln=max(4,len(b[0]))
                    txt.append(pl.text(tx[i],ty[i],a[:ln],fontsize='8'))
            obj = GraphicObject('partTime', txt, False, None)
            self.addGraphicObject(obj)
        self.gui_repaint()
        self.draw()
        
    def ptsPartic(self,X,Y,T,dt):
        #tx,ty,tt,i1=iphtC1.ptsLigne(X,Y,T,dt);
        tmax=amax(T);t1=linspace(0.,tmax,int(tmax/dt))
        f=interp1d(T,X);xn=f(t1)
        f=interp1d(T,Y);yn=f(t1)
        return xn,yn,t1
    #####################################################################
    #                   Gestion des zones de la visu
    #####################################################################
    # affichage de toutes les zones d'une variable
    def showVar(self, var, layer):
        self.setUnvisibleZones();self.curVar=var;self.curLayer=layer
        for i in range(len(self.listeZone[var])):
            if layer in self.listeZlayer[var][i] or layer==-1:
                self.listeZone[var][i].setVisible(True)
                self.listeZoneText[var][i].setVisible(True)
        self.changeTitre(var)
        self.redraw()
    def showData(self,liForage,liData):
        self.setUnvisibleZones();self.curVar='data'
        self.listeZoneText['data']=[]
        for zone in self.listeZone['Forages']: zone.setVisible(True)
        lZone=self.model.Aquifere.getZoneList('Forages');txt=[]
        for z in lZone:
            x,y=zip(*z.getXy());nom=z.getNom()
            if nom in liForage:
                ind=liForage.index(nom)
                txt.append(pl.text(mean(x),mean(y),nom+'\n'+str(liData[ind])))
        obj = GraphicObject('zoneText', txt, True, None)        
        self.addGraphicObject(obj)
        self.redraw()
    def changeData(self,taille,col):
        obj=self.listeZoneText['data'][0].getObject()
        for txt in obj:
            txt.set_size(taille);txt.set_color(col)
                
    def getcurZone(self) : return self.curZone
    def setcurZone(self,zone) : self.curZone = zone
    # methode qui efface toutes les zones de toutes les variables   
    def setUnvisibleZones(self):
        for v in self.listeZone:
            for zone in self.listeZone[v]: zone.setVisible(False)
            for txt in self.listeZoneText[v]: txt.setVisible(False)

    # methode appelee par la GUI lorsqu'on veut creer une nouvelle zone
    def setZoneReady(self,idZone, curVar):
        self.typeZone = idZone
        self.curVar = curVar
        self.tempZoneVal = []
        # on deconnecte la toolbar pour activer la formaiton de zones
        self.mpl_disconnect(self.toolbar._idPress)
        self.mpl_disconnect(self.toolbar._idRelease)
        self.mpl_disconnect(self.toolbar._idDrag)
        # on capte le clic gauche de la souris
        self.m1 = self.mpl_connect('button_press_event', self.mouse_clic)
        
    def setZoneEnd(self,evt):
        # on informe la GUI qui informera le model
        xv, yv = self.getcurZone().get_xdata(),self.getcurZone().get_ydata()
        xy = zip(xv,yv)
        # effacer zone pour si cancel, remettre de l'ordre
        self.curZone.set_visible(False)
        self.curZone = None
        self.x1 = self.y1 = []
        if self.curVar=='Profil':
            self.parent.menus.OnProfil2(self.typeZone,xy)
        else :
            self.parent.zoneBox.OnZoneCreate(self.typeZone, xy, self.tempZoneVal)
        
    def addZone(self, layer,nom, val,typeZone,info, xy):
        """ ajout de la zone et du texte (nom+valeur) sur visu et dans listegraphic
        """
        x,y = zip(*xy); txt = []
        if typeZone == Zone.POINT: zone = Line2D(x, y,marker='+',markersize=15,markeredgecolor='r')
        else : zone = Line2D(x, y)
        zone.verts = xy
        obj = GraphicObject(typeZone, zone, True, None);self.curLayer=layer
        obj.setData(info[2])
        self.addGraphicObject(obj)
        self.cnv.add_line(zone)
        if typeZone == Zone.POLYV :
            for i in range(len(x)):
                txt.append(pl.text(x[i],y[i],str(val[i])))
        else :
            txt = pl.text(mean(x)*.1+x[0]*.9,mean(y)*.1+y[0]*.9,nom+'\n'+str(val)[:16])
        obj = GraphicObject('zoneText', txt, True, None)        
        self.addGraphicObject(obj);
        #self.redraw()
        
    def delZone(self, Variable, ind):
        """methode de suppression de la zone d'indice ind de Variable
        """
        if self.listeZone.has_key(Variable)==False: return
        if len(self.listeZone[Variable])>ind:
            self.listeZone[Variable][ind].setVisible(False)
            self.listeZoneText[Variable][ind].setVisible(False)
            self.listeZone[Variable][ind:ind+1] = []
            self.listeZoneText[Variable][ind:ind+1] = []
            self.listeZlayer[Variable].pop(ind)
            self.redraw()
            
    def delAllZones(self,Variable):
        lz=self.listeZone[Variable]
        for i in range(len(lz)):
            lz[i].setVisible(False);
            self.listeZoneText[Variable][i].setVisible(False)
        self.listeZone[Variable] = []
        self.listeZoneText[Variable] = []
        self.redraw()
        
    def modifValZone(self, nameVar, ind, val):
        """modifier dans la zone nameVar la valeur
        ou liste valeur, attention le texte de la zone contient nom et valeur"""
        obj = self.listeZoneText[nameVar][ind].getObject();
        if type(obj)==type([2,3]):
            for i in range(len(obj)):
                pl.setp(obj[i],text=str(val[i]))
        else:
            nom = pl.getp(obj,'text').split('\n')[0]
            pl.setp(obj,text=nom+'\n'+str(val)[:16])
        self.redraw()

    def modifLayZone(self, nameVar, ind, lay):
        """modifier dans la zone la liste des layers"""
        obj = self.listeZone[nameVar][ind]
        obj.setData(lay)
        self.listeZlayer[nameVar][ind]=lay
        self.redraw()
        
    def modifXyZone(self, nameVar, ind, xy):
        """ modification des points de la zone d'indice ind de nom nameVar
        """
        zone = self.listeZone[nameVar][ind].getObject()
        x,y=zip(*xy);zone.set_data(x,y)
        self.redraw()

    def modifZone(self, nameVar, ind):
        """ modification interactive des points de la zone d'indice ind de nom nameVar
        """
        zone = self.listeZone[nameVar][ind].getObject()
        self.polyInteract = PolygonInteractor(self,zone, nameVar, ind)
        zone.set_visible(False)
        self.cnv.add_line(self.polyInteract.line)
        self.draw()

    def finModifZone(self):
        """fonction qui met fin a la modification de la zone courante"""
        if self.polyInteract != None:
            self.polyInteract.set_visible(False)
            self.polyInteract.disable()
            # on informe la GUI des nouvelles coordonnees
            var, ind = self.polyInteract.typeVariable,self.polyInteract.ind
            x,y=self.polyInteract.lx,self.polyInteract.ly
            xy=zip(x,y);self.parent.modifBox.OnModifZoneCoord(var, ind, xy)
            zone =self.listeZone[var][ind].getObject()
            zone.set_data(x,y);zone.set_visible(True)
            # on modifie la position du texte
            txt = self.listeZoneText[var][ind].getObject()
            if type(txt)==type([5,6]):
                for i in range(len(txt)):
                    txt[i].set_position((x[i],y[i]))
            else:
                txt.set_position((mean(x)*.1+x[0]*.9,mean(y)*.1+y[0]*.9))                
            self.draw()            
    
    def setAllZones(self,listeZin):
        """methode pour mettre toutes les zones a jour lors de l'import d'un fichier
        """
        for var in listeZin:
            self.listeZone[var]=[]
            self.curVar = var
            for i in range(len(listeZin[var])):
                zIn = listeZin[var][i];a,b,layer=zIn.getInfo()[:3];
                self.addZone(layer,zIn.getNom(),zIn.getVal(),zIn.getForme(),
                        zIn.getInfo(),zIn.getXy())

        self.setUnvisibleZones()
        #self.redraw()

    #####################################################################
    #             Gestion de l'interaction de la souris
    #             pour la creation des zones
    #####################################################################    

    #methode executee lors d'un clic de souris dans le canvas
    def mouse_clic(self, evt):
        if evt.inaxes is None:
            return      
        if self.curZone == None:  # au depart
            self.x1 = [float(str(evt.xdata)[:6])] # pour aovir chiffre pas trop long
            self.y1 = [float(str(evt.ydata)[:6])]
            self.setcurZone(Line2D(self.x1,self.y1))
            self.cnv.add_line(self.curZone)
            self.m2 = self.mpl_connect('motion_notify_event', self.mouse_motion)
            if self.typeZone==Zone.POLYV:
                self.polyVdialog()
            if self.typeZone==Zone.POINT:
                self.deconnecte()
                self.setZoneEnd(evt)

        else :  # points suivants
            if self.typeZone==Zone.POLYV and evt.button ==1:
                rep = self.polyVdialog()  # dialogue pour valeur intermediaires mais paps pour derniere
                if rep==False : return
            self.x1.append(float(str(evt.xdata)[:6]))
            self.y1.append(float(str(evt.ydata)[:6]))
            if self.typeZone==Zone.LIGNE or self.typeZone==Zone.RECT :
                self.deconnecte()  #fin des le 2eme point
                self.setZoneEnd(evt)
            if (self.typeZone==Zone.POLY or self.typeZone==Zone.POLYV) and evt.button==3: # fin du polygone
                self.deconnecte()
                self.setZoneEnd(evt)

    #methode executee lors du deplacement de la souris dans le canvas suite a un mouse_clic
    def mouse_motion(self, evt):
        time.sleep(0.1)
        if evt.inaxes is None: return
        lx, ly = self.x1*1, self.y1*1    
        if self.typeZone == Zone.RECT:
            xr,yr = self.creeRectangle(self.x1[0],self.y1[0],evt.xdata,evt.ydata)
            self.curZone.set_data(xr,yr)      
        else : # autres cas
            lx.append(evt.xdata);ly.append(evt.ydata)
            self.curZone.set_data(lx,ly)
        self.draw()

    def polyVdialog(self):
        dlg = MyDialogs.MyGenericCtrl(self, "Point", [('Valeur',0.)])
        retour = dlg.ShowModal()
        if retour == wx.ID_OK:
            values = dlg.GetValues()
            self.tempZoneVal.append(float(values[0][1]))
            return True
        else: return False

    def creeRectangle(self, x1, y1, x2, y2):
            xr=[x1,x2,x2,x1,x1]
            yr=[y1,y1,y2,y2,y1]
            return [xr,yr]
        
    def deconnecte(self):
        # deconnecter la souris
        self.mpl_disconnect(self.m1)
        self.mpl_disconnect(self.m2)
    ###################################################################
    #   deplacer une zone ##############################

    def startMoveZone(self, nameVar, ind):
        """ methode qui demarre les interactions avec la souris"""
        # reperer la zone et rajouter un point de couleur
        self.nameVar, self.ind = nameVar, ind;
        zone = self.listeZone[nameVar][ind].getObject()
        self.curZone = zone
        self.lx, self.ly = zone.get_xdata(),zone.get_ydata()
        self.xstart=self.lx[0]*1.;self.ystart=self.ly[0]*1.;
        self.ptstart=Line2D([self.xstart],[self.ystart],marker='o',
                markersize=7,markerfacecolor='r')
        self.cnv.add_line(self.ptstart)
        self.m1 = self.mpl_connect('button_press_event', self.zoneM_clic)
        self.draw()
        
    def zoneM_clic(self,evt):
        """ action au premier clic"""
        if evt.inaxes is None: return
        #if evt.button==3: self.finMoveZone(evt) # removed OA 6/2/13
        d=sqrt((evt.xdata-self.xstart)**2+(evt.ydata-self.ystart)**2)
        xmn,xmx=self.xlim;ymn,ymx=self.ylim
        dmax=sqrt((xmx-xmn)**2+(ymx-ymn)**2)/100;
        if d>dmax: return
        self.m2 = self.mpl_connect('motion_notify_event', self.zone_motion)
        self.m3 = self.mpl_connect('button_release_event', self.finMoveZone)
        self.mpl_disconnect(self.m1)

    def zone_motion(self,evt):
        """ methode pour deplacer la zone quand on deplace la souris"""
        # reperer le curseur proche du point de couleur
        time.sleep(0.1);
        if evt.inaxes is None: return
        # changer els coord du polygone lorsque l'on deplace la souris
        lx=[a+evt.xdata-self.xstart for a in self.lx]
        ly=[a+evt.ydata-self.ystart for a in self.ly]
        self.ptstart.set_data(lx[0],ly[0])
        self.curZone.set_data(lx,ly);
        self.draw()
        
    def finMoveZone(self,evt):
        """ methode pour arret de deplacement de la zone"""
        # lorsque l'on relache la souris arreter les mpl connect
        self.mpl_disconnect(self.m2)
        self.mpl_disconnect(self.m3)
        # renvoyer les nouvelels coordonnes au modele
        lx, ly = self.curZone.get_xdata(),self.curZone.get_ydata()
        self.listeZone[self.nameVar][self.ind].getObject().set_data(lx,ly)
        xy = zip(lx,ly)
        self.parent.modifBox.OnModifZoneCoord(self.nameVar, self.ind, xy)
        # on modifie la position du texte
        txt = self.listeZoneText[self.nameVar][self.ind].getObject()
        if type(txt)==type([5,6]):
            len(txt) # cas polyV
            for i in range(len(txt)): txt[i].set_position((lx[i],ly[i]))
        else:
            txt.set_position((mean(lx)*.1+lx[0]*.9,mean(ly)*.1+ly[0]*.9))                
        self.ptstart.set_visible(False);self.ptstart = None
        self.curZone=None
        self.draw()

class PolygonInteractor:
    """
    A polygon editor.

    Key-bindings
      't' toggle vertex markers on and off.  When vertex markers are on,
          you can move them, delete them
      'd' delete the vertex under point      
      'i' insert a vertex at point.  You must be within epsilon of the
          line connecting two existing vertices          
    """

    showverts = True

    def __init__(self, parent,poly, typeVariable, ind):
        if poly.figure is None:
            raise RuntimeError('You must first add the polygon to a figure or canvas before defining the interactor')
        self.canvas,self.parent = poly.figure.canvas,parent
        self.poly = poly
        self.epsilon=(parent.xlim[1]-parent.xlim[0])/100
        x, y = self.poly.get_xdata(),self.poly.get_ydata()
        self.lx=list(x);self.ly=list(y)
        self.line = Line2D(x,y,marker='o', markerfacecolor='r')
        self.typeVariable, self.ind = typeVariable, ind
        
        cid = self.poly.add_callback(self.poly_changed)
        self._ind = None # the active vert

        self.c1 = self.canvas.mpl_connect('button_press_event', self.button_press_callback)
        self.c2 = self.canvas.mpl_connect('key_press_event', self.key_press_callback)        
        self.c3 = self.canvas.mpl_connect('button_release_event', self.button_release_callback)
        self.c4 = self.canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)                

    def poly_changed(self, poly):
        'this method is called whenever the polygon object is called'
        # only copy the artist props to the line (except visibility)
        vis = self.line.get_visible()
        Artist.update_from(self.line, poly)
        self.line.set_visible(vis)  # don't use the poly visibility state        

    def get_ind_under_point(self, event):
        'get the index of the vertex under point if within epsilon tolerance'
        x, y = self.lx,self.ly
        d = sqrt((pl.array(x)-event.xdata)**2 + (pl.array(y)-event.ydata)**2)
        indseq = nonzero(equal(d, amin(d)));ind = indseq[0];
        if len(ind)>1: ind=ind[0]
        if d[ind]>=self.epsilon: ind = None
        return ind
        
    def button_press_callback(self, event):
        'whenever a mouse button is pressed'
        if not self.showverts: return 
        if event.inaxes==None: return
        if event.button == 1: 
            self._ind = self.get_ind_under_point(event)
        if event.button==3:
            self.disable();self.parent.finModifZone()

    def button_release_callback(self, event):
        'whenever a mouse button is released'
        if not self.showverts: return
        if event.button != 1: return
        self._ind = None      
        # modification du poly passe en parametre en fonction 
        # des nouveaux sommets crees par le PolygonInteractor
        x = self.line.get_xdata()
        y = self.line.get_ydata()  
        v = self.poly.verts
        for i in range(len(x)/10):
            v[i] = (x[i],y[i])  
        
    def key_press_callback(self, event):
        'whenever a key is pressed'
        if not event.inaxes: return
        if event.key=='t':
            self.showverts = not self.showverts
            self.line.set_visible(self.showverts)
            if not self.showverts: self._ind = None
        elif event.key=='d':
            ind = self.get_ind_under_point(event)
            if ind is not None:
                self.lx.pop(ind);self.ly.pop(ind)
                self.line.set_data(self.lx,self.ly)
        elif event.key=='i':            
            #xys = self.poly.get_transform().seq_xy_tups(self.poly.verts)
            p = (event.xdata, event.ydata) # display coords
            for i in range(len(self.lx)-1):                
                s0 = (self.lx[i],self.ly[i]); #xys[i]
                s1 = (self.lx[i+1],self.ly[i+1]); #xys[i+1]
                d = dist_point_to_segment(p, s0, s1)
                if d<=self.epsilon:
                    self.lx.insert(i+1,event.xdata)
                    self.ly.insert(i+1,event.ydata)
                    self.line.set_data(self.lx,self.ly)
                    break              
            
        self.canvas.draw_idle()

    def motion_notify_callback(self, event):
        'on mouse movement'
        time.sleep(0.1);
        if not self.showverts: return 
        if self._ind is None: return
        if event.inaxes is None: return
        if event.button != 1: return
        x,y = event.xdata, event.ydata;
        self.lx[self._ind],self.ly[self._ind] = x,y
        self.line.set_data(self.lx,self.ly)
        self.canvas.draw_idle()
        
    def disable(self):
        self.canvas.mpl_disconnect(self.c1)
        self.canvas.mpl_disconnect(self.c2)
        self.canvas.mpl_disconnect(self.c3)
        self.canvas.mpl_disconnect(self.c4)

    def set_visible(self,bool):
        self.line.set_visible(bool)
