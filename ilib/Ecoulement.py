import os
#import iphtC1
from scipy import *
from modflowWriter import *
from matplotlib.pylab import meshgrid

class Ecoulement:
    """Classe contenant le calcul et le resultat de l'ecoulement
    """

    def __init__(self, model):
        self.model,self.gui = model,model.gui
        if self.gui!=None: self.traduit=self.gui.traduit
        self.aqui = model.Aquifere
        self.Base = {}
        self.Base['solverdict'] = [('solver',['pcg',['sip', 'sor', 'pcg', 'de4']])]
        #solveur utilise, propre au calcul de ModFlow
        self.Base['sip'] = [('mxiter',500),('nparm',5),('accel',1),('hclose',1e-9),
                ('ipcalc',0),('seed',1e-3),('iprsip',1)] # param base solver flow
        self.Base['sor'] = [('mxiter',500),('accl',1.),('Hclose',1e-10),('iprsor',0)]
        self.Base['pcg'] = [('mxiter',1),('iter1',3000),('npcond',1),('hclose',1e-10),
                ('rclose',1e-10),('relax',1.),('nbpol',2),('iprpcg',0),('mutpcg',2),('damp',1.)]
        self.Base['de4'] = [('itmx',1),('mxup',0),('mxlow',0),('mxbw',0),('ifreq',1),
                ('mutd4',2),('accl',1.),('hclose',1e-10),('iprd4',5)]
        self.Base['temps']=[('t final',10.),('Stress per. length',1.),('N step/periode',10)]
        self.Base['options']=[('Steady for 1st time step',['no',['no','yes']]),('ratio Kz/Kx',1.)]
        # Sauvegarde des parametres initiaux
        self.Base0 = self.Base.copy()

        # resultat des calculs Modflow
        self.mfHead = None
        self.mfVitesse = None

    #recupere sous forme de tableau a 2 tableau les noms et valeurs associees
    def getBase(self): return self.Base           
    def setBase(self,base):
        self.Base=base
        if 'options' not in base.keys():
            self.Base['options']=[('Steady for 1st time step',['no',['no','yes']]),('ratio Kz/Kx',1.)]
    def initBase(self): self.Base = self.Base0.copy()
    def getParm(self,nom):
        if nom=='Variable': return self.aqui.getVarList()
        elif nom=='SolvListe': return self.Base['solverdict']
        elif nom=='SolvName': return self.Base['solverdict'][0][1][0]
        elif nom=='Solver':
            solv_nom = self.Base['solverdict'][0][1][0]
            return self.Base[solv_nom]
        elif nom=='Temps': return self.Base['temps']
        else : return self.Base[nom]
        
    def getParmDetail(self,parm):
        solv=self.Base['solverdict'][0][1][0]
        l1,l2=zip(*self.Base[solv]);indx=l1.index(parm)
        return l2[indx]
    def get1stepSteady(self): return self.Base['options'][0][1][0]
    def setParm(self,nom,dic2):
        if nom=='SolvListe': self.Base['solverdict']= dic2
        elif nom=='Solver': 
            solv_nom = self.Base['solverdict'][0][1][0]
            self.Base[solv_nom] = dic2
        elif nom=='Temps': 
            self.Base['temps'] = dic2
            self.aqui.createZoneTransient()
        else : self.Base[nom]=dic2
    def getVbase(self,nomv,mil): return self.aqui.getVbase(nomv,mil)
    def getObject(self,nom,tag,itemps,plan,ori='Z'):
        [A,B]=self.aqui.getMeshCentre(ori,plan)
        if self.aqui.getDim() in ['Xsection','Radial']:
            ori='Y';plan=0
        if nom=='Charge':
            if self.getMfHead(0)==None: return None
            if ori=='Z':head = self.getMfHead(itemps)[plan,:,:]
            elif ori=='Y':head = self.getMfHead(itemps)[:,plan,:]
            elif ori=='X':head = self.getMfHead(itemps)[:,:,plan];
            return [A,B,head]
        elif nom=='Vitesse':
            if self.getMfVitesse(0)==None: return None
            v = self.getMfVitesse(itemps)
            if ori=='Z':
                v1=v[0][plan,:,:];v2=v[1][plan,:,:]
            elif ori=='Y':v1 = v[0][:,plan,:]; v2 = v[2][:,plan,:]
            elif ori=='X':v1 = v[1][:,:,plan]; v2 = v[2][:,:,plan]
            v1=v1[:,:-1]/2+v1[:,1:]/2;v2=v2[:-1,:]/2+v2[1:,:]/2
            return [A,B,v1,v2]  # porosite??

    def doAction(self,action):
        if action=='Write':
            pPath, pName = self.model.getProjectPath(),self.model.getProjectName()
            mfDir = self.model.mainDir+os.sep+'bin'
            a=self.modflowWrite(mfDir,pPath,pName,self.model.Aquifere)
            if a!=None and self.model.gui!=None: return [self.traduit('Fichiers ecrits')]
            
        if action=='Run':
            if self.model.gui!=None:
                self.model.gui.afficheTree.OnSetItem('Ecoulement','Charge','B',False)
            # execution de modflow
            pPath, pName = self.model.getProjectPath(),self.model.getProjectName()
            mfDir = self.model.mainDir+os.sep+'bin'
            comment = self.modflowRun(mfDir,pPath,pName,self.model.Aquifere)
            #self.model.gui.afficheTree.OnSetItem('Ecoulement','Flux','B',False)
            #self.model.gui.afficheTree.OnSetItem('Ecoulement','Particules','B',False)
            self.model.setGlistParm('Ecoulement','Vitesse','calc',0)
            self.model.setGlistParm('Ecoulement','Charge','calc',0)
            return comment
        
    def setModflow(self, listmflow):
        """ modifie charge et vitesse apres calcul modflow"""
        self.mfHead = listmflow[0]
        self.mfVitesse = listmflow[1]

    def getMfHead(self,itemps):
        self.mfHead = self.mfReader.ReadHeadFile(self.aqui,itemps);
        return self.mfHead

    def getMfVitesse(self,itemps):
        self.mfVitesse = self.mfReader.ReadFloFile(self.aqui,itemps);
        return self.mfVitesse
        
    def getListTemps(self):
        return self.model.Aquifere.getZoneTransient()['tlist']
        
    def initParm(self):
        self.Base = self.Base0.copy()

    def calcParticule(self,xp0,yp0):
        """ calcule la position d'une particule a partir de pt de depart x0,y0
        puis represente la trajectoire dans la visu"""
        vxvy = self.getMfVitesse(0); # pas transitoire pour l'instant
        poro = float(self.model.Aquifere.getVbase('Porosite'))
        vx = vxvy[0]/poro; vy=vxvy[1]/poro; # attention vx ici n layers pas ds calc
        vx1=vx[0][-1::-1,:];vy1=vy[0][-1::-1,:]
        grd  = self.model.Aquifere.getFullGrid()
        clim = self.model.Aquifere.getClimP();
        dx=array(grd['dx']);dy=array(grd['dy']);
        data = array([grd['x0'],grd['y0'],xp0,yp0])
        #[xp,yp,tp,cu1,nt] = iphtC1.calcPart1(data,dx,dy,vx[0],vy[0],clim)
        [xp,yp,tp,cu1,nt] = self.calcPart(data,dx,dy,vx[0],vy[0],clim)
        #print xp,yp,tp,cu1,nt
        return [xp[:nt],yp[:nt],tp[:nt]]
        
    def modflowWrite(self,mfDir,pPath,pName,aqui):
        aqui.makeZblock()
        mflowWriter = ModflowWriter(pPath,pName)
        mflowWriter.WriteModflowFile(aqui,self,self.model)
        return 'ok'

    def modflowRun(self,mfDir,pPath,pName,aqui):        
        tabRes = [];curDir = os.getcwd();os.chdir(pPath);
        lf = os.listdir(pPath);
        if pName+'.nam' not in lf: return 'Fichiers non ecrits'
        if os.name == 'nt':
            exec_name = '"'+mfDir+os.sep+'mf2k_PMwin.exe"'
        else :
            exec_name = mfDir+os.sep+'mf2k '

        a=exec_name+' '+pName+'.nam'
        try :
            b=unicode(a).encode("utf-8")
        except UnicodeEncodeError:
            return 'Caracteres genants dans repertoire'
        p=os.popen(b,'r')
        while 1:
            line=p.readline()
            if not line: break
            tabRes.append(line)
            
        p.close();os.chdir(curDir)
        self.mfReader = ModflowReader(pPath,pName)
        #tabRes.append('\n divergence \% : a faire ') #+str(bal))
        return tabRes
    
    def setReader(self):
        pPath, pName = self.model.getProjectPath(),self.model.getProjectName()
        self.mfReader = ModflowReader(pPath,pName)
    
    def getPtObs(self,irow,icol,ilay,iper,esp):
        """ per is a list of time steps and esp a list too"""
        pto=self.mfReader.getPtObs(self.aqui,irow,icol,ilay,iper,esp[0])
        return [pto] # a list for compatibility with pht3d
    
    def calcPart(self,datai,dxi,dyi,vxi,vyi,clim):
        eps=1.e-6;cst1=5.e-5;
        x0=datai[0];y0=datai[1];xp0=datai[2];yp0=datai[3];
        ny,a=shape(vxi);nx=a-1;nt=int(max(nx,ny)*1.7) # mod nx
        xg=zeros((nx+1));yg=zeros((ny+1));xg[0]=x0;yg[0]=y0;
        for i in range(1,nx+1): xg[i] = xg[i-1]+dxi[i-1]; # mod dx(i) -> dx(i-1)
        for i in range(1,ny+1): yg[i] = yg[i-1]+dyi[i-1]; # pareil dy

        #* debut des calculs */
        xp=zeros((nt+1));yp=xp*0.;tp=xp*0.;cu1=xp*0.;
        it = 0;xp[0]=xp0;yp[0]=yp0;tp[0]=0.;ptin=1;
        while ((it<nt) and (ptin==1)):
            it+=1
            dxc = 0.; dyc = 0.;dt = 0.;
            dist=xg[nx-1]-x0;jp=0;
            for j in range(nx):
                a=xp[it-1]-xg[j]
                if ((a<dist)and(a>=0.)):dist=a;jp=j;
            dx=dxi[jp];

            dist=yg[ny-1]-x0;ip=0;
            for i in range(ny):
                a=yp[it-1]-yg[i];
                if ((a<dist)and(a>=0.)):dist=a;ip=i;
            dy=dyi[ip];
            
            cl = clim[ip,jp];
            if ((jp<nx)and(jp>0)and(ip<ny)and(ip>0)and(cl>0))or(it<5): ptin=1
            else : ptin=0
            vx1 = vxi[ip,jp];vx2 = vxi[ip,jp+1];      
            vy1 = vyi[ip,jp];vy2 = vyi[(ip+1),jp];
            Ax = (vx2-vx1)/dx;vxm = 2*vx1-vx2;
            Ay = (vy2-vy1)/dy;vym = 2*vy1-vy2;

            x0m = (xp[it-1]-xg[jp]+dx);
            y0m = (yp[it-1]-yg[ip]+dy);
            vxp0 = vxm+Ax*x0m; vyp0 = vym+Ay*y0m;
            sensx = sign(vxp0);sensy = sign(vyp0)
            #print xp0,yp0,ip,jp,vx1,vx2,Ax,vxm,x0m,vxp0,sensx
            #* on differencie les cas */
            if ( (abs(vy1)+abs(vy2)) < ((abs(vx1)+abs(vx2))*cst1) ): # sens x
                dt = ((1.5+0.5*sensx)*dx-x0m)/vxp0*(1.+eps);
                dxc = vxp0*dt; dyc = 0;
            elif ( (abs(vx1)+abs(vx2)) < ((abs(vy1)+abs(vy2))*cst1) ): # sens y
                dt = ((1.5+0.5*sensy)*dy-y0m)/vyp0*(1.+eps);
                dyc = vyp0*dt; dxc = 0;
            else :
                lb1 = (vxp0-vxm)/x0m;
                lb2 = (vyp0-vym)/y0m;
                ax1 = max((lb1*dx+vxm)/vxp0,eps);
                ax2 = max((lb1*dx*2+vxm)/vxp0,eps);
                ay1 = max((lb2*dy+vym)/vyp0,eps);
                ay2 = max((lb2*dy*2+vym)/vyp0,eps);
                dtx1 = log(ax1)/lb1;dtx2 = log(ax2)/lb1;dtx = max(dtx1,dtx2);
                dty1 = log(ay1)/lb2;dty2 = log(ay2)/lb2;dty = max(dty1,dty2);
                if (dtx<=0) : dtx=1.e5; 
                if (dty<=0) : dty=1.e5; 
                dt = min(dtx,dty)*(1.+eps);
                dxc = ( vxp0*exp(lb1*dt)-vxm )/lb1-x0m; 
                dyc = ( vyp0*exp(lb2*dt)-vym )/lb2-y0m;
            #* mis a jour des matrices */
            #print xp[it-1],dxc,xp[it-1]+dxc,yp[it-1],dyc,yp[it-1]+dyc
            cu1[it] = cu1[it-1] + sqrt(dxc*dxc+dyc*dyc);
            xp[it] = xp[it-1] + dxc;
            yp[it] = yp[it-1] + dyc;
            tp[it] = tp[it-1] + dt;
        return xp,yp,tp,cu1,it
