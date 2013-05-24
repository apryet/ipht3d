#import iphtC1
from scipy import *

    # fonctions de calcul
def irreg2mat(aqui,XP,YP,Z):
    """ transfrome des donnees disposees une matrice irreguliere XP, YP,
    en des donnees sur la grille reguliere du modele
    """
    grd = aqui.getFullGrid()
    x0,dx,nx = grd['x0'],grd['dx'],grd['nx']
    y0,dy,ny = grd['y0'],grd['dy'],grd['ny']
    Z1 = zeros((ny,nx))+0.
    # etendre un peu la grille pour eviter les trous
    [l,c] = shape(XP)
    x1=XP[:,1:]/2+XP[:,:-1]/2;y1=YP[:,1:]/2+YP[:,:-1]/2;z1=Z[:,1:]/2+Z[:,:-1]/2
    x2=zeros((l,2*c-1))+0.;y2=x2*0.;z2=x2*0.
    x2[:,::2]=XP;x2[:,1::2]=x1;y2[:,::2]=YP;y2[:,1::2]=y1;z2[:,::2]=Z;z2[:,1::2]=z1
    x3=x2[:,1:]/2+x2[:,:-1]/2;y3=y2[:,1:]/2+y2[:,:-1]/2;z3=z2[:,1:]/2+z2[:,:-1]/2
    x4=zeros((l,4*c-3))+0.;y4=x4*0.;z4=x4*0.
    x4[:,::2]=x2;x4[:,1::2]=x3;y4[:,::2]=y2;y4[:,1::2]=y3;z4[:,::2]=z2;z4[:,1::2]=z3
    ix=round_(x4/dx);ix=clip(ix,0,nx-1);ix=ix.astype(int)
    iy=round_(y4/dy);iy=clip(iy,0,ny-1);iy=iy.astype(int)
    # mettre dans la matrice puis boucher les derniers trous
    put(Z1,iy*nx+ix,z4)
    Z1b=ravel(Z1)
    ind = compress(Z1b==0.,arange(nx*ny))
    iy0 = floor(ind/nx);iy0=iy0.astype(int)
    ix0 = mod(ind,nx);ix0=ix0.astype(int)
    ind1=(iy0-1)*nx+ix0;ind2=(iy0+1)*nx+ix0;ind3=iy0*nx+ix0-1;ind4=iy0*nx+ix0+1
    ind1=clip(ind1,0,nx*ny-1);ind2=clip(ind2,0,nx*ny-1)
    ind3=clip(ind3,0,nx*ny-1);ind4=clip(ind4,0,nx*ny-1)
    nb=sign(take(Z1b,ind1))+sign(take(Z1b,ind2))+sign(take(Z1b,ind3))+sign(take(Z1b,ind4))
    nb=clip(nb,1,4)
    put(Z1,ind,(take(Z1b,ind1)+take(Z1b,ind2)+take(Z1b,ind3)+take(Z1b,ind4))/nb)
    return Z1

# fonction de calcul a partir des zones
def obj2mat(aqui,var,lay,vbase=None,iper=0):
    if aqui.getInterpol(var):
        m=obj2mat2(aqui,var,lay,iper)
    else:
        m=obj2mat1(aqui,var,lay,iper)
    if var=='Recharge':m=m[-1]
    return m

def obj2matBlock(aqui,var,iper=0):
    grd = aqui.getFullGrid()
    ncol, nrow,dcol  = int(grd['nx']),int(grd['ny']), grd['dx']
    nlay = aqui.getNbCouches()
    radfact=1.
    if aqui.getDim()=='Radial' and var in['Permeabilite','Emmagasin.','Porosite']: #,'Porosite' later, for mt3d
        radfact=(cumsum(dcol)-array(dcol)/2)*6.28
    if aqui.getDim()in ['Xsection','Radial']:
        m=obj2mat(aqui,var,0,iper)*radfact;
        m=reshape(m,(nrow,1,ncol));
        return m[-1::-1,:,:]
    else:
        m=zeros((nlay,nrow,ncol))
        for l in range(nlay): m[l]=obj2mat(aqui,var,l,iper)
        return m

def obj2matBlockNb(aqui,var,opt):
    grd = aqui.getFullGrid()
    ncol, nrow = int(grd['nx']),int(grd['ny']);
    nlay = aqui.getNbCouches()
    if aqui.getDim()in ['Xsection','Radial']:
        m=obj2mat1(aqui,var,0,0,opt=opt);m=reshape(m,(nrow,1,ncol))
        m=m.astype('int')
        return m[-1::-1,:,:]
    else :
        m=zeros((nlay,nrow,ncol));m=m.astype(int)
        for l in range(nlay): 
            #mil=aqui.lay2mil(l)
            m[l]=obj2mat1(aqui,var,l,0,opt=opt)
        return m.astype('int')

def obj2mat1(aqui,var,lay,iper,opt=None):
    """ transforme une serie de zones en matrice de taille nx*ny avec la valeur
    de base partout sauf SUR LEs LIGNES des zones (pour potentiel)
    c est obj2mat1 sans remplissage des polygonss
    """
    grd = aqui.getFullGrid();mil=aqui.lay2mil(lay)
    x0,x1,dx,nx = grd['x0'],grd['x1'],grd['dx'],grd['nx']
    y0,y1,dy,ny = grd['y0'],grd['y1'],grd['dy'],grd['ny']
    xvect=concatenate([array(x0,ndmin=1),x0+cumsum(dx)],axis=0)
    yvect=concatenate([array(y0,ndmin=1),y0+cumsum(dy)],axis=0)
    vbase=aqui.getVbaseLay(var,lay);#print 'caclA',var,lay,vbase
    if var=='Tr_rech':
        vbase=aqui.model.getParm('Transport','Recharge')[0][1];
    if opt in['BC','zon']: vbase=0
    if type(vbase)not in [type(5.),type(5)]: return vbase # case with matrix loaded from outside
    m0 = zeros((ny,nx))+vbase
    zlist = aqui.getZoneList(var) #take all zones because zval has all zones
    zval = aqui.getZoneTransient()[var];#print 'zval',zval

    for i in range(len(zlist)):  # boucle sur les formes
        milz=zlist[i].getInfo()[2];#print 'calAq',var,mil,zlist[i],zval[iper,i]
        if mil not in milz: continue # the zone is not in the correct media
        xy = zlist[i].getXy();x,y = zip(*xy)
        zv0=zval[iper,i];
        typz='B.Condition';info=zlist[i].getInfo();#print 'zv0',zv0
        if len(info)>3: typz=info[3]
        if opt=='BC' and typz!='B.Condition': continue # initial not needed for BC
        if opt=='BC': zv0=1
        if opt=='zon': zv0=i+1  # zone number
        
        if zlist[i].getForme()== 0:  # cas point
            ix,iy = minDiff(x[0],xvect),minDiff(y[0],yvect)
            m0[iy,ix] = zv0
            
        elif zlist[i].getForme()>0: # autres formes
            lp = len(x);form=zlist[i].getForme()
            if (form==4) and (opt not in['BC','zon']): z = [float(a) for a in zlist[i].getVal()]
            else : z=[zv0]*lp
            nxp,nyp,nzp=zone2index(x,y,z,xvect,yvect,nx,ny);#print 'obj2m1',var,nxp,nyp
            #print nxp,nyp,nzp,shape(m0)
            put(m0,nyp*nx+nxp,nzp)
       
        if (zlist[i].getForme()==3) or (zlist[i].getForme()==2): # cas polygone
            # remplir la zone par des lignes verticales
            js = argsort(nxp);
            nxs, nys = take(nxp,js), take(nyp,js)            
            lls = len(nxs)
            ind1 = zeros((ny,nx))
            mn, mx = int(nys[0]),int(nys[0])
            for j in range(1,lls):
                if nxs[j]<>nxs[j-1]:
                    ind1[mn:mx+1,int(nxs[j-1])] = [1]*(mx-mn+1)
                    mn,mx = int(nys[j]),int(nys[j])                    
                mn,mx = int(min(mn,nys[j])),int(max(mx,nys[j]))
            ind1[mn:mx+1,int(nxs[lls-1])] = [1]*(mx-mn+1)
            # remplir la zone avec ligne horizontales 
            js = argsort(nyp)
            nxs, nys = take(nxp,js),take(nyp,js)
            ind2 = zeros((ny,nx))
            mn, mx = int(nxs[0]),int(nxs[0])
            for j in range(1,lls):
                if nys[j]<>nys[j-1]:
                    ind2[int(nys[j-1]),mn:mx+1] = [1]*(mx-mn+1)
                    mn,mx = int(nxs[j]),int(nxs[j])                    
                mn,mx = int(min(mn,nxs[j])),int(max(mx,nxs[j]))                
            ind2[int(nys[lls-1]),mn:mx+1] = [1]*(mx-mn+1)
            ind = ind1*ind2  ## il faut que les deux indices=1 pour dans zone
            putmask(m0, ind==1, [zv0])
    return array(m0)

def zone2index(x,y,z,xvect,yvect,nx,ny):
    nxp,nyp,nzp=array(minDiff(x[0],xvect)),array(minDiff(y[0],yvect)),array(z)
    if len(x)==1:
        return nxp,nyp,nzp
    nxp=array([],dtype='int');nyp=nxp*1;nzp=array([],dtype='float')
    for j in range(1,len(x)):
        ix1=minDiff(x[j-1],xvect);ix2=minDiff(x[j],xvect);
        iy1=minDiff(y[j-1],yvect);iy2=minDiff(y[j],yvect);#print y[0],yvect
        if ix1==ix2 and iy1==iy2: continue
        sensx=sign(ix2-ix1);sensy=sign(iy2-iy1);
        lx=abs(ix2-ix1);ly=abs(iy2-iy1);ll=max(lx,ly)
        dz=z[j]-z[j-1];#print ix1,ix2,iy1,iy2,sensx,xvect
        if lx>=ly:
            ixp=arange(ix1,ix2+sensx,sensx);
            iyp=ixp*0;xv2=xvect[ixp]
            yv2=y[j-1]+(xv2-xv2[0])*(y[j]-y[j-1])/(x[j]-x[j-1]);
            for k in range(ll+1): iyp[k]=minDiff(yv2[k],yvect)
            zp=z[j-1]+dz*(xv2-x[j-1])/(x[j]-x[j-1]);#print ixp,xv2,iyp,yv2,zp
        else:
            iyp=arange(iy1,iy2+sensy,sensy);
            ixp=iyp*0;yv2=yvect[iyp];
            xv2=x[j-1]+(yv2-yv2[0])*(x[j]-x[j-1])/(y[j]-y[j-1]);
            for k in range(ll+1): ixp[k]=minDiff(xv2[k],xvect)
            zp=z[j-1]+dz*(yv2-y[j-1])/(y[j]-y[j-1]);
        nzp=concatenate([nzp,zp],axis=0)           
        nxp=concatenate([nxp,clip(ixp,0,nx-1)],axis=0)           
        nyp=concatenate([nyp,clip(iyp,0,ny-1)],axis=0)
    #nyp=ny-nyp-1
    if len(nxp)<1:nxp,nyp,nzp=array(minDiff(x[0],xvect)),array(minDiff(y[0],yvect)),array(z)
    mix=nxp*1000+nyp;a,ind=unique(mix,return_index=True)
    return nxp[ind].astype(int),nyp[ind].astype(int),nzp[ind]

def minDiff(x,xvect):
    d=x-xvect; d1=d[d>0.];
    if len(d1)==0: return 0
    else :
        a=where(d==amin(d1));return a[0]
    #a=nonzero(equal(d, amin(d[d>0.])))
    
from scipy.interpolate import splrep,splev,bisplrep,bisplev,Rbf
from scipy.interpolate import CloughTocher2DInterpolator as CTI

def obj2mat2(aqui,var,lay,iper):
    """ interpolation case from points or zones to matrix"""
    grd = aqui.getFullGrid()
    x0,dx,nx = grd['x0'],grd['dx'],grd['nx']
    y0,dy,ny = grd['y0'],grd['dy'],grd['ny']
    zlist = aqui.getZoneList(var,lay)
    xpt,ypt,zpt=[],[],[];mil=aqui.lay2mil(lay)
    vbase=aqui.getVbaseLay(var,lay)
    m = zeros((ny,nx)) + float(vbase)
    if len(zlist)==0: return m
    
    for i in range(len(zlist)):  # boucle sur les formes pour coordonnees
        xy = zlist[i].getXy()
        x,y = zip(*xy)
        z = float(zlist[i].getVal())
        l0 = len(xpt); l1 = len(x);#print i,x,y,l1
        if (zlist[i].getForme()!=4)and(zlist[i].getForme()!=0):
            z=[z]*l1
        if l1==1:
            xpt[l0:l0+l1]=[x[0]];ypt[l0:l0+l1]=[y[0]];zpt[l0:l0+l1]=[z]
        else:
            xpt[l0:l0+l1]=x;ypt[l0:l0+l1]=y;zpt[l0:l0+l1]=z
    xpt,ypt,zpt = array(xpt),array(ypt),array(zpt);#print xpt,ypt,zpt
    xg=x0-dx[0]/2.+cumsum(grd['dx']);yg=y0-dx[0]/2.+cumsum(grd['dy']);
    xm,ym=meshgrid(xg,yg)
    # interpolate
##    pol=polyfit2d(xpt,ypt,zpt,order=1)
##    z0=polyval2d(xpt,ypt,pol);dz=zpt-z0
##    m0=polyval2d(xm,ym,pol)
##    z0=mean(zpt);dz=zpt-z0;dx=min(xpt-mean(xpt));dy=min(ypt-mean(ypt))
##    rbfi=Rbf(xpt,ypt,zpt) #,function='thin_plate') #,epsilon=min(dx,dy)*2
##    m=rbfi(xm,ym)#+z0
##    c=CTI(zip(xpt,ypt),zpt,fill_value=mean(zpt))
##    m=c.__call__(xm,ym);
##    bs = bisplrep(xpt,ypt,dz,kx=3,ky=3)
##    m1=transpose(bisplev(xg,yg,bs));
##    m=m0+m1
    #distx = 2.*(max(xpt)-min(xpt))/sqrt(len(xpt))
    #disty = 2.*(max(ypt)-min(ypt))/sqrt(len(xpt))
    #grd1=(float(x0),float(y0),distx,disty);
    #m = iphtC1.interp2d(grd1,dx,dy,xpt,ypt,zpt)
    #clip(m,min(zpt)*.9,max(zpt)*1.1);m=m[-1::-1,:]
    xv,yv,m=invDistance(xpt,ypt,zpt,xm,ym,power=1.)
    return m #[-1::-1,:]

def invDistance(x,y,z,xm,ym,power=1.):
    ny,nx=shape(xm);m0=xm*0.;l=len(x)
    xv=xm[0,:];yv=ym[:,0]
    for ix in range(nx):
        for iy in range(ny):
            d=sqrt((xv[ix]-x)**2.+(yv[iy]-y)**2.)
            lb=1./(d**power)
            lb=lb/sum(lb)
            m0[iy,ix]=sum(z*lb)
    return xv,yv,m0

import itertools
from numpy.linalg import lstsq
def polyfit2d(x, y, z, order=3):
    ncols = (order + 1)**2
    G = zeros((x.size, ncols))
    ij = itertools.product(range(order+1), range(order+1))
    for k, (i,j) in enumerate(ij):
        G[:,k] = x**i * y**j
    m, _, _, _ = lstsq(G, z)
    return m

def polyval2d(x, y, m):
    order = int(sqrt(len(m))) - 1
    ij = itertools.product(range(order+1), range(order+1))
    z = zeros_like(x)
    for a, (i,j) in zip(m, ij):
        z += a * x**i * y**j
    return z

def vario(xpt,ypt,zpt):
#if 3>2:
    xm,ym=meshgrid(xpt,ypt)
    d=sqrt((xm-transpose(xm))**2+(ym-transpose(ym))**2)
    xm,zm=meshgrid(xpt,zp);g=1/2.*(zm-transpose(zm))**2
    dmax=amax(amax(d))/2.;lag=dmax/30.;
    grp=d/lag;grp=grp.astype(int);d1=zeros(15);vario=d1*0.
    for i in range(15):
        d1[i]=mean(d[grp==i]);vario[i]=mean(g[grp==i])
    # fit simple pente depart (sans le cube)
    r=mean(vario[1:8]/d1[1:8]);po=1.5/r #3/2/po = pente droite
    #mod=g0*(3/2.*d/po-1/2.*(d/po)**3) #spherical
    return po

from numpy.linalg import solve
def krige(xpt,ypt,zpt,po,xv,yv):
    """ krige function to interpolate over matrix made by xv, yv
    using the base points xpt ypt and the vario distance po"""
    z0=zeros((len(yv),len(xv)))
    for i in range(len(xv)-1):
        for j in range(len(yv)-1):
            x0=xv[i];y0=yv[j];
            d=sqrt((x0-xpt)**2+(y0-ypt)**2);ind=argsort(d)
            x1=xpt[ind<12];y1=ypt[ind<12];z1=zpt[ind<12];d1=d[ind<12];
            xm1,ym1=meshgrid(x1,y1)
            d1=sqrt((xm1-transpose(xm1))**2+(ym1-transpose(ym1))**2)
            g1=3/2.*d1/po-1/2.*(d1/po)**3 # vario model
            l1=len(x1)+1;A=ones((l1,l1));
            A[:-1,:-1]=g1;A[-1,-1]=0.
            d2=sqrt((x0-x1)**2+(y0-y1)**2)
            g2=3/2.*d2/po-1/2.*(d2/po)**3
            B=ones((len(x1)+1,1));B[:-1,0]=g2;#print i,j,len(A),len(B)
            lb=solve(A,B);z0[j,i]=sum(z1*transpose(lb[:-1]))
    return z0
