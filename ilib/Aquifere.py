from scipy import *
from scipy.optimize import fmin,leastsq
import wx
import MyDialogs
from matplotlib.pylab import meshgrid,arange
from calcAquifere import *

class Aquifere:
    """This is class that contains the major characteristics of the domain, grid...
       Hello 
    """

    def __init__(self, model):
        self.model = model;
        self.Base= {}
        self.Base['domain'] = [('x Origine',0.),('x Maximum',500.),('y Origine',0.),
                ('y Maximum',100.)]
        self.Base['grid'] = [('Largeur Cell',5.),('Hauteur Cell',5.),
                ('Nb couche/milieu',1)]
        # NB valable pour grille reguliere sinon large et haut sont listes x dx
        self.Base['units'] =  [('distance',['m',['km','m','cm']]),
                ('temps',['an',['an','j','h','min','sec']])]
        self.Base['vbase'] = [('Mur',[0.]),('Toit',[10.]),('Potentiel',[20.]),
                ('CelluleInactive',[1.]),('Permeabilite',[500.]),('Forages',[0.]),
                ('Porosite',[0.25]),('Recharge',[0.]),('Riviere',[0.]),
                ('Drain',[0.]),('Emmagasin.',[1e-4]),
                ('Transport',[0.]),('Tr_Rech',[0.]),
                ('PHT3D',[0.]),('PH_Rech',[0.])]
        self.Base['type'] = [('Dimension',['2D',['2D','Xsection','Radial','3D']]),('nb Milieux',1),
                ('confinement',['libre',['libre','confine']])]
        noms = zip(*self.Base['vbase'])[0]
        self.Base['interpol'] = list(zip(noms,[False]*len(noms)))
        self.Base['zList']=[('zList',[0.,1.])]
        self.grid={};self.makeGrid()
        # NB si on a plusieurs layers on a une liste de vbase longue n layers
        dzone = {}
        for n in zip(*self.Base['vbase'])[0]: dzone[n] = []
        dzone['Observation'] = []
        # NB si plusieurs layers info chaque zone contient num du layer dans info
        self.Zones = dzone  # dict des zones
        self.Zones0 = dzone.copy();
        # Sauvegarde des parametres initiaux
        self.Base0 = self.Base.copy();self.zb,self.zoneTrans=None,None

    def getBase(self):
        bas=self.Base.copy()
        vb=bas['vbase']
        for i in range(len(vb)): #case of an array in vbase
            if type(vb[i][1][0])==type(rand(4,5)):vb[i][1][0]=self.model.tmpImport[vb[i][0]]
        #print 'aquif getbase',bas
        return bas
    def setBase(self,base):
        for k in base.keys():
            lb0,val0=zip(*self.Base[k]);lb1,val1=zip(*base[k]);
            self.Base[k]=[]
            lb0=list(lb0);val0=list(val0);
            for i in range(len(lb0)):
                if lb0[i] in lb1:
                    i1=lb1.index(lb0[i])
                    if lb0[i] in ['distance','temps','Dimension','confinement']:
                        val0[i]=[val1[i1][0],val0[i][1]]
                    else : val0[i]=val1[i1]
                    if k=='vbase':
                        if type(val1[i1][0])==type(u'e'):  # case of an array
                            fname=val1[i1][0];#print 'aqui setvb',fname
                            val0[i]=[genfromtxt(fname)]
##                        for n in ['Transport','Tr_Rech','PHT3D','PH_Rech']:
##                            if n not in lb1: lb1
            self.Base[k]=zip(lb0,val0)

    def initBase(self):
        self.Base={};self.Base = self.Base0.copy()
        self.zones={};self.Zones = self.Zones0.copy()
        
    def getParm(self,nom):
        if nom=='Type': return self.Base['type']
        elif nom=='Variable':return ['',self.getVarList()]
        elif nom=='zList':
            return range(self.getNbCouches())
        elif nom=='Milieux':
            l0=range(self.getNbMilieux());return ['Milieux',[str(n) for n in l0]]
        elif nom=='Couches':
#            nm=self.getNbMilieux();nbc=self.Base['grid'][2][1]
#            l1=range(nm*nbc);
            return ['Couches',range(self.getNbCouches())]
        elif nom=='Unites': return self.Base['units']
        elif nom=='Domaine':
            if self.getDim() not in ['Xsection','Radial']:return self.Base['domain'] #pas encore besoin z
            else :
                a=self.Base['domain']*1;a[2]=('z Origin',a[2][1]);a[3]=('z Maximum',a[3][1]);return a
        elif nom=='Grille':
            grd=self.Base['grid']
            if type(grd[0][1])==type(5.): return grd
            else : # case of existing vairable grid
                return [('Largeur Cell',5.),('Hauteur Cell',5.),('Nb couche/milieu',1)]
        elif nom=='GriVar':
            grd=self.Base['grid']
            if type(grd[0][1])==type(5.): # debut pas de valeurs de points grille var
                return {'liste x dx': [],'liste y dy': [],'Nb couche/milieu' : [1]}
            else : # case of existing vairable grid
                nb=grd[2][1];nmil=self.getNbMilieux()
                if len(nb)<nmil: nb=nb[0]*nmil
                return {'liste x dx': grd[0][1],'liste y dy': grd[1][1],'Nb couche/milieu' : grd[2][1]}
        elif nom=='Zones':return self.Zones
        elif nom=='Interpol': return self.Base['interpol']        
        
    def setParm(self,nom,lst2):
        if nom=='Type':
            self.Base['type']=lst2
            # mise a jour des vbase pour nl layers
            nMil=lst2[1][1];l0,l1=zip(*self.Base['vbase']);
            self.Base['vbase']=[]
            for i in range(len(l0)): #put vbase to previous values if nb layer change
                self.Base['vbase'].append((l0[i],[l1[i][0]]*nMil))
        elif nom=='Domaine':
            if self.getDim() not in ['Xsection','Radial']: self.Base['domain'] = lst2
            else :
                a=lst2*1;a[2]=('y Origine',lst2[2][1]);a[3]=('y Maximum',lst2[3][1])
                self.Base['domain'] = a
        elif nom=='Grille':
            self.Base['grid'] = lst2;
        elif nom=='GriVar': # lst2 est un dico dans ce cas...
            self.Base['grid']=[('Largeur Cell',lst2['liste x dx']),('Hauteur Cell',lst2['liste y dy']),
                  ('Nb couche/milieu',lst2['Nb couche/milieu'])] 
        elif nom=='Unites':self.Base['units'] = lst2
        elif nom=='Interpol': self.Base['interpol'] = lst2
            
    def getObject(self,nom,retour,temps,lay,ori):
        if nom=='ZoneImg':
            nomv = self.model.gui.parametresGui.getCurrentVar();
            vbase = self.getVbase(nomv)
            return obj2mat(self,nomv,lay,vbase)
        
    def doAction(self,nom):
        if nom in ['Domaine','Grille','GriVar']:
            self.createZoneTransient();self.makeGrid()
            self.makeZblock()
            if self.model.gui!=None: self.model.visu.changeDomain();
    
    def getVarList(self):
        return list(zip(*self.Base['vbase'][:11])[0])
    def getTypeAq(self):
        l1=list(zip(*self.Base['type'])[0])
        return self.Base['type'][l1.index('confinement')][1][0]
    def getDim(self):
        l1=list(zip(*self.Base['type'])[0])
        return self.Base['type'][l1.index('Dimension')][1][0]        
    def getInterpol(self,nomv):
        l = self.getVarList();
        if nomv in l:return self.Base['interpol'][l.index(nomv)][1]
        else : return False

    # media, layers
    def getNbMilieux(self):
        # returns the number of media in the model
        l1=list(zip(*self.Base['type'])[0])
        return self.Base['type'][l1.index('nb Milieux')][1]
##    def getListMilieux(self):
##        # returns a list of the nb of layers per media
##        a=self.Base['grid'][2][1];
##        if type(a)==type([5]):return [int(b) for b in a]
##        else : return int(a)
    def getNbCouches(self):
        # returns the total number of layers in the model
        nm=self.getNbMilieux();nbc=0
        for m in range(nm):nbc+=self.getNbCouByMil(m)
        if self.getDim() in ['Xsection','Radial']:return self.grid['ny']
        else : return nbc
    def getNbCouByMil(self,mil):
        # returns the number of layer for a given media
        lm=self.Base['grid'][2][1]
        if type(lm)==type([5,6]):
            if len(lm)>1:
                if len(lm[mil].split())>1: # a range of value for one media
                    mur=self.getVbase('Mur',mil);toit=self.getVbase('Toit',mil)
                    parm=lm[mil].split();#print 'aqui nbCou',parm
                    a=self.calcGriVar(mur,toit,float(parm[0]),float(parm[1]))
                    return len(a) # the number of layers for this media
                else : return int(lm[mil]) # juste one value for this media
            else : return int(lm[0]) # in case of a tooo short list
        else : return int(lm) # just one value for all media
    def lay2mil(self,lay): 
        nbm=self.getNbMilieux();totl=0
        for m in range(nbm):
            totl+=self.getNbCouByMil(m)
            if lay<totl : return m
    def mil2lay(self,mil):
        start=0
        for m in range(mil):start+=self.getNbCouByMil(m)
        a=range(self.getNbCouByMil(mil))
        b=[x+start for x in a];return b
        
    def getFullGrid(self): return self.grid
    def getGridForMf(self):
        if self.getDim() in ['Xsection','Radial']:
            grd=self.grid.copy();grd['ny']=1;grd['dy']=[1.];return grd
        else: return self.grid

    def getXYticks(self):
        g=self.grid;
        xt=[g['x0']];xt.extend(g['x0']+cumsum(g['dx']))
        yt=[g['y0']];yt.extend(g['y0']+cumsum(g['dy']))
        return [array(xt),array(yt)]
    
    def makeGrid(self):
        """ a partir des listes domaines et grid on sort un dictionnaire avec les donnees
        x0, dx, nx, y0, dy, ny
        pour grille variable l'input est une liste de coord et taille de cellule
        et dx et dy crees sont des vecteurs
        """
        grd = {}
        grd['x0'] = float(self.Base['domain'][0][1])
        grd['x1'] = float(self.Base['domain'][1][1])
        grd['y0'] = float(self.Base['domain'][2][1])
        grd['y1'] = float(self.Base['domain'][3][1])
        dxIn=self.Base['grid'][0][1]
        dyIn=self.Base['grid'][1][1]
        # cas grille fixe
        longX = grd['x1']-grd['x0']
        longY = grd['y1']-grd['y0']
        #if dxIn>longX: dxIn=longX
        if type(dxIn)==type(3.):
            grd['nx'] = int(round(longX/dxIn))
            grd['ny'] = int(round(longY/dyIn))
            grd['dx'] = array([dxIn]*grd['nx'])
            grd['dy'] = array([dyIn]*grd['ny'])
        else:
        # cas variable liste de valeurs pour xi, largeur au pt xi
            ldx=linspace(0,0,0);ldy=ldx*1; # vect vides
            xi=range(len(dxIn));dxi=xi*1;
            for i in range(len(dxIn)):
                sxi=dxIn[i];xi[i],dxi[i]=[float(x) for x in sxi.split()]
            yi=range(len(dyIn));dyi=yi*1;
            for i in range(len(dyIn)):
                syi=dyIn[i];yi[i],dyi[i]=[float(x) for x in syi.split()]
            for i in range(1,len(dxIn)):
                ldx=concatenate([ldx,self.calcGriVar(xi[i-1],xi[i],dxi[i-1],dxi[i])],axis=0)
            for i in range(1,len(dyIn)):
                ldy=concatenate([ldy,self.calcGriVar(yi[i-1],yi[i],dyi[i-1],dyi[i])],axis=0)
            grd['dx'],grd['dy']=ldx*1.,ldy*1.;
            grd['nx'],grd['ny']=len(ldx),len(ldy)
        self.grid=grd

    def calcGriVar(self,x0,x1,dx0,dx1):
#if 3>2:
        a=logspace(log10(dx0),log10(dx1),100);#print 'aq calcgriv',a
        n=round(100*(x1-x0)/sum(a))
        if n==0:
            dxv=[x1-x0]
        else :
            dxv=logspace(log10(dx0),log10(dx1),n)
            dxv[dxv==max(dxv)]+=x1-x0-sum(dxv) # to fit the total
        return dxv

    def makeZblock(self):
        # value of top of each layer at the centre of the cells
        if self.zoneTrans==None: self.createZoneTransient()
        grd = self.getFullGrid();nlay=self.getNbCouches()
        nmil=self.getNbMilieux();
        mlist=self.Base['grid'][2][1];#mlist is still a list of strings
        self.zb = zeros((nlay+1,grd['ny'],grd['nx']));
        toit=obj2mat(self,'Toit',0,self.getVbase('Toit',0));l=0;
        self.zb[0,:,:]=toit
        for m in range(nmil):
            mur=obj2mat(self,'Mur',m,self.getVbase('Mur',m));
            nl = self.getNbCouByMil(m)
            ep0=self.zb[l,:,:]-mur;ep=[0]*nl
            if type(mlist)==type(5): ep=[ep0/mlist]*nl  # one integer
            else : # mlist is a true list
                if len(mlist)==1: ep=[ep0/int(mlist[0])]*nl # a list with one value
                else :
                    if type(mlist[m])==type(4):
                        ep=[ep0/mlist[m]]*nl;break # one value integer
                    elif len(mlist[m].split())==1: # the m lay has one value string
                        ep=[ep0/int(mlist[m])]*nl 
                    else: # the m layer has two parameters to calc thickn distribution
                        parm=mlist[m].split();
                        a=self.calcGriVar(mur[0,0],toit[0,0],float(parm[0]),float(parm[1]))
                        for i in range(len(a)):
                            ep[i]=a[i]*(toit-mur)/(toit[0,0]-mur[0,0])
            for i in range(nl):
                l+=1;#print l,ep,self.zb[:,:,l-1]
                self.zb[l,:,:]=self.zb[l-1,:,:]-ep[i]
            toit=mur

    def getZblock(self):
        if self.zb==None: self.makeZblock()
        return self.zb        
  
    def getMesh(self,ori,plan): # complete mesh for given plane
        if self.zb==None: self.makeZblock()
        grd = self.getFullGrid();dx1=grd['dx'];dy1=grd['dy'];#print 'aq mesh',grd
        xv=zeros((grd['nx']+1));xv[0]=grd['x0'];xv[1:]=grd['x0']+cumsum(dx1);
        yv=zeros((grd['ny']+1));yv[0]=grd['y0'];yv[1:]=grd['y0']+cumsum(dy1);
        nlay,nx,ny=shape(self.zb)
        if self.getDim()in ['Xsection','Radial']: return meshgrid(xv,yv)
        if ori=='Z': return meshgrid(xv,yv)
        elif ori=='X':
            a=yv*ones((nlay,1));b=self.zb[:,:,plan]
            c=ones((nlay,len(yv)));
        elif ori=='Y':
            a=xv*ones((nlay,1));b=self.zb[:,plan,:];
            c=ones((nlay,len(xv)));
        c[:,1:-1]=b[:,1:]/2+b[:,:-1]/2;c[:,0]=b[:,0];c[:,-1]=b[:,-1]
        return a,c

    def getMeshCentre(self,ori,plan): # mesh au milieu de la grille
        if self.zb==None: self.makeZblock()
        grd = self.getFullGrid();dx1=grd['dx'];dy1=grd['dy']
        xv=grd['x0']+cumsum(dx1)-dx1/2.;
        yv=grd['y0']+cumsum(dy1)-dy1/2.;
        nlay,nx,ny=shape(self.zb)
        if self.getDim()in ['Xsection','Radial']: return meshgrid(xv,yv)
        if ori=='Z': return meshgrid(xv,yv)
        elif ori=='X':
            z=self.zb[1:,:,plan]/2+self.zb[:-1,:,plan]/2
            return yv*ones((nlay-1,1)),z
        elif ori=='Y':
            z=self.zb[1:,plan,:]/2+self.zb[:-1,plan,:]/2;
            return xv*ones((nlay-1,1)),z

    def getEpais(self):
        if self.zb==None: self.makeZblock()
        ep = self.zb[:-1,:,:]-self.zb[1:,:,:];
        if self.getDim()in ['Xsection','Radial']:
            grd = self.getFullGrid();dx,dy = grd['dx'],grd['dy'];
            a,ep=meshgrid(ones((len(dx))),dy[::-1])
            ep=reshape(ep,(len(dy),1,len(dx)))
        if self.getTypeAq()=='libre': 
            hd=self.model.Ecoulement.getMfHead(0);ep[0,:,:]=hd-self.zb[1,:,:]
        return ep
                
    def getClimP(self):
        """ retourne les conditions aux limites qui arretent les particules"""
        a= 1-obj2mat1(self,'Potentiel',0,0,'BC')
        clim=a*obj2mat1(self,'CelluleInactive',0,0)
        return clim[-1::-1,:]

# travail sur les valeurs de base
    
    def getVbase(self, nom, mil=0):
        """ permet d'obtenir la valeur de base d'une variable donnee sur un milieu"""
        l= list(zip(*self.Base['vbase'])[0])
        if nom in l: return self.Base['vbase'][l.index(nom)][1][mil]
        else : return 0.
    def getVbaseLay(self, nom, layer=0):
        """ permet d'obtenir la valeur de base d'une variable donnee sur un layer"""
        l=list(zip(*self.Base['vbase'])[0]);m =self.lay2mil(layer)
        nbc=self.getNbCouByMil(m);lstart=0
        for i in range(m): lstart+=self.getNbCouByMil(i)
        if nom=='Toit':
            v1=self.Base['vbase'][l.index('Mur')][1][m]
            v2=self.Base['vbase'][l.index('Toit')][1][m]
            vb=v1+(v2-v1)*(nbc-layer+lstart)/nbc
        elif nom=='Mur':
            v1=self.Base['vbase'][l.index('Mur')][1][m]
            v2=self.Base['vbase'][l.index('Toit')][1][m]
            vb=v1+(v2-v1)*(nbc-layer+lstart-1)/nbc
        else : vb=self.Base['vbase'][l.index(nom)][1][m]
        #print 'aqui',layer,m,vb
        return vb

    def setVbase(self, nom, vbase, lmil=[0]):
        li= list(zip(*self.Base['vbase'])[0]) # list of variables
        nbm= self.getNbMilieux()
        for m in lmil:
            self.Base['vbase'][li.index(nom)][1][m] = vbase*1.
            if nom=='Mur' and m<nbm-1:
                self.Base['vbase'][li.index('Toit')][1][m+1] = vbase*1.
          
    def getUnits(self,nomvar):
        if nomvar in ['Transport','Tr_Rech','PHT3D','PH_Rech','Observation']:return ' '
        units = self.Base['units']
        dist,tps = units[0][1][0],self.model.gui.traduit(units[1][1][0])
        l = list(zip(*self.Base['vbase'])[0]);
        if nomvar not in l: return ' '
        ivar = l.index(nomvar)
        lst = [dist,dist,dist,"",dist+"/"+tps,dist+"3/"+tps,"",dist+"/"+tps,
               "","","",""]
        return lst[ivar]
       

# travail sur les zones
    def getAllZones(self): return self.Zones
    def setAllZones(self,lzone):
        self.Zones =lzone.copy()
    def getZoneList(self, var, mil=-1):
        lzone = []
        if mil==-1: return self.Zones[var]
        else :
            for z in self.Zones[var]:
                info = z.getInfo()[2]
                if (type(info)==type([5,6])) and (mil in info):
                    lzone.append(z)
                elif (type(info)==type(5)) and (mil==info): 
                    lzone.append(z)
            return lzone
    def getZonesAsDict(self):
        dict1={}
        if 'PH_Rech' not in self.Zones.keys(): self.Zones['PH_Rech']=[]
        for k in self.Zones.keys():
            dict1[k]=[]
            for z in self.Zones[k]: dict1[k].append(z.getBase())
        return dict1
    def setZonesFromDict(self,dict0):
        self.Zones = {}
        for k in ['PH_Rech','Observation','Tr_Rech']:
            if k not in self.Zones.keys(): self.Zones[k]=[]
        if dict0.has_key('GeneralHead'):dict0.pop('GeneralHead');
        dict0['Emmagasin.']=[]
        for k in dict0.keys():
            self.Zones[k]=[]
            for z in dict0[k]:
                var=z['info'][0]
                if (var in ['Potentiel','Transport','PHT3D']) and len(z['info'])<4:
                    z['info'].extend(['B.Condition','Transient'])  # version 1_k to 1_l
                if (var in ['Transport','PHT3D']) and z['val']<0:
                    z['val']=-z['val'];z['info'][-1]='Initial'  # version 1_k to 1_l
                z1 = Zone(z['nom'],z['val'],z['forme'],z['info'],z['xy'])
                self.Zones[k].append(z1)
        
    def getNbzone(self, var):
        if self.Zones.has_key(var): return len(self.Zones[var])
        else : return 0
    def addZone(self,var,nom,val,forme,info,xy):
        if self.Zones.has_key(var):
            self.Zones[var].append(Zone(nom,val,forme,info,xy))
        else :
            self.Zones[var] = [Zone(nom,val,forme,info,xy)]
        self.createZoneTransient()
        self.model.setGlistParm('Aquifere','ZoneImg','calc',0)  # pour detruire ZoneImg
            
    def getZone(self, var, izone):
        """ recupere la zone qui correspond a variable et numero"""
        listeZ = self.Zones[var]
        for i in range(len(listeZ)):
            if listeZ[i].getInfo()[1] == izone:
                return listeZ[i]
        return None
    def getZoneByName(self,var,zname):
        listeZ = self.Zones[var]
        for i in range(len(listeZ)):
            if listeZ[i].getNom() == zname:
                return listeZ[i]
        
    def createZoneTransient(self):
        """make a dic of all times and values of each zone for each time"""
        lVar=self.Zones.keys()*1
        dZone={};tlist=[];
        for var in lVar: # make the list of times
            for z in self.getZoneList(var):
                if z.getForme()!=4 and type(z.getVal())==type([5,6]): # if list of values : transient
                    slist=z.getVal()
                    for s in slist: tlist.append(float(s.split (' ')[0]))
        # get the list from flow model
        t0=self.model.getParm('Ecoulement','Temps') # final time, stress period l, nsteps
        tf=t0[0][1];per=t0[1][1];tf2=arange(0.,tf*1.01,per);tflow=[round(x,5) for x in tf2]
        tflow.extend(tlist);tlist=list(set(tflow));tlist.sort()
        #if tlist==[]: tlist=[100.] # cas permanent on met long 500
        dZone['tlist']=tlist;dZone['Transient']={};dZone['zlist']={}
        for var in lVar: # loop into var to get transient values for each zone
            dZone['Transient'][var]=False;dZone['zlist'][var]=[]
            dZone[var]=None;lZ=self.getZoneList(var);
            if len(lZ)==0: continue
            tbl=zeros((len(tlist),len(lZ)))+0.
            for iz in range(len(lZ)):
                # get the list, 
                slist=lZ[iz].getVal();form=lZ[iz].getForme()
                if type(slist)!=type([5,6]): tbl[:,iz]=slist # only one value
                elif form==4: tbl[:,iz]=slist[0] # variable polygon take only 1st value
                else : # a list of values : transient
                    vprec=0;tl2=[];vl2=[];dZone['Transient'][var]=True
                    dZone['zlist'][var].append(iz)
                    for s in slist:
                        [a,b]=s.split();tl2.append(float(a));vl2.append(float(b))
                    for it in range(len(tlist)):
                        t = tlist[it]
                        if t in tl2:
                            v=vl2[tl2.index(t)];tbl[it,iz]=v;vprec=v
                        else : tbl[it,iz]=vprec
            dZone[var]=tbl
        self.zoneTrans=dZone;#print 'Aq ztrans',dZone
        
    def getZoneTransient(self): return self.zoneTrans
    def getZoneIndices(self,zone):
        grd = self.getFullGrid();
        x0,dx,nx,y0,dy,ny=grd['x0'],grd['dx'],grd['nx'],grd['y0'],grd['dy'],grd['ny']
        grx=concatenate([array(x0,ndmin=1),x0+cumsum(dx)],axis=0)
        gry=concatenate([array(y0,ndmin=1),y0+cumsum(dy)],axis=0)
        xy=zone.getXy();x,y = zip(*xy)
        return zone2index(x,y,x,grx,gry,nx,ny)
    
    def delZone(self, var, izone):
        """detruit une zone dans la liste et decremente les numeros des suivantes
        """
        listeZ = self.Zones[var]
        for i in range(len(listeZ)):
            if listeZ[i].getInfo()[1] == izone :
                del self.Zones[var][i]
                break;
        for i in range(len(listeZ)):
            if listeZ[i].getInfo()[1] > izone :
                nb2 = self.Zones[var][i].getInfo()[1]
                self.Zones[var][i].setInfo(1,nb2-1)
        self.createZoneTransient()

    def delAllZones(self,var):
        self.Zones[var]=[];self.createZoneTransient()

class Zone:

    POINT = 0
    LIGNE = 1
    RECT = 2
    POLY = 3
    POLYV = 4
    
    # creation d'une zone d apres sa forme
    def __init__(self,nom,val,forme,info,xy):
        self.Base={'nom':nom,'val':val,'forme':forme,'info':info,'xy':xy}
        
    def getBase(self): return self.Base
    def getNom(self): return self.Base['nom']
    def getVal(self): return self.Base['val']    
    def getForme(self): return self.Base['forme']    
    def getInfo(self): return self.Base['info']
    def getXy(self): return self.Base['xy']
    def getMil(self): return self.Base['info'][2]

    def setNom(self,nom): self.Base['nom'] = nom
    def setVal(self,val): self.Base['val'] = val        
    def setForme(self,forme): self.Base['forme'] = forme
    def setInfo(self,num,info): self.Base['info'][num] = info
    def setXy(self,xy): self.Base['xy'] = xy

