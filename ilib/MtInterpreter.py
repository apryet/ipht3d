from calcAquifere import *
from scipy import *

class MtInterpreter:
    """this class allows to exchange data between ipht3d or qGIS format
    with Modflow, Mt3dms or pht3d formats
    the mtpht.. writers call this class
    opt is Transport, SEWAT or PHT3D"""
    def __init__(self,model,opt):
        self.model=model;
        self.aqui,self.transport,self.pht3d=model.Aquifere,model.Transport,model.PHT3D
        self.opt=opt
        grd = self.aqui.getFullGrid();dcol = grd['dx']
        if self.aqui.getDim()=='Radial': self.radfact=(cumsum(dcol)-array(dcol)/2)*6.25
        self.lstMt3d=[('title','#ti1\nti2','fixed'),
                ('NLAY','self.getNlay()','function'),
                ('NCOL','nx','grid'),('NROW','ny','grid'),
                ('NPER','self.getNper()','function'),
                ('NCOMP','self.getMNcomp(\'n\')','function'),
                ('MCOMP','self.getMNcomp(\'m\')','function'),
                ('TUNIT','1','fixed'),('LUNIT','1','fixed'),('MUNIT','1','fixed'),
                ('TRNOP','T T T F T F F F F F \n','fixed'),
                ('LAYCON','self.getStringLay(0)','function'),
                ('DELR','dx','grid'),('DELC','dy','grid'),
                ('HTOP','self.getToit()','function'),                
                ('DZ','self.getDz()','function'),
                ('PRSTY','Porosite',''),
                ('ICBUND','self.getBC()','function'),
                ('SCONC','self.getConc(\'main\')','function'),
                ('CINACT','  1E+30 ','fixed'),('THKMIN','.01 ','fixed'),
                ('IFMTCN','0','fixed'),('IFMTNP','0','fixed'),
                ('IFMTRF','0','fixed'),('IFMTDP','0','fixed'),
                ('SAVUCN','T','fixed'),
                ('NPRS','self.getNper()','function'),
                ('TIMPRS','self.getPerTimes()','function'),
                ('NOBS','0','fixed'),('NPROBS','1','fixed'),
                ('CHKMAS','T','fixed'),('NPRMAS','0','fixed'),
                ('PERLEN','self.getPerlen()','function'),
                ('NSTP','self.getNstp()','function'),
                ('TSMULT','self.getTsmult()','function'),
                ('DT0','self.getNpval(0.)','function'),
                ('MXSTRN','self.getNpval('+self.getMxstrn()+')','function'),
                ('TTSMULT','self.getNpval(1.)','function'),('TTSMAX','self.getNpval(0.)','function'),

                ('MIXELM',('Methodes','methode'),'trans'),
                ('PERCEL',('Methodes','nb courant'),'trans'),
                ('MXPART',('Methodes','max part'),'trans'),
                ('NADVFD',('Methodes','ndvfd'),'trans'),
                ('ITRACK','3','fixed'),('WD','0.5','fixed'),
                ('DCEPS',('Particules','dceps'),'trans'),('NPLANE',('Particules','nplane'),'trans'),
                ('NPL',('Particules','npl'),'trans'),('NPH',('Particules','nph'),'trans'),
                ('NPMIN',('Particules','np min'),'trans'),('NPMAX',('Particules','np max'),'trans'),
                ('INTERP','1','fixed'),
                ('NLSINK',('Particules','nplane'),'trans'),('NPSINK',('Particules','nph'),'trans'),
                ('DCHMOC',('Particules','dceps'),'trans'),

                ('IMDIFF','self.isMultiDiff()','function'),
                ('AL','self.getAl()','function'),
                ('TRPT','self.getTrpt()','function'),
                ('TRPV','self.getTrpv()','function'),
                ('DMCOEF','self.getDmcoef()','function'),

                ('FWEL','T','fixed'),('FDRN','F','fixed'),
                ('FRCH','self.getFrch()','function'),
                ('FEVT','F','fixed'),('FRIV','F','fixed'),('FGHB','F','fixed'),
                ('MXSS','self.getNbPoints(\'Transport\')','function'),
                ('INCRCH',' ','fixed'),
                ('CRCH','self.getConc(\'rech\')','function'),
                ('INCEVT','0','fixed'),
                ('NSS',' ','fixed'),
                ('KSS','Transport','npoints')
                
                ]
        
    def getParm(self,kwd):
        """to ask a value to ipht3d, by giving the keyword name"""
        parm,categ=self.getParmFromKwd(kwd);aqui=self.aqui;
        grd=self.aqui.getGridForMf()
        if categ=='grid': val=grd[parm]
        elif categ=='function': exec('val='+parm)
        elif categ=='fixed': val=parm
        elif categ=='npoints': val=self.getPoints(parm)
        elif categ=='trans': val=self.model.Transport.getParmDetail(parm[0],parm[1])
        #print kwd,val
        return val

    def getArray(self,kwd):
        """to ask a vector or an array to ipht3d, by giving the keyword name"""
        #print kwd
        grd=self.aqui.getGridForMf()
        parm,categ=self.getParmFromKwd(kwd);aname=parm
        if categ=='': arr=obj2matBlock(self.aqui,parm)
        elif categ=='grid': arr=grd[parm]
        else : exec('arr,aname='+parm)
        return arr,aname
    
    def getArrayPeriod(self,kwd,iper):
        """ask for an array at a given period, for variable arrays
        work only for the first layer up to now"""
        parm,a=self.getParmFromKwd(kwd)
        arr,a=self.getConc('rech',iper)
        return  arr

    def getNbPoints(self,var):
        mP=obj2matBlockNb(self.aqui,'Potentiel','BC');nlay,ny,nx=shape(mP)
        mT=obj2matBlockNb(self.aqui,var,'zon');
        ztr=self.aqui.getZoneTransient()
        nz=self.aqui.getNbzone(var);nper=self.getNper()
        mxss=0
        for iz in range(nz):
            if iz not in ztr['zlist'][var]: mT[mT==iz+1]=0
        for ip in range(nper):
            for l in range(nlay):
                mxss+= sum(sum(mP[l])); # pts ou pot impose
                if ztr['Transient'].has_key(var):
                    if ztr['Transient'][var]==False: continue #if no transient zone do not write
                a,b=where(mT[l]>0) # counts pts in transient zone
                mxss += len(a)# print nss[ip]
        return mxss
        
    def getPointsPer(self,var,iper):
        """to ask a list of points with corresponding values for a given
        period"""
        ztr=self.aqui.getZoneTransient();
        ilay,irow,icol,typ,res=[],[],[],[],[];
        if var=='MT3D': var='Transport'
        if ztr['Transient'][var]==False: return [ilay,irow,icol,typ,res]
        zlist=ztr[var];np,nz=shape(zlist);
        grd = self.aqui.getFullGrid();
        x0,x1,dx,nx = grd['x0'],grd['x1'],grd['dx'],grd['nx']
        y0,y1,dy,ny = grd['y0'],grd['y1'],grd['dy'],grd['ny']
        xvect=concatenate([array(x0,ndmin=1),x0+cumsum(dx)],axis=0)
        yvect=concatenate([array(y0,ndmin=1),y0+cumsum(dy)],axis=0)
        wells=obj2matBlockNb(self.aqui,'Forages','BC')
        BC,n = self.getBC()
        if self.opt=='PHT3D': self.createConcStrings()
        for iz in range(nz):
            zone=self.aqui.getZone(var,iz);
            if zone.getInfo()[3]!='Transitoire': continue
            zmil=zone.getMil();il=[]
            for m in zmil: il.extend(self.aqui.mil2lay(m))
            nlay=len(il);
            xy=zone.getXy();x,y=zip(*xy);z=x*1
            ic,ir,a=zone2index(x,y,z,xvect,yvect,nx,ny)
            ir2=[ny-x-1 for x in ir];
            if self.aqui.getDim() in ['Xsection','Radial']:
                il=ir2*1;nlay=1;ir2=[0]*len(il);ilay.extend(il)
            else :
                a=il*len(ic);a.sort();ilay.extend(a)
            icol.extend(ic*nlay);irow.extend(ir2*nlay);
            ty=1;
            if BC[il[0],ir2[0],ic[0]]==-1: ty=-1
            if wells[il[0],ir2[0],ic[0]]==1: ty=2
            typ.extend([ty]*(len(ic)*nlay))
            val=zlist[iper,iz]
            if self.opt=='PHT3D': val=self.concStrings[int(val/1000)]
            else : val=str(val).rjust(10)
            res.extend([val]*(len(ic)*nlay))
        #print len(ilay),len(irow),len(typ)
        return [ilay,irow,icol,typ,res]
    
    def getParmFromKwd(self,kwd):
        """get the parameter in ipht3d corresponding to a keyword in MT3D or PHT3D"""
        #print kwd
        l1,l2,l3=zip(*self.lstMt3d);
        indx=l1.index(kwd)
        return l2[indx],l3[indx]
    
    #****************** for BTN file *******************
    def getToit(self):
        if self.aqui.getDim() in ['Xsection','Radial']:
            grd=self.aqui.getFullGrid()
            return [grd['y0']+sum(grd['dy'])],'top'
        else : return obj2matBlock(self.aqui,'Toit')[0],'top'
    def getDz(self):
        if self.aqui.getDim() in ['Xsection','Radial']:
            grd=self.aqui.getFullGrid();b=grd['dy']
            return reshape(array(b[-1::-1]),(len(b),1,1)),'dz' #special shape
        else :
            return self.aqui.getEpais(),'dz'
    def getNper(self): return len(self.aqui.getZoneTransient()['tlist'])-1
    def getMNcomp(self,name):
        if self.opt=='MT3D': return 1
        else :
            listE=self.model.PHT3D.getListEsp()
            m=0;im=0
            for e in ['k','i']: m+=len(listE[e])
            for e in ['kim','p','e','s','kp']: im+=len(listE[e])
            if name=='m': return m-2  # -2 for pH and pe
            elif name=='n' : return m+im
    def getPerTimes(self):
        t=self.aqui.getZoneTransient()['tlist'];s=''
        for i in range(len(t)):
            if (i>0)and(i-(i/8)*8==0): s+='\n'
            s+=' %9.3e'%(t[i])#s+='{:9.3e}'.format(float(t[i]))+' '
        s+='\n'
        return s
    def getPerlen(self):
        pers=self.aqui.getZoneTransient()['tlist'];pers=array(pers)
        return pers[1:]-pers[:-1],'perlen'
    def getNstp(self):
        n=self.model.getParm('Ecoulement','Temps')[2][1]
        return [n]*self.getNper(),'nstp'
    def getTsmult(self): return [1.1]*self.getNper(),'tsmult'
    def getNpval(self,val): return [val]*self.getNper(),'npval'
    def getMxstrn(self):
        return str(self.model.Transport.getParmDetail('Methodes','maxstrn'))

    def getBC(self): # get fixed BC from head zones
        mci = obj2matBlock(self.aqui,'CelluleInactive').astype('int')
        opt=self.opt*1;
        if opt=='MT3D': opt='Transport'
        return mci-2*obj2matBlockNb(self.aqui,opt,'BC'),'BC'
    
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
    
    #****************** layers characteristics ******************
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

    def getAl(self):
        nl=self.getNlay()
        aL=[self.model.Transport.getParmDetail('Transp','aL')]*nl
        arr=array(aL)
        return reshape(arr,(nl,1,1)),'aL'
    def getTrpt(self):
        aL=self.model.Transport.getParmDetail('Transp','aL')
        return [float(self.model.Transport.getParmDetail('Transp','aT'))/aL],'aT'
    def getTrpv(self):
        aL=self.model.Transport.getParmDetail('Transp','aL')
        return [float(self.model.Transport.getParmDetail('Transp','aZ'))/aL],'aZ'
    def isMultiDiff(self):
        lDiff=self.model.Transport.getDiffuList()
        if len(ldiff)==1: return ' '
        else : return '$MultiDiffusion   \n'
    def getDmcoef(self):
        # get diffusion coef for simple or mult
        lDiff=self.model.Transport.getDiffuList()
        nlay=self.getNlay()
        u=self.aqui.getParm('Unites');d0,d1=u[0][1];t0,t1=u[1][1]
        idi=d1.index(d0);mudi=[1e3,1,1e-2];
        iti=t1.index(t0);muti=[365*86400,86400,3600,60,1]
        if len(lDiff)==1:
            D=float(lDiff[0])*muti[iti]/mudi[idi]**2.
            return '        0  '+str(D)+' \n'
        else :
            lesp=self.model.PHT3D.getListEsp();s=''
            ia=lDiff[0].index('all');
            Dall=float(lDiff[1][ia])*muti[iti]/mudi[idi]**2.
            for k in ['k','i','kim','p','e','s','kp']:
                for esp in lesp[k]:
                    if esp in lDiff[0]:
                        ie=lDiff[0].index(esp);
                        D=float(lDiff[1][ie])*muti[iti]/mudi[idi]**2.
                    else : D=Dall*1
                    for l in range(nlay):
                        s+='        0       '+str(D)+'    \n'
            return s
        
    def getFrch(self):
        flagR='F'
        if self.aqui.getNbzone('Recharge')>0 or self.aqui.getVbase('Recharge',0)!=0.: flagR='T'
        print flagR
        return flagR
    def getFrch2(self):
        flagR=0
        if self.aqui.getNbzone('Recharge')>0. or self.aqui.getVbase('Recharge',0)>0.: flagR=1
        return flagR
    
    def getConc(self,typ,iper=0):
        if self.opt=='MT3D':
            if typ=='main': return [obj2matBlock(self.aqui,'Transport')],['Transp']
            elif typ=='rech': return [obj2matBlock(self.aqui,'Tr_Rech')[0]],['Rech']
        else :
            listC=[];names=[] # this will be the list of conc arrays and names of species
            listE=self.model.PHT3D.getListEsp()
            Chem=self.model.PHT3D.getParm('Chemistry')
            if typ=='main': phzone='PHT3D'
            elif typ=='rech': phzone='PH_Rech'
            pht=obj2matBlock(self.aqui,phzone,iper)
            if typ=='rech': pht=pht[0] # only the 1st layer
            dInd={'Solutions':pht/1000.,'Phases':mod(pht,1000)/100,'Exchange':mod(pht,100)/10,
                  'Surface':mod(pht,10)}
            short=['k','i','kim','p','e','s','kp']
            long=['Solutions','Solutions','Solutions','Phases','Exchange','Surface','Phases']
            for i in range(len(short)):
                kw=short[i];chm=Chem[long[i]];data=chm['data'];rows=chm['rows']
                for e in listE[kw]:
                    ncol=len(data[0]);names.append(e)
                    inde=rows.index(e)
                    m1=dInd[long[i]].astype('int')
                    if long[i]=='Phases': m0=pht*0.+float(data[inde][2])
                    else : m0=pht*0.+float(data[inde][1])
                    rcol=range(2,ncol)
                    if long[i]=='Phases': rcol=range(4,ncol,2)
                    if long[i]=='Surface': rcol=range(2,ncol-2)
                    for c in rcol:
                        m0[m1==(c-1)]=float(data[inde][c])
                    if self.aqui.getDim()=='Radial' and long[i]!='Solutions':
                        m0=m0*self.radfact
                    listC.append(m0)
            return listC,names
        
    def createConcStrings(self):
        """creates a string of concentrations for a pht3d zone value"""
        self.concStrings=[] # needed to remenber conc strings not to calculate each time
        listE=self.model.PHT3D.getListEsp()
        Chem=self.model.PHT3D.getParm('Chemistry')
        data=Chem['Solutions']['data'];rows=Chem['Solutions']['rows']
        ncol=len(data[0])
        for c in range(2,ncol):
            s=''
            for kw in ['k','i','kim']:
                for e in listE[kw]:
                    inde=rows.index(e)
                    s+=str(data[inde][c]).rjust(10)
            for kw in ['p','e','s','kp']:
                for e in listE[kw]:
                    s+='0.'.rjust(10)
            self.concStrings.append(s)