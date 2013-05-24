import os
from phtDbase import *
from scipy import zeros
from MtphtWriter import *
from matplotlib.pylab import meshgrid

class Transport:
    """A class that gathers thhe actions for Mt3d, except writing that is left to
    rtphtwriter"""
    def __init__(self, model):
        self.model = model;self.aqui=self.model.Aquifere
        self.initBase()
        
    def initBase(self):
        self.Base= {}
        self.Base['Temps']=[('pas de temps',1.),('t final',10.)]
        self.Base['Transp']=[('aL',1.),('aT',.1),('aZ',0.),('Rf',1.)]
        self.Base['Methodes']=[('methode',-1),('nb courant',.75),('dt0',0.),('maxstrn',50000),
                ('max part',5000),('ndvfd',1)] 
        self.Base['Particules']=[('dceps',1e-5),('nplane',1),('npl',0),('nph',16),('np min',2),
                ('np max',32)]
        self.Base['Recharge']=[]
        self.Base['Solver']=[('out iter',1),('in iter',50),('solve',1),('ncrs',0),
                ('accel',1),('tolerance',1e-5),('print',0)]
        self.Base['options']=[('Type of diffusion',['simple',['simple','multiple']]),('Diffusion coeff (m2/s)',1e-10)]
        self.temp={}
        self.temp['period']=[0]  # liste de duree et conc de chque periode
        self.temp['run']=0  # Rt3d n'a pas tourne
        self.temp['write']=0 # Rt3d file not written
        self.Eactuel,self.Tactuel,self.Uactuel=0,0,'mmol/L'
        
    def getBase(self): return self.Base
    def setBase(self,base):
        self.Base = base
        if self.Base.has_key('Recharge')==False: self.Base['Recharge']=[]
        if self.Base.has_key('options')==False:
            self.Base['options']=[('Type of diffusion',['simple',['simple','multiple']]),
                    ('Diffusion coeff (m2/s)',1e-10)];return
        if len(self.Base['options'])==1:
            self.Base['options']=[('Type of diffusion',['simple',['simple','multiple']]),
                    ('Diffusion coeff (m2/s)',1e-10)]
    def getParm(self,nom):
        if nom=='Variable': return ['','Tr_Source','Tr_Rech']
        else: return self.Base[nom]
        
    def setParm(self,nom,lst2):
        if nom=='Recharge':
            lrech=[];self.aqui.delAllZones('Tr_Rech')
            for i in range(len(lst2)):
                znam=lst2[i][0]; conc=lst2[i][1];
                lrech.append((znam,conc))
                # add zone to model
                z=self.aqui.getZoneByName('Recharge',znam);
                xy=z.getXy();zform=z.getForme();info = ['Tr_Rech',i,[0]]
                self.aqui.addZone('Tr_Rech',znam,conc,zform,info,xy)
            self.Base[nom]=lrech
        else : self.Base[nom] = lst2
        self.Base[nom] = lst2
        
    def getParmDetail(self,categ,name):
        a=self.Base[categ];lparm,lval=zip(*a)
        ind=lparm.index(name)
        return lval[ind]
    
    def setParmDetail(self,name,val):
        plist=self.getParm('Transp')
        lname=zip(*plist)[0]
        if name in lname:
            ind=lname.index(name)
            plist[ind]=(name,float(val))
            self.setParm('Transp',plist)
            
    #def getVbase(self,nomv,mil): return 0.
    def getTactuel(self): return self.Tactuel
    def getEactuel(self): return self.Eactuel
    def getDiffuList(self):
        opt=self.Base['options']
        if opt[0][1][0]=='simple':
            return [opt[1][1]]
        else:
            la,lb=[],[]
            ld=opt[1][1]
            for i in range(len(ld)):
                a,b=ld[i].split()
                la.append(a);lb.append(b)
            return [la,lb]
    
    def doAction(self,nom):
        if nom=='Write':
            a=self.ecrireMP3();
            if a!=None: return ['Fichiers MT3D ecrits']
        if nom=='Run':
            dirFich = self.model.getProjectPath();
            if self.temp['write']==0 : return 'Fichiers non ecrtis'
            if self.model.getVarDensity() : add='swt_v4.exe" seawat.nam'
            else : add='mt3dms5b.exe" mt3d.nam'
            cmd = '"'+self.model.gui.mainDir+os.sep+'bin'+os.sep+add
            os.chdir(dirFich);os.system(cmd)
            self.temp['run']=1
        
    def getListTemps(self):
        tlist=self.model.Ecoulement.getListTemps()
        return tlist

    def getObject(self,nom,tag,itemps,plan,ori='Z'):
        #ramener un array de resultats :
        #nom : dans la liste des boites de visu, tag : valeur de liste nom
        [A,B]=self.aqui.getMeshCentre(ori,plan)        
        c0 = self.MP3dReader.lireUCN(self.aqui,'MT3D', itemps, 0)
        if c0==None: self.model.gui.OnMessage('pas de fichier')
        if self.aqui.getDim() in ['Xsection','Radial']:
            ori='Y';plan=0
        if ori=='Z':conc = c0[plan,:,:]
        elif ori=='Y':conc = c0[:,plan,:]
        elif ori=='X':conc = c0[:,:,plan];
        #print 'transp getobj',shape(A),shape(B),shape(c0),conc[50,35]
        return [A,B,conc]
    
    def setReader(self):
        pPath, pName = self.model.getProjectPath(),self.model.getProjectName()
        self.MP3dReader = MP3dReader(pPath, pName)
        
    def ecrireMP3(self):
        pPath, pName = self.model.getProjectPath(),self.model.getProjectName()
        fullPath = pPath+os.sep+pName
        a='copy  "'+fullPath+'.flo"  "'+pPath+os.sep+'mt3d.flo" /Y'
        #pName='MT3D';
        # os.system(unicode(a).encode("utf-8"))
        # temps et periodes prednre sleon le type de reaction ds trac ou reac
        #ecrire fichier
        t0 = self.model.Ecoulement.getParm('Temps');
        tf=float(t0[0][1]);dur=t0[1][1];nstep=t0[2][1]
        lstress=arange(dur,tf*1.01,dur);
        writer = MP3dWriter( self.model, pPath, pName)
        if self.model.getVarDensity() :
            listE = writer.WriteMP3dFile(self.aqui,'Traceur',self.Base,[lstress,nstep],'SEAWAT')
        else:
            listE = writer.WriteMP3dFile(self.aqui,'Traceur',self.Base,[lstress,nstep],'MT3D')
        self.MP3dReader = MP3dReader(pPath, pName)
        self.temp['write']=1
        return 'ok'

    def getPtObs(self,irow,icol,ilay,per,esp):
        """ per is a list of time steps, esp useless, for comaptibility with pht3d"""
        pto=self.MP3dReader.getPtObs(self.aqui,irow,icol,ilay,per,'MT3D')
        return [pto] # a list for compatibility with pht3d

