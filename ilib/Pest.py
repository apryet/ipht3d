"""PEST utility for iPht3D :
steps :
1. ipht3d seek for the main input file for pest (same name as iphtfile +.pst)
This file contains the parameters starting values and the boundaries
the parameters have to start with MF, MT or PH for modflow, mt3d or pht3d
This file must be in the same folder than the ipht3d file
for permeability : use MFKz1 where z1 is the name of the zone of interest
for dispersivity : MTPaL or MTPaT MTPaZ
observation model input are not read from this file
they will be produced

2. from this file ipht3d produces the template files (.tpl) for pest
and a batch file (runmod.bat)

3. ipht3d reads files starting as pest_obs that contain the observed values
one file per observation zone (for zone o1 file pest_obs_o1.txt)
start with line headers that are the observed variables names
first column is the observation time

4. ipht3d writes in the same folder a script to read data and write them in a correct
format in a txt file (out_..)

5. then pest is run by the user in a cmd window (using runmod.bat)
for each pest run, the python script is run"""

# all imports
import os,sys
from scipy import *
from pylab import loadtxt,savetxt

class Pest:
    def __init__(self,model):
    # get all important parameters from the current model (names and timelist)
        self.mod=model
        self.tlist=self.mod.Ecoulement.getListTemps()
        self.fdir,self.fname=self.mod.getProject()
        self.mdir=self.mod.mainDir
        sys.path.append(self.mdir)
        
    def readPst(self):
    # reads the pest_parms.txt file
        f1=open(self.fdir+os.sep+'pest_parms.txt','r');
        ind=0;self.parm=[];self.pstring=''
        for l in f1:
            if len(l)>3: self.pstring+=l;self.parm.append(l.split())
        f1.close()

    def writeTpl(self):
        # change the values in the model to initial ones and writes the files
        dicMF={'K':'Permeabilite'}
        self.prtMF,self.prtMT,self.prtPH=False,False,False
        kparm=[];s='ptf @ \n'
        print 'reading parameters'
        for pl in self.parm:
            name=pl[0];v0=pl[3];grp=name[:2];catg=name[2];print name
            s+=name+' @'+name+'@ \n'
            if grp=='MF': self.prtMF=True
            elif grp=='MT': self.prtMT=True
            elif grp=='PH': self.prtPH=True
        f1=open(self.fdir+os.sep+'pest_tpl.txt','w')
        f1.write(s);f1.close()
        self.ntfiles=1
        
    def writeBat(self):
    # produce the runmod.bat file
        s='python scriptPest1.py \n'
        if self.prtMF: s+=self.mdir+'\\bin\\mf2k_Pmwin.exe '+self.fname+'\n'
        if self.prtMT: s+=self.mdir+'\\bin\\mt3dms5b.exe Mt3d \n'
        if self.prtPH: s+=self.mdir+'\\bin\\pht3dv217.exe Pht3d \n'
        s+='python scriptPest2.py'
        f1=open(self.fdir+os.sep+'runmod.bat','w')
        f1.write(s);f1.close()
        print 'runmod.bat written'
        
    def getObsPt(self):
    # get the observation files and gathers data in one dict
        os.chdir(self.fdir)
        ldir=os.listdir(self.fdir);
        self.onames=[]; # list of observation points or zones
        self.ospec=[]; # list of observed species
        self.obs=[] #dict that will contain the observed data
        self.nbobs=0 #number of observation
        self.nifiles=0
        print 'reading observation'
        for f in ldir:
            if f[:9]=='pest_obs_':
                oname=f[9:].split('.')[0]
                self.onames.append(oname);self.nifiles+=1
                f1=open(f,'r')
                el0=f1.readline().split();self.ospec=el0[1:]
                f1.close()
                a=loadtxt(f,skiprows=1);self.obs.append(a)
                l,c=shape(a);self.nbobs+=l
                print f,self.nbobs
        # calc multipl factors
        mn=mean(self.obs[0],axis=0)
        self.fact=around(1/mn[1:])
                    
    def writeInst(self):
    # write the instruction files
        os.chdir(self.fdir)
        n=1
        for i in range(len(self.onames)):
            name=self.onames[i];nline,ncol=shape(self.obs[i])
            f1=open(name+'.ins','w')
            s='pif @ \n'
            for j in range(nline):
                s+='l1  '
                for k in range(ncol-1):
                    s+='['+self.ospec[k]+str(n)+']'+str((k+1)*10+1)+':'+str((k+2)*10)+' '
                s+=' \n';n+=1
            f1.write(s);f1.close()
        print 'instruction file written'
            
    def writePyscript(self):
    # writes the pyton script to retrieve data after model run
        os.chdir(self.mdir+os.sep+'ilib')
        f1=open('tplPestScript1.txt','r')
        s=f1.read();f1.close()
        os.chdir(self.fdir)
        s=s.replace('ppmdir',self.mdir)
        s=s.replace('ppfdir',self.fdir)
        s=s.replace('ppfname',self.fname)
        f1=open(self.fdir+os.sep+'scriptPest1.py','w')
        f1.write(s);f1.close()
        
        os.chdir(self.mdir+os.sep+'ilib')
        f1=open('tplPestScript2.txt','r')
        s=f1.read();f1.close()
        os.chdir(self.fdir)
        s=s.replace('ppmdir',self.mdir)
        s=s.replace('ppfdir',self.fdir)
        s=s.replace('ppfname',self.fname)
        tlist=[]
        for i in range(len(self.obs)):tlist.append(list(self.obs[i][:,0]))
        print tlist
        s=s.replace('pptime',str(tlist))
        s=s.replace('pponames',str([str(a) for a in self.onames]))
        s=s.replace('ppospec',str(self.ospec))
        f1=open(self.fdir+os.sep+'scriptPest2.py','w')
        f1.write(s);f1.close()
        print 'pyscripts written'
        
    def writePst(self):
    # rewrites the pst file
        nbgroup=1
        s='pcf \n* control data \n restart estimation\n'
        s+=str(len(self.parm))+' '+str(self.nbobs)+' 1 0 1 \n'
        s+=str(self.ntfiles)+' '+str(self.nifiles)+' single point 1 0 0 \n'
        s+='5.0 2.0 0.3 0.01 10\n'
        s+='5.0 5.0 0.001 \n.1 \n30 .005 3 3 .005 3 \n 1 1 1 \n'
        s+='* group definitions and derivative data \n'
        s+='G1 relative  .01  0 always_2  1 parabolic \n'
        s+='* parameter data \n'
        s+=self.pstring+'\n'
        s+='* observation groups \n  Gro1  \n'
        s+='* observation data \n'
        n=0;
        for i in range(len(self.onames)):
            print self.onames[i]
            nlines,c=shape(self.obs[i])
            for il in range(nlines):
                n+=1
                for isp in range(len(self.ospec)):
                    sp=self.ospec[isp]
                    s+=sp+str(n)+' '+str(self.obs[i][il,isp+1])+' '
                    s+=str(self.fact[isp])+' Gro1 \n'
        s+='* model command line \n runmod.bat \n'
        s+='* model input/output \n'
        s+='pest_tpl.txt  pest_run.txt \n'
##        if self.prtMF: s+=self.fname+'lpf.tpl '+self.fname+'.lpf  \n'
##        if self.prtMT: s+='MT3Ddsp.tpl MT3Ddsp.dat \n'
##        if self.prtPH: s+='Pht3d_ph.tpl Pht3d_ph.dat \n'
        for n in self.onames:
            s+=n+'.ins out'+n+'.txt \n'
        s+='* prior information'
        f1=open(self.fdir+os.sep+self.fname+'.pst','w')
        f1.write(s);f1.close()
        print 'Pst file modified \n Pest ready to run'
