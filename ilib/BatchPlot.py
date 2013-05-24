#import os;os.chdir('d:/ipht3d/lib1_j/ilib')
from iPht3dModel import *;import os
import matplotlib.pylab as pl
from matplotlib import rcParams;rcParams['interactive']=True

#########################################################
def op(model):
    filename = model.project[0] + os.sep + model.project[1] + '.ipht'
    f1 = file(filename, 'r');doc = f1.read();f1.close()
    dom=xdom.parseString(doc)        
    dicts=dom.getElementsByTagName("dict")
    for d in dicts:
        dname = d.getElementsByTagName("name")[0].childNodes[0].data
        keys = d.getElementsByTagName("key");dict1 = {}
        for k in keys:
            kname = k.getElementsByTagName("name")[0].childNodes[0].data
            kdata = k.getElementsByTagName("content")[0].childNodes[0].data
            exec('dict1[kname] ='+kdata)
        model.setBase(dname,dict1)
    model.Aquifere.createZoneTransient();
    model.Aquifere.makeGrid();model.Aquifere.makeZblock();
    model.Ecoulement.setReader();model.Transport.setReader()
    model.PHT3D.setReader()

model = iPht3dModel(None,'d://ipht3d//lib1_k');
model.setProject(['d://ipht3d//exemples//beenyup','BeenyupR3'])
op(model);

# linking wells names and mdoflow numbers
wnum={'BY11':11,'BY16':19,'BY04':4,'BY10':12,'BY15':20,'BY03':5,\
'BY22':8,'BY19':16,'BY07':2,'BY13':21,'BY02':6,'BY21':9,'BY18':17,\
'BY08':13,'BY14':22,'BY06':3,'BY12':23,'BY01':7,'BY20':10,'BY17':18}
wells=['BY11','BY16','BY04','BY00','BY00',\
       'BY10','BY15','BY03','BY22','BY19',\
       'BY07','BY13','BY02','BY21','BY18',\
       'BY08','BY14','BY00','BY00','BY00',\
       'BY06','BY12','BY01','BY20','BY17']

elemts=['Date(num)','Cl','FieldpH','Ca','HCO3','SO4']; #names that are in elemts
mmass=[1,35.5,1,40.,62.,96.]
fdir='d://ipht3d//ex//henning//beenyupdata'
def impCsv(fdir,wells,elemts):
    meas={}
    fname=fdir+os.sep+'elmts.txt'
    f1=open(fname);ti=f1.readline();ti2=ti.split(',');f1.close()
    cols=[];
    for e in elemts: cols.append(ti2.index(e))
    for w in wells:
        if w=='BY00': continue
        fname=fdir+os.sep+w+'.txt'
        f1=open(fname);arr=zeros((100,len(elemts)));il=0
        for ll in f1:
            a=ll.split();
            for ic in range(len(cols)): 
                if '#' in a[cols[ic]]: arr[il,ic]='NaN'
                else : arr[il,ic]=float(a[cols[ic]])
            il+=1
        meas[w]=arr[:il,:]
    return meas
    
#meas=impCsv(fdir,wells,elemts)

# import Simone 3D data (start stop copied from startstop.txt)
def ImpVmNodes():
    stime={};ls=0 # a dictionnary
    for k in start.keys(): # put start and stop time in the same stime dict
        stime[k]=zip(start[k],stop[k]);ls+=len(start[k])
        
    data=loadtxt('d://ipht3d//ex//henning//beenyupData//Var16a.dat')

    #colonnes: 3:time, 4: well nr, 8 : conc, 9 : num species
    nspec=52;arr=zeros((ls,nspec+1));l=0
    lwells=['q']*ls;l=0
    for k in stime.keys():
        if k in ['BY05','BY09']:continue
        wn=wnum[k];print k
        for ti in stime[k]:
            indx=where((data[:,3]>=ti[0])&(data[:,3]<=ti[1])&(data[:,4]==wn))
            if len(indx[0])<2: continue
            data2=data[indx[0],:];n,b=shape(data2);n=n/nspec/2
            arr[l,0]=(ti[1]+ti[0])/2.;
            for ie in range(1,nspec):
                arr[l,ie+1]=data2[data2[:,9]==ie,8][n]
            lwells[l]=k;l+=1
    # if only one species no species column
    data=loadtxt('d://ipht3d//ex//henning//beenyupData//Run14a.dat')
    vm3d=zeros((ls,2));lwells=ones((ls));l=0
    for k in stime.keys():
        if k in ['BY05','BY09']:continue
        wn=wnum[k];print k
        for ti in stime[k]:
            indx=where((data[:,3]>=ti[0])&(data[:,3]<=ti[1])&(data[:,4]==wn))
            if len(indx[0])<2: continue
            data2=data[indx[0],:];n,b=shape(data2);n=n/2
            vm3d[l,0]=(ti[1]+ti[0])/2.;vm3d[l,1]=data2[:,8][n]
            lwells[l]=wn;l+=1
    vm3d[:,1]=vm3d[:,1]/1000.

# get data from ipht3d model
def getIphData(model,opt,wells,esp=''):
    """ opt is Transport or PHT3D, esp is the name of species
    just for PHT3D"""
    ipht={};print esp
    lper=range(445)
    for w in wells:
        if w=='BY00':continue
        ipht[w]=model.onPtObs('B',lper,opt,w,esp)
    return ipht
#ipht=getIphData(model,'PHT3D',wells,esp='Ca')

#plot the data for transport
def plotCompar(wnum,wells,elemts,mmass,meas,ipht,esp):
    """ipht result sin moles, measured in ug/l"""
    iesp=elemts.index(esp);mx=0;mass=mmass[iesp]
    # find maximum
    for w in wells:
        if w=='BY00':continue
        mx2=amax(ipht[w][1][:,1])
        if mx2>mx: mx=mx2
    mx=mx*1000*1.05
    for iw in range(len(wells)):
        w=wells[iw];print w
        if w=='BY00':continue
        wn=wnum[w];
        pl.subplot(5,5,iw+1)
        t,p=ipht[w];
        pl.plot(t,p[:,1]*1000,'r');pl.axis([-50,600,0,mx]) # ipht radial model
        #pl.plot(vm3d[lwells==wn,0],vm3d[lwells==wn,1])
        #pl.plot(meas[w][:,0]-40492,meas[w][:,iesp]/mass,'o') # measured data
        pl.text(450,mx*.85,w)
#plotCompar(wnum,wells,elemts,mmass,meas,ipht,'SO4')

