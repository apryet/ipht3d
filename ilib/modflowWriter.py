from scipy import *
#import scipy.io.array_import as IOAscii
from pylab import load,save
from array import array as arr2
import os
from calcAquifere import *
from MfInterpreter import *
import MflowKeywords as Fkey

class ModflowWriter:
    
    def __init__(self, path, name):
        self.pPath = path
        self.pName = name
        self.fullPath = path+os.sep+name

    def CreateFile(self, extension, mode):
        filename = self.fullPath + extension
        file_descriptor = open(filename, mode)
        return file_descriptor

    def WriteModflowFile(self, aqui, ecoul, model):
        self.interpreter=MfInterpreter(model)
        nbfor = aqui.getNbzone('Forages')
        nbrech = aqui.getNbzone('Recharge')
        rech = abs(sign(aqui.getVbase('Recharge')))
        aqui.createZoneTransient()
        self.zoneTransient=aqui.getZoneTransient()
        self.tlist=self.zoneTransient['tlist'];
        self.radfact=1.
        if self.zoneTransient['Transient'].has_key('Potentiel'):
            self.zpTrans= self.zoneTransient['Transient']['Potentiel']
        else : self.zpTrans=False
        self.WriteNamFile(ecoul,nbfor,max(nbrech,rech))
        for n in ['dis','ba6','lpf']:
            self.writeFile(n);print n+' printed'
        #self.WriteLpfFile(aqui, ecoul)
        if nbfor>0: self.writeFile('wel');print 'wel printed'
        if nbrech>0 or rech>0: self.writeFile('rch');print 'rch printed'
        solv = ecoul.getParm('SolvName')
        self.writeFile(solv)
        self.WriteLmtFile()
        self.WriteOcFile(aqui,ecoul);#print 'mfwri wri',self.zpTrans
        if self.zpTrans==True:
            self.WriteChdFile(aqui)
        
    """ for the y dimension ipht3d matrices are the inverse of modflow ones
    for vectors, it is taken into account any time a y vector is written
    for matrices it is in the writeblock function"""
    #************************* fichier NAM ****************
    def WriteNamFile(self, ecoul, nbfor, recharge):
        f1 = self.CreateFile('.nam', 'w')
        solv = ecoul.getParm('SolvName')
        f1.write('LIST      6        ' + self.pName + '.lst\n')
        f1.write('DIS      10        ' + self.pName + '.dis\n')
        f1.write('LMT6      66       ' + self.pName + '.lmt\n')
        f1.write('BAS6      5        ' + self.pName + '.ba6\n')      
        #f1.write('BCF6      11       ' + self.pName + '.bc6\n') 
        f1.write('LPF      11       ' + self.pName + '.lpf\n') 
        f1.write(solv+'      19     '  + self.pName +'.'+solv+'\n')      
        f1.write('OC       22        ' + self.pName + '.oc\n')      
        f1.write('DATA(BINARY)     30        ' + self.pName + '.head\n')
        f1.write('DATA(BINARY)     31        ' + self.pName + '.budget\n')

        if nbfor>0: f1.write('WEL     20     ' + self.pName + '.wel\n')
        if recharge>0: f1.write('RCH     15     ' + self.pName + '.rch\n')
        if self.zpTrans:
            f1.write('CHD     35     ' + self.pName + '.chd\n')
        f1.close()

    #*********************** generic file writer ****************
    def writeFile(self,name):
        """to write any modflow file.
        reads the keyword file and prints all keywords by types : param (0D)
        vector (1D) array (2D). types are found by (dim1,dim2).."""
        f1=open(self.fullPath +'.'+ name,'w');alist=[]
        n1=Fkey.groups.keys();#print n1,name
        for n in n1:
            if n.split('.')[1]==name: llist=Fkey.groups[n]
        for ll in llist:
            cond=Fkey.lines[ll]['cond'];#print 'mflw 1',cond,self.testCondition(cond)
            if self.testCondition(cond)==False :continue
            kwlist=Fkey.lines[ll]['kw'];kw0=kwlist[0].split('(')[0]
            ktyp=Fkey.lines[ll]['type'];#print 'mfw',ktyp
            if ktyp in ['arr','vec']: arr=self.interpreter.getArray(kw0)
            if ktyp=='vec': # a vector
                self.writeVecModflow(arr,f1)
                exec('self.'+kw0+'='+str(arr[0]))
                
            elif ktyp=='string': # a string to print 
                s=self.interpreter.getParm(kw0);f1.write(s)
                exec('self.'+kw0+'='+s[:2])
                
            elif ktyp=='arr': # one array
                self.writeBlockModflow(arr,f1)
                
            elif ktyp=='parr': # one variable, p arrays: one for each period
                nper=self.interpreter.getNper()
                for ip in range(nper):
                    head,arr=self.interpreter.getArrayPeriod(kw0,ip)
                    f1.write(head);self.writeBlockModflow(arr,f1)
                    
            elif ktyp=='larr': #several variable written for each layer
                for k in kwlist:
                    a=k.split('(');
                    alist.append(self.interpreter.getArray(a[0]))
                    
            elif ktyp=='nvec': # list of periods or others
                vlist=[]
                for k in kwlist:
                    a=k.split('(')
                    vlist.append(self.interpreter.getArray(a[0]))
                nlines=len(vlist[0]);s=''
                for j in range(nlines):
                    for ik in range(len(kwlist)):
                        val=str(vlist[ik][j]);s+=val[:9].ljust(9)+' '
                    s+='\n'
                f1.write(s)
            elif ktyp=='npoints': # points on the grid
                nptot,plist=self.interpreter.getParm(kw0)
                f1.write(str(nptot)+'\n');
                ir,ic,il,izone,kscal,val=plist;np,nz=shape(val)
                for ip in range(np):
                    s=str(len(il))+'\n'
                    for i in range(len(il)):
                        s+=str(il[i]+1).ljust(10)+str(ir[i]+1).ljust(10)+str(ic[i]+1).ljust(10)
                        v=val[ip,izone[i]]*kscal[i]
                        s+='%9.3e \n'%v #str(v).ljust(10)+'\n'
                    f1.write(s)
            else : # classical parameters
                for k in kwlist:
                    val=str(self.interpreter.getParm(k));
                    try : int(val);exec('self.'+k+'='+val)
                    except ValueError: a=None
                    f1.write(val[:9].ljust(10)) #' %9.3e'%float(val)
                f1.write('\n')
        if len(alist)>0: # write the arrays by layer saved in a list previously
            nlay=self.interpreter.getNlay()
            for il in range(nlay):
                for ik in range(len(alist)):
                    #print il,ik,alist[ik][il]
                    self.writeMatModflow(alist[ik][il],f1)
        f1.close()
        
    #**************** test condition **********************
    def testCondition(self,cond):
        """ test if the condition is satisfied"""
        a=True
        if cond!='':
##            if len(cond.split('+'))>1:
##                cond=cond.replace('+','+self.');
            if len(cond.split('and'))>1:
                c1=cond.split('and'); c2='(self.'+c1[0].strip()+')'
                for i in range(1,len(c1)): c2+=' and (self.'+c1[i].strip()+')'
            elif len(cond.split('or'))>1:
                c1=cond.split('or'); c2='(self.'+c1[0]+')'
                for i in range(1,len(c1)): c2+=' or (self.'+c1[i].strip()+')'
            else : c2='self.'+cond
            exec('a='+c2);#print 'cond',c2,a;
        if a or cond=='': return True
        return False  
        
    #************************ file for transient head (CHD)*************************************
    def WriteChdFile(self,aqui):
        f1 = self.CreateFile('.chd', 'w') 
        grd = aqui.getFullGrid();
        x0,x1,dx,nx = grd['x0'],grd['x1'],grd['dx'],grd['nx']
        y0,y1,dy,ny = grd['y0'],grd['y1'],grd['dy'],grd['ny']
        xvect=concatenate([array(x0,ndmin=1),x0+cumsum(dx)],axis=0)
        yvect=concatenate([array(y0,ndmin=1),y0+cumsum(dy)],axis=0)
        # for each stress period
        # line 0 is text
        f1.write('#Text \n')
        # line 1 optional for parameters
        # line 2 mxact max numb of active cells (here simply ncol*nrow
        f1.write('%9i \n' %(nx*ny))
        # line 3 and 4 optional for parameters
        # line 5 itmp: nb fixed cells, NP: nb parameteres
        # line 6 layer row column Shead (start) Ehead (end)
        # first loop round iper
        # take care if ou put twice a cell in chd it adds values!!!
        nper=len(self.tlist)
        zlist=self.zoneTransient['Potentiel'];np,nz=shape(zlist)
        for ip in range(nper):
            buff='';npts=0
            # then loop round zones to get the index and write the head
            for iz in range(nz):
                zone=aqui.getZone('Potentiel',iz);
                xy=zone.getXy();x,y=zip(*xy);z=x*1
                icol,irow,ilay=zone2index(x,y,z,xvect,yvect,nx,ny)
                hd=zlist[ip,iz];npts+=len(irow)
                if aqui.getDim() in ['Xsection','Radial']:
                    ir2=[1]*len(irow);ilay=irow
                else : ir2=[ny-x for x in irow]
                if aqui.getDim()=='2D':
                    ilay=ilay.astype(int)*0
                for i in range(len(irow)):
                    buff+=str(ilay[i]+1).rjust(9)+' '+str(ir2[i]).rjust(9)+' '+\
                           str(icol[i]+1).rjust(9)+' %+9.2e %+9.2e'%(hd,hd)+'\n'
            f1.write(' %6i     0    \n' %npts)
            f1.write(buff)
        

    #*************************** fichier Solver ***********************
    def WriteSolveFile(self, ecoul):
        
        nom_solv = ecoul.getParm('SolvName')
        f1 = self.CreateFile('.'+nom_solv, 'w')
        s = ecoul.getParm('Solver')
        for i in range(len(s)): exec(s[i][0]+'=s['+str(i)+'][1]')
        if nom_solv == 'sip':
            f1.write('%9i %9i  \n' %(mxiter,nparm))
            f1.write('%9.3f %9.2e %9i %9.3f %9i \n' %(accel,hclose,ipcalc,seed,iprsip))
        elif nom_solv == 'sor':
            f1.write('%9i  \n' %mxiter)
            f1.write('%9.3f %9.2e %9i \n' %(accl,Hclose,iprsor))            
        elif nom_solv == 'pcg':           
            f1.write('%9i %9i %9i \n' %(mxiter,iter1,npcond))
            f1.write('%9.3e %9.2e %9.3f %9i %9i %9i %9i \n' %(hclose,rclose,relax,nbpol,iprpcg,mutpcg,damp))            
        elif nom_solv == 'de4':
            f1.write('%9i %9i %9i %9i \n' %(itmx,mxup,mxlow,mxbw))
            f1.write('%9i %9i %9.3f %9.3e %9i \n' %(ifreq,mutd4,accl,hclose,iprd4))
        f1.close()
        
    #*************************** fichier LMT ***********************
    def WriteLmtFile(self):
        
        f1 = self.CreateFile('.lmt', 'w')        
        f1.write('OUTPUT_FILE_NAME    '+self.pName+'.flo \n')
        f1.write('OUTPUT_FILE_UNIT    333 \n')
        f1.write('OUTPUT_FILE_HEADER  standard \n')
        f1.write('OUTPUT_FILE_FORMAT  unformatted \n')
        f1.close()
        
    #*************************** fichier OC ***********************
    def WriteOcFile(self, aqui, ecoul):

        grd = aqui.getFullGrid()
        ncol = int(grd['nx'])
        f1 = self.CreateFile('.oc', 'w')       
        #f1.write('HEAD SAVE FORMAT ('+str(ncol)+'F13.5) \n')
        f1.write('HEAD SAVE UNIT 30 \n')
        t0=ecoul.getParm('Temps');tf=t0[0][1];dur=t0[1][1]
        nstp = t0[2][1];tr='SS';#print nstp;
        if len(self.tlist)>1:
            for p in range(len(self.tlist)):
                #for step in range(nstp):
                f1.write('Period %5i Step %5i \n' %(p+1,nstp))
                f1.write('Save Head \n')
        else : f1.write('Period 1 Step 1 \nSave Head\nSave Budget \n')
        f1.close()
    #------------------------- fonction  writevect, writemat -------------------
    def writeVecModflow(self, v, f1):
        l=len(v);a=str(type(v[0]))
        if a[13:16]=='int': typ='I'
        else : typ='G'
        if amin(v)==amax(v):
            f1.write('CONSTANT     %9.5e \n' %amin(v))
            return
        if typ=='I': fmt='1    ('+str(l)+'I'+str(ln)
        else : fmt='0    ('+str(l)+'G12.4'           
        f1.write('INTERNAL     '+fmt+')     3' )
        
        if typ=='I': fmt='%'+str(ln)+'i'
        else : fmt='%+11.4e '            
        f1.write('\n')
        for i in range(l):
            f1.write(fmt %v[i])
        f1.write('\n')

    def writeMatModflow(self, m, f1):
        if len(shape(m))==1: return self.writeVecModflow(m,f1)
        [l,c] = shape(m);ln=3;a=str(type(m[0,0]))
        if a[13:16]=='int': typ='I'
        else : typ='G'
        if amin(amin(m))==amax(amax(m)):
            if typ=='I': f1.write('CONSTANT     %9i \n' %(amin(amin(m))))
            else : f1.write('CONSTANT     %9.5e \n' %(amin(amin(m))))
            return
        if typ=='I':
            fmt='1    ('+str(c)+'I'+str(ln)
        else :
            fmt='0    ('+str(c)+'G12.4' #+str(ln)            
        f1.write('INTERNAL     '+fmt+')     3' )      
        if typ=='I':
            fmt='%'+str(ln)+'i'
        else :
            fmt='%+11.4e ' #'+str(ln)+'e '            
        f1.write('\n')
        for i in range(l-1,-1,-1): # to write the rows from top to bottom
            for j in range(c):
                f1.write(fmt %m[i][j])
            f1.write('\n')

    def writeBlockModflow(self,m,f1):
        if len(shape(m))==3:
            nlay,a,b=shape(m);
            for l in range(nlay):
                self.writeMatModflow(m[l],f1)
        else : self.writeMatModflow(m,f1)

""" Classe de lecture des fichiers produits par Modflow """
class ModflowReader:
    
    def __init__(self, pPath, pName):
        """ on recupere le nom du projet pour effectuer l'ouverture du projet a partir de ce nom """
        self.pFullPath = pPath+os.sep+pName

    def ReadHeadFile(self, aqui,iper=0):
        """ lecture du fichier .head (fichier dwritevant la charge) """    
        grd = aqui.getFullGrid();ncol, nrow = grd['nx'], grd['ny']
        nlay=aqui.getNbCouches();#print iper, nlay,ncol,nrow
        if aqui.getDim() in ['Xsection','Radial']:
            nlay=nrow;nrow=1
        #print 'mfl readh',nlay,ncol,nrow
        try : f1 = open(self.pFullPath+'.head','rb')
        except IOError: return None
        hd=zeros((nlay,nrow,ncol))+0.;blok=44+nrow*ncol*4; # v210 60
        for il in range(nlay):
            #pos=iper*nlay*blok+blok*il+56;f1.seek(pos) v1_10
            pos=iper*nlay*blok+blok*il+44;f1.seek(pos) #vpmwin
            data = arr2('f');data.fromfile(f1,nrow*ncol);
            hd[il] = reshape(data,(nrow,ncol)) # 
        f1.close();
        if aqui.getDim() in ['Xsection','Radial']: hd = array(hd[::-1,:,:])
        else : hd = array(hd[:,::-1,:]);#print 'mflwri rdhed',shape(hd)            
        return hd
    
    def ReadFloFile(self, aqui,iper=0):
        """ read flo file and gives back Darcy velocities"""
        grd = aqui.getFullGrid();dx, dy = grd['dx'], grd['dy'];
        dxm,dym=meshgrid(dx,dy)
        ep = aqui.getEpais();
        if aqui.getDim() in ['Xsection','Radial']:
            dxm=array(dx);dym=1.;
        try : f1 = open(self.pFullPath+'.flo','rb')
        except IOError : return None
        # point de depart dans le fichier
        # variables Sat,Qx(ncol>1),Qy(nrow>1),Qz(nlay>1),Stor(trans),
        ncol,nrow,nlay,blok,part=self.getPart(f1);
        l0=11;pos = l0+36+iper*part+blok+5*4+16       
        f1.seek(pos);data = arr2('f');data.fromfile(f1,nlay*ncol*nrow)        
        vx = reshape(data,(nlay,nrow,ncol))
        # trouver position des vitesses y
        pos = l0+36+iper*part+blok*2+5*4+16
        f1.seek(pos);data = arr2('f');data.fromfile(f1,nlay*ncol*nrow)       
        vy = reshape(data,(nlay,nrow,ncol));bal=0.0
##        if nlay==1: # balance de flux
##            vx=vx[0][::-1,:];vy=-vy[0][::-1,:];vx[vx==0.]=1.;vy[vy==0.]=1.;
##            vm=abs(vx)+abs(vy);vmax=amax(amax(vm))
##            bal=abs(vx[2:-2,1:-2]-vx[2:-2,2:-1]+vy[2:-2,2:-1]-vy[3:-1,2:-1])# on prend pas les bords
##            bal[vm[2:-2,1:-2]<vmax*1e-3]=0.
##            #bal[pot[2:-2,1:-2]!=0.]=0.;
##            md=median(median(bal));b2=clip(bal,md*1e-3,md*1e3)
##            bal=sum(sum(b2/(abs(vx[2:-2,1:-2])+abs(vy[2:-2,2:-1]))))*100
        # trouver position des vitesses z (nexiste que si plus d'un layer)
        bal=0.
        if nlay>1: # rajouter vz
            nb=2 #number of blocks to read z velocities (absence of y velo)
            if nrow>1: nb=3 #presence of y velo
            pos = l0+36+iper*part+blok*nb+5*4+16
            f1.seek(pos);data = arr2('f');data.fromfile(f1,nlay*ncol*nrow)       
            m0 = reshape(data,(nlay,nrow,ncol));vz=m0*0.
            for l in range(nlay): vz[l] = m0[l]/dxm/dym
            vz=concatenate([vz[:1,:,:],vz],axis=0)
        # fermer le fichier
        f1.close();
        # rows are ordered from top to bottom in modflow so invert them here
        vx=vx[:,::-1,:]/dym/ep;vy=-vy[:,::-1,:]/dxm/ep; #retourner les vecteurs
        # as vx start from right of 1st cell we need to add one in the first col
        vx=concatenate([vx[:,:,:1],vx],axis=2);vx[:,:,-1]=vx[:,:,-2]
        # ssame for vy start at lower face, which is the last one now (inversion)
        vy=concatenate([vy,vy[:,-1:,:]],axis=1)
        # seems that vy is surrounded by 0
        vy[:,:,0]=vy[:,:,1];vy[:,:,-1]=vy[:,:,-2];vy[:,0,:]=vy[:,1,:]
        if aqui.getDim() in ['Xsection','Radial']:
            vx=vx[::-1,:,:]*1;vz=vz[::-1,:,:]*1
        if nlay>1 : return [vx,vy,-vz]#,bal -vz[:,::-1,:]
        else : return [vx,vy]

    def getPtObs(self,aqui,irow,icol,ilay,iper,typ):
        """for typ=flux return fluxes for a series of obs cell
        for typ=head return the heads
        iper is a list of periods indices"""
        nper=len(iper);
        if aqui.getDim() in ['Xsection','Radial']:
            ilay=irow*1;irow=[0]*len(ilay)
        if typ=='Charge': 
            return self.getHeadPtObs(aqui,irow,icol,ilay,iper)
        try : f1 = open(self.pFullPath+'.flo','rb')
        except IOError : return None
        ncol,nrow,nlay,blok,part=self.getPart(f1);blok2=ncol*nrow*4
        l0=11;qx= zeros((nper,len(irow)));qy=qx*0.
        for ip in range(nper):
            posx = l0+36+iper[ip]*part+blok+5*4+16;posy=posx+blok
            for i in range(len(irow)):
                pos2 = blok2*ilay[i]+irow[i]*ncol*4+icol[i]*4
                f1.seek(posx+pos2);data = arr2('f');data.fromfile(f1,1)
                qx[ip,i] = float(data[0])
                f1.seek(posy+pos2);data = arr2('f');data.fromfile(f1,1)        
                qy[ip,i] = float(data[0])
        return qx,qy

    def getHeadPtObs(self,aqui,irow,icol,ilay,iper):
        try : f1 = open(self.pFullPath+'.head','rb')
        except IOError: return None
        grd = aqui.getFullGrid();ncol, nrow = grd['nx'], grd['ny']
        nlay=aqui.getNbCouches();
        if aqui.getDim() in ['Xsection','Radial']:
            nlay=nrow*1;nrow=1;ilay=irow*1;irow=[0]*len(ilay)
        nper=len(iper);hd=zeros((nper,len(irow)))
        f1.seek(32);data=arr2('i');
        #data.fromfile(f1,3);ncol,nrow,nlay=data;print 'mfw gethedpt nc,nr,nl',ncol,nrow,nlay
        blok=44+nrow*ncol*4;#print 'mfw gethedpt ilay,icol,row',ilay,icol,irow
        for ip in range(nper):
            for i in range(len(irow)):
                pos=44+iper[ip]*nlay*blok+ilay[i]*blok+irow[i]*ncol*4+icol[i]*4;
                f1.seek(pos);data = arr2('f');data.fromfile(f1,1);#print iper[ip],irow[i],icol[i],data
                hd[ip,i]=float(data[0])
        return hd
        
    def getPart(self,f1):
    #if 3>2:
        l0=11;f1.seek(l0);data = arr2('i');data.fromfile(f1,14);
        mwel,mdrn,mrch,mevt,mriv,m,chd,mss,nper,kp,kst,ncol,nrow,nlay = data
        blok=5*4+16+ncol*nrow*nlay*4;l2=5*4+16+4
        nwel=0;mss=1; # even in SS it seems to have sto?
        ichd=sign(chd);iwel=sign(mwel);irch=sign(mrch)
        icol=sign(ncol-1);irow=sign(nrow-1);ilay=sign(nlay-1);
        part0=blok+icol*blok+irow*blok+ilay*blok+mss*blok+ichd*(l2+chd*16)
        if iwel>0:
            f1.seek(l0+36+part0+l2-4);data = arr2('i');data.fromfile(f1,1)
            nwel=data[0];
        part=part0+iwel*(l2+nwel*16)+irch*(l2-4+ncol*nrow*4*2);
        return ncol,nrow,nlay,blok,part
