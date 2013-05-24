from scipy import *
from Aquifere import *
from calcAquifere import *
from Ecoulement import *
from Transport import *
from PHT3D import *
#import scipy.io.array_import as IOAscii
from pylab import savetxt
import xml.dom.minidom as xdom
import os
import time

class iPht3dModel:
    '''Classe generale du modele, contient toutes les donnees necessaires a
    Modflow, Rflow, RT3D...
    Les donnees sont dans un dictionnaire sous forme de listes
    contenant domaine, grid, unit, solver, lzone, Tparam, espec, parC...
    '''
    
    def __init__(self,gui=None,mainDir=' '):
        self.project = ['','']
        self.gui = gui;self.visu=None;self.Base = {};self.mainDir=mainDir
        self.binDir = mainDir+os.sep+'bin'
        self.Base['info'] = {'version':'2_1a','type':1,'transitoire':False,'langue':None,'date':' ',
                     'Isot':False,'etat':'','opt':[]}
        self.data={'cols':[],'lignes':[],'data':None}
        self.mapName = ''
        self.groupes = ['Aquifere','Ecoulement','Transport','PHT3D'] 
        for g in self.groupes:
            exec('self.'+g+'='+g+'(self)')
        self.Base['Glist'] = self.initGlist()
        self.initOpt()
        self.indxReac,self.indxRt3d,self.tempsRt3d = '','',0
        self.tmpImport={}

    def initGlist(self):
        d={'calc':0,'valeur':None,'col':None};dic={}
        dic['Aquifere']= {'Grille':d.copy(),'Carte':d.copy(),'ZoneImg':d.copy()}
        dic['Ecoulement'] = {'Charge':d.copy(),'Vitesse':d.copy(),'Particules':d.copy()}
        dic['Transport'] = {'Traceur':d.copy()}
        dic['PHT3D']={'Temps':d.copy(),'Especes':d.copy()}
        return dic
    def initOpt(self):
        if self.Base['info']['opt']==[]:
            self.calcOpt=[('Variable_Density',['non',['oui','non']]),
                      ('Double porosite',['non',['oui','non']])]
            self.Base['info']['opt']=self.calcOpt*1
        else : self.calcOpt=self.Base['info']['opt']*1
        self.visuOpt=[('Axes meme echelle',['non',['oui','non']])]

    # focntions de base
    def getBase(self,groupe):
        if groupe=='Zones': return self.Aquifere.getZonesAsDict()
        elif groupe=='Modele': return self.Base
        elif groupe=='Data': return self.data
        else:
            exec('n=self.'+groupe+'.getBase()');return n        
    def setBase(self,groupe,dic):
        if groupe=='Zones': self.Aquifere.setZonesFromDict(dic)
        elif groupe=='Modele':
            for d in dic.keys():
                if d=='Glist':
                    self.Base['Glist']=self.updateDict(self.initGlist(),dic[d])
                else : self.Base[d] = dic[d]
        elif groupe=='Data':
            self.data=dic;#print self.Base['data']
        else :
            exec('n=self.'+groupe+'.setBase(dic)')
        if 'opt' not in self.Base['info'].keys(): self.Base['info']['opt']=[]
    def initModel(self):
        for n in self.groupes:
            exec('self.'+n+'.initBase()')
    def getGroupe(self,grp):
        exec('g=self.'+grp);return g
    def getParm(self,groupe,nom):
        if groupe=='calcOpt': return self.calcOpt
        if groupe=='visuOpt': return self.visuOpt
        if groupe in self.groupes:
            exec('n=self.'+groupe+'.getParm(\"'+nom+'\")');return n

    def setParm(self,groupe,nom,lst2):
        if groupe=='calcOpt': self.calcOpt=lst2;self.Base['info']['opt']=lst2
        elif groupe=='visuOpt': self.visuOpt=lst2
        elif groupe in self.groupes:
            exec('self.'+groupe+'.setParm(\"'+nom+'\",lst2)');

    def getObject(self,groupe,nom,tag,temps,lay,ori):
        if nom=='Carte': return self.mapName
        if groupe in self.groupes:
            exec('n=self.'+groupe+'.getObject(\"'+nom+'\",tag,temps,lay,ori)');return n

    def doAction(self,groupe,nom,info=True):
        if groupe in self.groupes:
            exec('text=self.'+groupe+'.doAction(\"'+nom+'\")')
        else : text=None
        if info==False: text=None
        if self.gui!=None: self.gui.control.majour(groupe,nom,text)
            
    def getEtat(self) : return self.Base['info']['etat']
    def setEtat(self,etat):
        self.Base['info']['etat'] = etat
    def getInfo(self) : return self.Base['info']
    #def getTypeAq(self): return self.Base['info']['type']
    #def getTransit(self): return self.calcOpt[0][1][0]
    def getVarDensity(self):
        if self.calcOpt[0][1][0]=='oui': return True
        else : return False
    def getDualPoro(self):
        if self.calcOpt[1][1][0]=='oui': return True
        else : return False
    def getOptEchelle(self): return self.visuOpt[0][1][0]=='oui'
    def getProject(self): return self.project
    def setProject(self,project): self.project=project
    def getProjectPath(self): return self.project[0]
    def getProjectName(self): return self.project[1]
    def setVisu(self,visu): self.visu = visu
    def getMap(self): return self.mapName
    def setMap(self,mapfile):
        self.mapName = mapfile;self.setGlistParm('Aquifere','Carte','calc',0)
    def getGlist(self): return self.Base['Glist']
    def getGlistParm(self,groupe,nom,parm):
        if groupe in self.groupes or groupe=='Data':
            if nom in self.Base['Glist'][groupe]:
                return self.Base['Glist'][groupe][nom][parm]
        
    def setGlistParm(self,groupe,nom,parm,val):
        if groupe in self.groupes or groupe=='Data':
            if self.Base['Glist'][groupe].has_key(nom):
                if self.Base['Glist'][groupe][nom].has_key(parm):
                    self.Base['Glist'][groupe][nom][parm]=val   

    def setGlistGroup(self,groupe,lst0):
        d={'calc':0,'valeur':None,'col':None};
        self.Base['Glist'][groupe]={}
        for n in lst0: self.Base['Glist'][groupe][n]=d.copy()

    def resetGlist(self):
        self.Base['Glist']=self.initGlist()
        #print self.Base['Glist']
    def allGlistCalcNull(self):
        for k in self.Base['Glist'].keys():
            for k1 in self.Base['Glist'][k].keys():
                if type(self.Base['Glist'][k][k1])==type({}):
                    self.Base['Glist'][k][k1]['calc']=0
         
    def openModel(self):
        tstart=time.time()
        filename = self.project[0] + os.sep + self.project[1] + '.ipht'
        f1 = file(filename, 'r');doc = f1.read();f1.close()
        dom=xdom.parseString(doc)        
        dicts=dom.getElementsByTagName("dict")
        for d in dicts:
            dname = d.getElementsByTagName("name")[0].childNodes[0].data
            keys = d.getElementsByTagName("key");dict1 = {}
            for k in keys:
                kname = k.getElementsByTagName("name")[0].childNodes[0].data
                kdata = k.getElementsByTagName("content")[0].childNodes[0].data
                exec('dict1[kname] ='+kdata);
            self.setBase(dname,dict1)
        if self.gui!=None:
            self.visu.setVisu(self,self.Base['Glist']);
            self.gui.parametresGui.initParm()
            self.gui.afficheTree.resetVisu()
            self.gui.parametresGui.setDualPoro(self.calcOpt[1][1][0]=='oui')
            self.gui.parametresGui.currentLayer=0
        self.doAction('Aquifere','Type');
        self.Aquifere.createZoneTransient();
        self.Aquifere.makeGrid();self.Aquifere.makeZblock();
        self.doAction('Aquifere','Domaine');
        self.doAction('Ecoulement','Temps');
        self.Ecoulement.setReader();self.Transport.setReader()
        self.setOptions() # option file
        self.initOpt() #calculation options
        self.PHT3D.setListEsp()
        # faire calculs selon l'etat
        #etat=self.getEtat();
        self.allGlistCalcNull();self.initOpt()
##        l1=['Aquifere','Ecoulement','Transport']
##        if etat in l1:
##            l2 = l1[:l1.index(etat)+1]
##            for i in range(len(l2)):
##                c=self.doAction(l2[i],'Run');
        # m a jour liste choix de paramGui
        
    def setOptions(self):
        """if the file options is here, read it and get the options for the specific file"""
        fi = self.project[0] + os.sep + 'options.txt'
        keyw=['User_species','Chemistry_solutions','end'];
        curkw='';bufr=[]
        try:
            f1=open(fi,'r')
            for l1 in f1:
                l1=l1.strip();
                if len(l1)==0:continue
                if l1[0]=='#':continue
                if l1 in keyw:
                    if curkw=='User_species': self.setUserEsp(bufr)
                    elif curkw=='Chemistry_solutions': self.setChemSolutions(bufr)
                    curkw=l1;bufr=[]
                else : bufr.append(l1)
        except IOError: return

    def setUserEsp(self,bufr):
        listE=[[],[]]
        for l1 in bufr:
            if l1.rfind('=')>-1:
                l2=l1.split('=');
                listE[0].append(l2[0]);listE[1].append(l2[1])
        self.PHT3D.setUserEsp(listE)
        if self.gui!=None: self.gui.afficheTree.setNames('PHT3D_User_L',listE[0])
        
    def setChemSolutions(self,dicData):
        rows,dataIn=dicData['lignes'],dicData['data']
        nl,nc=shape(dataIn);data=[]
        for i in range(nl):
            a=[True];a.extend(list(dataIn[i,:]));data.append(a)
        cols=['C','Backgrd']
        cols.extend(['solu'+str(i+1) for i in range(len(data[0])-2)]);
        dic={'cols':cols,'data':data,'rows':rows};#print dic
        print len(cols),shape(data),data
        self.PHT3D.setSolutions(dic)

    def saveModel(self):
        dsk,chem = self.project[0].split(':')
        chem2=chem.split(os.sep)[1:];#os.chdir(dsk+':')
        #for n in chem2: os.chdir('\"'+n+'\"')
        filename = dsk+':'+chem+os.sep+self.project[1] + '.ipht'
        f1=file(filename,'w');str1='<ipht3ddoc>\n'
        for n in ['Aquifere','Ecoulement','Transport','PHT3D','Zones','Modele']: # tenir compte de l'etat
            dict0=self.getBase(n);#print 'model save',n,dict0
            str1+='<dict>\n<name>'+n+'</name>\n'
            for k in dict0.keys():
                str1 += '<key>\n<name>'+k+'</name>\n<content>'+str(dict0[k])+\
                    '</content>\n</key>\n'
            str1+='</dict>\n'
        str1+='</ipht3ddoc>'
        f1.write(str1);f1.close()
        
    def openTabFile(self,fullName):
        """ ouvre un fichier txt avec tabualtions sous forme ligne titre
        et nom variable a chauqe ligne, renvoie un dictionnaire sous forme
        d un tableau"""
        f1=open(fullName,'r'); #utils//
        tiCol=f1.readline().split('\t');tiCol=tiCol[1:]
        tiCol[-1]=tiCol[-1][:-1];nC=len(tiCol)
        dat0=[];tiL=[]
        for ll in f1:
            l1=ll.split('\t');#l1[-1]=l1[-1][:-1]
            tiL.append(l1[0]);dat0.append(l1[1:])
        nl=len(tiL)
        data=zeros((nl,nC))*0.;#print 'in model',dat0
        for l in range(nl):
            for c in range(nC):
                data[l,c]=float(dat0[l][c])
        return {'cols':tiCol,'lignes':tiL,'data':data}
        
    def updateDict(self, Gl0,Gl1):
        """ on update Glist en conservnat a la fois ce qui est en plus dans
        Gl0 (version plus recente, et pour reaction les caracteristiques venant
        de Gl1 (modele ouvert)"""
        for k1 in Gl1:
            if Gl0.has_key(k1):
                for k2 in Gl1[k1]: # on cherche a remplacer les cles de Gl0 par Gl1
                    if Gl0[k1].has_key(k2):
                        for k3 in Gl1[k1][k2]:
                            if Gl0[k1][k2].has_key(k3):
                                Gl0[k1][k2][k3] = Gl1[k1][k2][k3]
                    else : Gl0[k1][k2]=Gl1[k1][k2]
        return Gl0
        
    def impVar(self,fullName,var):
        #zlist=self.openZonefile(fullName);
        Kgrid=genfromtxt(fullName);self.tmpImport[var]=fullName
        self.Aquifere.setVbase(var,Kgrid)

    def impZones(self,fullName,var):
        """ import a tabulated file with cols : 'name',name of zone,'value',
        value attached to the zone,'coord', and as many colums as coordinates
        organissed x1 y1 x2 y2...
        then add the zoens to the aquifer and visu"""
        f1=open(fullName,'r');
        name=[];val=[];coord=[];mil=[0];typeZone=3
        for ll in f1:
            l1=ll.split('\t');
            name.append(l1[1]);val.append(l1[3]);c0=l1[5:];a=[]
            for j in range(0,len(c0),2):
                a.append((float(c0[j]),float(c0[j+1])))
            coord.append(a)
        for i in range(len(name)):
            info = [var,self.Aquifere.getNbzone(var),mil];
            self.Aquifere.addZone(var,name[i],val[i],typeZone,info,coord[i])
            self.visu.curVar=var
            self.visu.addZone(mil,name[i],val[i],typeZone,info,coord[i])
        self.visu.redraw()

    def baseExport(self,lvariable,lsuffixe):
        pPath, pName = self.getProject()
        for i in range(len(lvariable)):
            f1 = open(pPath+os.sep+pName+lsuffixe[i]+'.txt','w')
            savetxt(f1,lvariable[i])
            f1.close()
        
    def export(self,nom,var=None):
        if nom=='Vitesses':
            vue=self.gui.afficheTree;ec=self.Ecoulement;
            it=vue.curItemps; ori=vue.curOri; plan = vue.curPlan
            if ori=='Z': v = ec.getMfVitesse(it);v1=v[0][plan,:,:];v2=v[1][plan,:,:]
            if ori=='Y': v = ec.getMfVitesse(it);v1=v[0][:,plan,:];v2=v[1][:,plan,:]
            if ori=='X': v = ec.getMfVitesse(it);v1=v[0][:,:,plan];v2=v[1][:,:,plan]
            self.baseExport([v1,v2],['V1','V2'])
        elif nom in ['Transport','PHT3D']:self.exportRP3D(nom)
        else: self.exportVariable(nom)
        self.gui.OnMessage(nom+" exporte")

    def exportVariable(self,var):
        """ exporte une variable a partir de l'evt du menu"""
        vbase = self.Aquifere.getVbase(var)
        data = obj2mat(self.Aquifere,var,0,vbase)
        data = data[-1::-1,:]*1.
        self.baseExport([data],[var])
        self.gui.OnMessage("Variable exporte")
        
    def exportRP3D(self,typ):
        """ export currently visualized data from pht3d or Rt3d for transport"""
        vue=self.gui.afficheTree
        it=vue.curItemps;ori=vue.curOri; plan = vue.curPlan
        espece = 'Transport'
        if typ=='PHT3D': espece = self.PHT3D.getEactuel()
        conc = self.getObject(typ,'','',it,plan,ori)[2]
        self.baseExport([conc],[typ+str(it)+str(espece)])                     

    def onPtObs(self,typ,iper,group,zname,esp):
        """ get the values at observation zones, esp can be a list of species names"""
        # typ is breakthrough or profile
        #print 'model ptobs',iper
        aqui=self.getGroupe('Aquifere'); grd = aqui.getFullGrid();
        x0,dx,nx,y0,dy,ny=grd['x0'],grd['dx'],grd['nx'],grd['y0'],grd['dy'],grd['ny']
        grx=concatenate([array(x0,ndmin=1),x0+cumsum(dx)],axis=0)
        gry=concatenate([array(y0,ndmin=1),y0+cumsum(dy)],axis=0);
        
        if typ[0]=='X': #XYplot
            zlist=aqui.getZoneList('Observation');ix=[];iy=[]
            for zo in zlist:
                xy=zo.getXy();x,y = zip(*xy)
                a,b,c = zone2index(x,y,x,grx,gry,nx,ny)
                ix.append(a[0]);iy.append(b[0])
            ix2=array(ix);iy2=grd['ny']-array(iy)-1;iz2=ix2*0.
        else:    
            zo=aqui.getZoneByName('Observation',zname);xy=zo.getXy();x,y = zip(*xy)
            ix,iy,a = zone2index(x,y,x,grx,gry,nx,ny) ;#print 'model ptobs ix iy',ix,iy
            zmil=zo.getInfo()[2] # a list of media in obs zone
            iy1=grd['ny']-iy-1;ix2=[];iy2=[];iz2=[]
            for m in zmil:
                llay=aqui.mil2lay(m);
                for l in llay:
                    ix2.extend(ix);iy2.extend(iy1);iz2.extend([l]*len(ix))

        t0 = self.Ecoulement.getListTemps()[1:]
        if typ[0]=='B': iper=range(len(t0)) # breakthrough
        else : iper = [iper]
        exec('pt=self.'+group+'.getPtObs(iy2,ix2,iz2,iper,esp)'); # irow,icol,ilay
        f0=self.Ecoulement.getPtObs(iy2,ix2,iz2,iper,'flux')[0];
        flux=sqrt(f0[0]**2.+f0[1]**2.);flux[flux==0]+=1e-5;
        if esp[0]=='Charge': typ=typ[0]+'0'
        if esp[0]=='Flux': typ=typ[0]+'2'
        if typ[0]=='B':  # Breakthrough
            p1=zeros((len(t0),len(pt)));labls=['temps']; # pt species to plot
            for i in range(len(pt)):
                if esp[0]=='Flux': pt[i]=1. # to show the flux
                if typ[1]=='0': p1[:,i]=mean(pt[i],axis=1); #conc
                if typ[1]=='1': p1[:,i]=mean(pt[i]*flux,axis=1)/mean(flux,axis=1) # weighted conc
                if typ[1]=='2': p1[:,i]=sum(pt[i]*flux,axis=1); #flux
                labls.append(esp[i])
            return t0,p1,labls
        elif typ[0]=='P':  # Profile
            xzon=grx[ix];yzon=gry[iy];
            d0=sqrt((xzon-xzon[0])**2.+(yzon-yzon[0])**2.)
            p1=zeros((len(d0),len(pt)));labls=['distance']
            for i in range(len(pt)):
                if esp[0]=='Flux': pt[i]=1. # to show the flux
                if typ[1]=='0': p1[:,i]=pt[i]
                if typ[1] in ['1','2']: p1[:,i]=pt[i]*flux # weigthed conc=flux
                labls.append(esp[i])
            return d0,p1,labls
        elif typ[0]=='X': # XY plot
            mes=self.data['data'][:,0];
            p1=zeros((len(mes),1));p1[:,0]=pt[0];
            return mes,p1,'correl'
           
    

