from calcAquifere import *
from scipy import *

class MfInterpreter:
    """this class allows to exchange data between ipht3d or qGIS format
    with Modflow, Mt3dms or pht3d formats
    the modflow.. writers call this class"""
    def __init__(self,model):
        self.model=model;self.aqui=model.Aquifere
        self.lstMflow=[('title','# title ','fixed'),('NCOL','nx','grid'),('DELR','dx','grid'),
                ('NROW','ny','grid'),('DELC','dy','grid'),
                ('NLAY','aqui.getNbCouches()','function'),
                ('LAYCBD','self.getStringLay(0)','function'),
                ('NPER','self.getNper()','function'),
                ('ITMUNI','4','fixed'),('LENUNI','2','fixed'),
                ('STRT','Potentiel',''),
                ('BOTM','self.getMur()','function'),
                ('TOP','self.getToit()','function'),
                ('PERLEN','self.getPerlen()','function'),
                ('NSTP','self.getNstp()','function'),
                ('TSMULT','self.getTsmult()','function'),
                ('SsTr','self.getSsTr()','function'),
                
                ('bas_opt','NO options','fixed'),
                ('IBOUND','self.getHeadBC()','function'),
                ('HNOFLO','100001','fixed'),
                ('STRT','Potentiel',''),

                ('IBCFCB','31','fixed'),('HDRY','0.05','fixed'),
                ('IWDFLG','0','fixed'),('WETFCT','1.0','fixed'),
                ('IWETIT','1','fixed'),('IHDWET','0','fixed'),
                ('Ltype','self.getLtype()','function'),
                ('TRPY','self.getStringLay(1.)','function'),
                ('Tran','self.getTran()','function'),
                ('Sf1','Emmagasin.',''),('Sf2','Porosite',''),
                ('HY','Permeabilite',''),('Vcont','Permeabilite',''),

                ('ILPFCB','0','fixed'),('HDRY','0.05','fixed'),
                ('NPLPF','0','fixed'),
                ('LAYTYP','self.getLaytyp()','function'),
                ('LAYAVG','self.getStringLay(1)','function'),
                ('CHANI','self.getStringLay(1)','function'),
                ('LAYVKA','self.getStringLay(0)','function'),
                ('LAYWET','self.getStringLay('+self.getLaycon()+')','function'),
                ('WETFCT','0.5','fixed'),('IWETIT','1','fixed'),
                ('IHDWET','0','fixed'),
                ('HK','Permeabilite',''),('VKA','Permeabilite',''),
                ('VKCB','Permeabilite',''),
                ('WETDRY','self.getWetDry()','function'),

                ('MXACTW','# ','fixed'),('IWELCB',' ','fixed'),
                ('WLayer','Forages','npoints'),

                ('NRCHOP','3','fixed'),('IRCHCB','0','fixed'),
                ('INRECH','1','fixed'),('INIRCH','0','fixed'),
                ('RECH','Recharge','1        0  \n'),
                
                ('MXITER','mxiter','flo'),('NPARM','nparm','flo'),
                ('SACCL','accel','flo'),('SHCLOSE','hclose','flo'),
                ('IPCALC','ipcalc','flo'),('WSEED','seed','flo'),
                ('IPRSIP','iprsip','flo'),
                
                ('ITER1','iter1','flo'),('NPCOND','npcond','flo'),('PACCL','accl','flo'),
                ('PHCLOSE','hclose','flo'),('RCLOSE','rclose','flo'),('RELAX','relax','flo'),
                ('NBPOL','nbpol','flo'),('IPRPCG','iprpcg','flo'),
                ('MUTPCG','mutpcg','flo'),('DAMP','damp','flo'),

                ('OACCL','accl','flo'),('OHCLOSE','Hclose','flo'),
                ('IPRSOR','iprsor','flo'),

                ('ITMX','itmx','flo'),('MXUP','mxup','flo'),
                ('MXLOW','mxlow','flo'),('MXBW','mxbw','flo'),
                ('IFREQ','ifreq','flo'),('MUTD4','mutd4','flo'),
                ('IPRD4','iprd4','flo'),('DACCL','accl','flo'),
                ('DHCLOSE','hclose','flo')
    
                ]
        
    def getParm(self,kwd):
        """to ask a value to ipht3d, by giving the keyword name"""
        parm,categ=self.getParmFromKwd(kwd);aqui=self.aqui
        grd=self.aqui.getGridForMf()
        if categ=='grid': val=grd[parm]
        elif categ=='function': exec('val='+parm)
        elif categ=='fixed': val=parm
        elif categ=='npoints': val=self.getPoints(parm)
        elif categ=='flo': val=self.model.Ecoulement.getParmDetail(parm)
        #print kwd,val
        return val

    def getArray(self,kwd):
        """to ask a vector or an array to ipht3d, by giving the keyword name"""
        #print kwd
        grd=self.aqui.getGridForMf()
        parm,categ=self.getParmFromKwd(kwd)
        if categ=='': arr=obj2matBlock(self.aqui,parm)
        elif categ=='grid': arr=grd[parm]
        else : exec('arr='+parm)
        return arr
    
    def getArrayPeriod(self,kwd,iper):
        """ask for an array at a given period, for variable arrays
        work only for the first layer up to now"""
        parm,head=self.getParmFromKwd(kwd)
        return head,obj2mat(self.aqui,parm,0,0,iper)
        
    def getPoints(self,parm):
        """to ask a list of points with corresponding values for a given
        period (take care for wells k is not considered here)"""
        grd = self.aqui.getFullGrid();
        x0,x1,dx,nx = grd['x0'],grd['x1'],grd['dx'],grd['nx']
        y0,y1,dy,ny = grd['y0'],grd['y1'],grd['dy'],grd['ny']
        xvect=concatenate([array(x0,ndmin=1),x0+cumsum(dx)],axis=0)
        yvect=concatenate([array(y0,ndmin=1),y0+cumsum(dy)],axis=0)
        zlist=self.aqui.getZoneTransient()[parm];np,nz=shape(zlist)
        irow,icol,ilay,izone=[],[],[],[]
        for iz in range(nz):
            zone=self.aqui.getZone(parm,iz);
            zmil=zone.getMil();zlay=[]
            for m in zmil: zlay.extend(self.aqui.mil2lay(m))
            nlay=len(zlay);
            xy=zone.getXy();x,y=zip(*xy);z=x*1
            ic,ir,a=zone2index(x,y,z,xvect,yvect,nx,ny)
            icol.extend(list(ic)*nlay)
            ir2=[ny-x-1 for x in ir];irow.extend(ir2*nlay);
            a=zlay*len(ic);a.sort();ilay.extend(a)
            izone.extend([iz]*len(ic)*nlay)
        if self.aqui.getDim() in ['Xsection','Radial']:
            ilay=irow*1;irow=[0]*len(ilay)
        nptot=len(ilay)*np;plist=[]
##        for ip in range(np):
##            res=[zlist[ip,iz] for iz in izone]
##            #val=zlist[ip,iz];res.extend([val]*nlay)
##            u=ones(len(ilay))
        if parm=='Forages': u=self.getPermScaled(ilay,irow,icol)
        else :u=1.
##            res=array(res)*u
##            plist.append([ilay,irow,icol,res])
        return nptot,[irow,icol,ilay,izone,u,zlist]
    
    def getPermScaled(self,ilay,irow,icol):
        """return the permeability for a list of layer, col rows scaled by the
        sum of permeability for this list"""
        #print 'mfinterp',ilay,icol,irow
        K=obj2matBlock(self.aqui,'Permeabilite')
        grd = self.aqui.getFullGrid();dx=grd['dx'];dy=grd['dy'];ny=grd['ny']
        ka=ones(len(ilay))*0.;#print shape(k),ilay,irow,icol
        for i in range(len(ilay)):
            if self.aqui.getDim() in ['Xsection','Radial']: surf=dx[icol[i]]*dy[ny-ilay[i]-1]
            else : surf=dx[icol[i]]*dy[irow[i]]
            ka[i]=K[ilay[i],irow[i],icol[i]]*surf
        return ka/sum(ka)
        
    def getParmFromKwd(self,kwd):
        """get the parameter in ipht3d corresponding to a keyword in Modflow"""
        #print kwd
        l1,l2,l3=zip(*self.lstMflow);
        indx=l1.index(kwd)
        return l2[indx],l3[indx]
    
    #****************** for DIS file *******************
    def getToit(self):
        if self.aqui.getDim() in ['Xsection','Radial']:
            grd=self.aqui.getFullGrid();return [grd['y0']+sum(grd['dy'])]
        else : return obj2matBlock(self.aqui,'Toit')[0]
    def getMur(self):
        if self.aqui.getDim() in ['Xsection','Radial']:
            grd=self.aqui.getFullGrid();b=grd['y0']+cumsum(grd['dy'])-grd['dy']
            return reshape(array(b[-1::-1]),(len(b),1,1)) #special shape
        else : return obj2matBlock(self.aqui,'Mur')
    def getNper(self): return len(self.aqui.getZoneTransient()['tlist'])-1
    def getPerlen(self):
        pers=self.aqui.getZoneTransient()['tlist'];pers=array(pers)
        return pers[1:]-pers[:-1]
    def getNstp(self):
        n=self.model.getParm('Ecoulement','Temps')[2][1]
        return [n]*self.getNper()
    def getTsmult(self): return [1.1]*self.getNper()
    def getSsTr(self):
        l1=['Tr']*self.getNper()
        if self.model.Ecoulement.get1stepSteady()=='oui': l1[0]='SS'
        return l1

    #****************** for BAS file *******************
    def getHeadBC(self): # get fixed BC from head zones
        mci = obj2matBlock(self.aqui,'CelluleInactive').astype('int')
        return mci-2*obj2matBlockNb(self.aqui,'Potentiel','BC')
    
    #****************** For BC6 file ******************
    def getNlay(self): return self.aqui.getNbCouches();
    def getLtype(self):
        nlay=self.getNlay();s=''
        tp = aqui.getTypeAq() #0 confine 1 libre
        if tp=='libre': laycon='1'
        else : laycon='0'
        s+='0'+laycon
        for l in range(1,nlay):
            if mod(l,38)==0: s+='\n'
            s+='0'+laycon # faire moyenne , lay confine ou non
        return s+'\n'
    def getTran(self):
        mk = obj2matBlock(self.aqui,'Permeabilite')
        ep=self.aqui.getEpais()
        return mk/ep
    
    #****************** For Lpf file ******************
    def getLaycon(self):
        tp = self.aqui.getTypeAq() #0 confine 1 libre
        if tp=='libre': return '1'
        else : return '0'
    
    def getLaytyp(self):
        nlay=self.getNlay();laycon=self.getLaycon()
        s=' '+laycon
        for l in range(1,nlay):
            if mod(l,38)==0: s+='\n'
            s+=' '+laycon # faire moyenne , lay confine ou non
        return s+'\n'
    def getStringLay(self,val):
        nlay=self.getNlay();s=' '+str(val)
        for l in range(1,nlay):
            if mod(l,38)==0: s+='\n'
            s+=' '+str(val)
        return s+'\n'
    def getWetDry(self):
        m = obj2matBlock(self.aqui,'Permeabilite')
        return m*0.+.05

