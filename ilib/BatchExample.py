#model.Aquifere.setVbase('Permeabilite',500)

# changing a zone value and running modflow and mt3d
iper=1;
typ='B1' # B for breakthrough 1 is for weighted average
group='Transport'
zname='w1'
esp=['']
z=model.Aquifere.getZoneByName('Forages','pomp')
data=None
val= [-400.,-800.,-1600.,-3200.]
for v in val:
    z.setVal(v)
    model.doAction('Ecoulement','Write',info=False) # info false not to have the dialog
    model.doAction('Ecoulement','Run',info=False)
    model.doAction('Transport','Write',info=False)
    model.doAction('Transport','Run',info=False)
    t,d0,labels=model.onPtObs(typ,iper,group,zname,esp)
    if data==None: data=d0
    else : data=concatenate([data,d0],axis=1)

savetxt('d://ipht3d//exemples//LepoutF2b.txt',data)

# printing all zones in one file
iper=1;
typ='P0' # B for profile
group='Transport'
esp=[''];data=None;zname='o1'
for iper in arange(9)*10:
    t,d0,labels=model.onPtObs(typ,iper,group,zname,esp)
    if data==None: data=d0
    else : data=concatenate([data,d0],axis=1)

savetxt('f://ipht3d//ex//output.txt',data)

# Pht3D printing all species in one file for each obs zone
iper=1; # dummy val for breakthrough
typ='B1' # B for breakthrough 1 is for weighted average
group='PHT3D'
desp=model.PHT3D.getListEsp();lesp=[]
for k in ['k','i','kim','p','e','s','kp']: lesp.extend(desp[k])
data=None;print lesp
zlist=model.Aquifere.getZoneList('Observation')
for z in zlist:
    zname=z.getNom();print zname
    t,data,labels=model.onPtObs(typ,iper,group,zname,lesp)
    savetxt('f://ipht3d//ex//'+zname+'.txt',data)

#--------------------- optimization -----------------------
# modifying perm of one zone and dispersivity to get values at three obs points
from scipy.optimize import leastsq,fmin,fmin_l_bfgs_b
z1=model.Aquifere.getZoneByName('Permeabilite','z')
def residuals(p,args):
    k1,aT=p;self,z1=args
    iper=5;group='Transport';typ='B0'
    z1.setVal(k1);
    model.setParm('Transport','Transp',[('aL',1.),('aT',aT),('aZ',0.),('Rf',1.)])
    model.doAction('Ecoulement','Write',info=False)
    model.doAction('Ecoulement','Run',info=False)
    model.doAction('Transport','Write',info=False)
    model.doAction('Transport','Run',info=False)
    t,data,labels=model.onPtObs(typ,iper,group,'o1',['']);vo1=data[:,0][-1]
    t,data,labels=model.onPtObs(typ,iper,group,'o2',['']);vo2=data[:,0][-1]
    err=sum(array([(4.-vo1)**2.,(.5-vo2)**2.]))
    print k1,aT,vo1,vo2
    return err
p0=array([1500.,1.]);
a=fmin(residuals,p0,args=[(self,z1)],maxfun=50)

#a=fmin_l_bfgs_b(residuals,p0,args=[(self,z1)],maxfun=20,bounds=bounds)
#plsq = leastsq(residuals, p0, args=(y_meas,x,self,z1),maxfev=200,ftol=1e-12)  
