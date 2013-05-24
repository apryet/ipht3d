# -*- coding: cp1252 -*-
from scipy import *
from calcAquifere import *
from array import array as arr2
import os,time
from phtDbase import *
import MtPhtKeywords as Mkey
from MtInterpreter import *

class MP3dWriter:

    def __init__(self, model, path, name):
        self.model,self.gui = model, model.gui
        self.pPath,self.pName = path,name;
        self.fullPath = path + os.sep + name
        self.ncomp, self.mcomp= 1,1

    def CreateFile(self, extension, mode):
        filename = self.pPath + os.sep+extension
        file_descriptor = open(filename, mode)
        return file_descriptor

    def WriteMP3dFile(self, aqui,listEsp,Tbase,Etemps,opt,parmk=None):
        self.interpreter=MtInterpreter(self.model,opt)
        aqui.createZoneTransient();
        self.zoneTransient = aqui.getZoneTransient()
        self.tlist=self.zoneTransient['tlist']
        [aL,aT,aZ,rf] = zip(*Tbase['Transp'])[1]
        self.WriteNamFile(opt,rf)
        if opt in ['MT3D','SEAWAT']:self.mcomp=self.ncomp=1
        else :
            self.mcomp,self.ncomp,self.anySol=listEsp['mcomp'],listEsp['ncomp'],listEsp['anySol']
        if opt in ['MT3D','SEAWAT']:
            l='T' # transport que traceur
            trans=self.model.Aquifere.getZoneTransient()['Transport']
        if opt=='SEAWAT':
            self.WriteVdfFile()
        if opt=='PHT3D':
            self.WritePht3dFile(aqui,Tbase,listEsp,parmk)
            self.WritePhreeqc(aqui,Tbase,listEsp);
            trans=self.model.Aquifere.getZoneTransient()['PHT3D']
        for n in ['btn','adv','dsp']: self.writeFile(n,opt)
        if len(trans)>0: self.writeFile('ssm',opt)
##        self.WriteBtnFile(aqui,Tbase,listEsp,Etemps,opt);
##        self.WriteAdvFile(Tbase,opt);
##        self.WriteDspFile(aqui,Tbase,opt);
##        self.WriteSsmFile(aqui,Tbase,listEsp,Etemps,opt);
        self.WriteGcgFile(Tbase,opt);
        if rf>1: self.WriteRctFile(aqui,Tbase,listEsp,opt) # case with retardation
        if self.model.getDualPoro() and opt=='PHT3D':
            self.WriteRct1File(aqui,Tbase,listEsp,opt)  # dual porosity exists
        return 
        
    def WriteNamFile(self,opt,rf):
        f1 = self.CreateFile(opt+'.nam','w');
        f1.write('List  7  '+opt+'.out\n')
        if opt=='SEAWAT':
            f2=open(self.fullPath+'.nam','r');f2.readline()
            for ll in f2: f1.write(ll)
            f2.close()
        else : f1.write('FTL  66 '+self.pName+'.flo\n')
        f1.write('BTN  31 '+opt+'btn.dat\n ADV  32    '+opt+'adv.dat\n')
        f1.write('DSP  33 '+opt+'dsp.dat\n SSM  34    '+opt+'ssm.dat\n')
        f1.write('GCG  35 '+opt+'gcg.dat\n')
        if opt=='PHT3D':
            f1.write('PHC  64    '+opt+'_ph.dat\n')
        if rf>1 or self.model.getDualPoro():
            f1.write('RCT  36 '+opt+'rct.dat\n')
        f1.close()

    #*********************** generic file writer ****************
    def writeFile(self,name,opt):
        """to write any modflow file.
        reads the keyword file and prints all keywords by types : param (0D)
        vector (1D) array (2D). types are found by (dim1,dim2).."""
        f1=open(self.pPath +os.sep+opt+ name+'.dat','w');
        ptslist,arrlist=[],[]
        n1=Mkey.groups.keys();#print n1,name
        for n in n1:
            if n.split('.')[1]==name: llist=Mkey.groups[n]
        for ll in llist:
            cond=Mkey.lines[ll]['cond'];#print 'mflw 1',cond,self.testCondition(cond)
            if self.testCondition(cond)==False :continue
            kwlist=Mkey.lines[ll]['kw'];kw0=kwlist[0].split('(')[0]
            ktyp=Mkey.lines[ll]['type'];#print 'mtw',kw0,ktyp
            if ktyp in ['arr','vec','xarr']: arr,aname=self.interpreter.getArray(kw0)
            
            if ktyp=='vec': # a vector
                self.writeVecMT3D(arr,f1)
                exec('self.'+kw0+'='+str(arr[0]))
                
            elif ktyp=='string': # a string to print 
                s=self.interpreter.getParm(kw0);f1.write(s)
                #exec('self.'+kw0+'='+s[:2])
                
            elif ktyp=='arr': # one array
                self.writeBlockMT3D(arr,f1,aname)
            elif ktyp=='xarr': # several arrays
                for i in range(len(arr)): self.writeBlockMT3D(arr[i],f1,aname[i])
                
            elif ktyp=='parr': # one variable, p arrays: one for each period
                nper=self.interpreter.getNper()
                for ip in range(nper):
                    arr=self.interpreter.getArrayPeriod(kw0,ip)
                    arrlist.append(arr)
        
            elif ktyp=='nvec2': # list of periods or others
                vlist=[]
                for k in kwlist:
                    a=k.split('(')
                    b,c=self.interpreter.getArray(a[0]);vlist.append(b)
                nlines=len(vlist[0]);s=''
                for j in range(nlines):
                    for ik in range(3):
                        val=vlist[ik][j];s+=str(val)[:9].ljust(9)+' ' #' %9.3e'%val# 
                    s+='\n'
                    for ik in range(3,7):
                        val=vlist[ik][j];s+=str(val)[:9].ljust(9)+' ' #' %9.3e'%val #
                    s+='\n'
                f1.write(s)
                
            elif ktyp=='npoints': # points on the grid stored in alist (for ssm)
                nper=self.interpreter.getNper();print 'opt',opt
                for ip in range(nper):
                    plist=self.interpreter.getPointsPer(opt,ip)
                    il,ir,ic,typ,v=plist;s=str(len(il))+'\n'
                    #print len(il),len(ir),len(ic),len(typ),len(v)
                    for i in range(len(il)):
                        s+=str(il[i]+1).ljust(10)+str(ir[i]+1).ljust(10)+str(ic[i]+1).ljust(10)
                        if opt=='MT3D': s+='%9.3e '%float(v[i])+str(typ[i]).rjust(9)+'\n'
                        elif opt=='PHT3D': s+='       0.'+str(typ[i]).ljust(10)+v[i]+'\n'
                    ptslist.append(s)
                    
            else : # classical parameters
                for k in kwlist:
                    val=str(self.interpreter.getParm(k));
                    try : int(val); exec('self.'+k+'='+val) #
                    except ValueError:
                        if val[0]!='#' : exec('self.'+k+'=\''+val+'\'') 
                    if val!=' ': f1.write(val[:9].ljust(9)+' ')
                if val!=' ': f1.write('\n')
                
        if len(arrlist)+len(ptslist)>0: # write the variables by period saved in a list previously
            nper=self.interpreter.getNper()
            for ip in range(nper):
                if len(arrlist)>ip:
                    if type(arrlist[ip])==type([5,6]): # case of recharge with several species
                        f1.write('1         \n');
                        for j in range(len(arrlist[ip])): self.writeMatMT3D(arrlist[ip][j],f1)
                    else: f1.write('1         \n');self.writeMatMT3D(arrlist[ip],f1)
                if len(ptslist)>ip: f1.write(ptslist[ip])
        print 'print '+name+' done'
        f1.close()

    #**************** test condition **********************
    def testCondition(self,cond):
        """ test if the condition is satisfied"""
        a=True
        if cond!='':
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

    #************************ writeture du fichier GCG ***********************************
    def WriteGcgFile(self, Tbase,opt):
        f1 = self.CreateFile(opt+'gcg.dat','w')
        
        it, mxiter, isolve, ncrs, accl, cclose, iprgcg = zip(*Tbase['Solver'])[1]
        f1.write('%9i %9i %9i %9i\n' %(int(it),int(mxiter),int(isolve),int(ncrs)))
        f1.write('%9i %9.4e %9i\n' %(accl,cclose,int(iprgcg)))
        f1.close()  #fermer le fichier gcg

        #*************************** write RCT file for sorption *********************
    def WriteRctFile(self,aqui,Tbase,listE,opt):
        """ writes an RCT file in case of retardation """
        f1 = self.CreateFile(opt+'rct.dat','w')
        nrow = int(aqui.getFullGrid()['ny'])
        nlay = aqui.getNbCouches()
        if aqui.getDim() in ['Xsection','Radial']: nlay=nrow
        [aL,aT,aZ,rf] = zip(*Tbase['Transp'])[1]
        Isothm, Ireact,Irctop, Igetsc = 1,0,2,0
        f1.write('%9i %9i %9i %9i\n' %(Isothm, Ireact,Irctop, Igetsc))
        # Rec 2 : Rohb (2b and 2c not used here)
        poro = obj2matBlock(aqui,'Porosite');rhob = 2650.*(1.-poro);#print nlay,shape(poro),shape(rhob)
        for l in range(nlay):
            self.writeMatMT3D(rhob[l]*self.radfact,f1,'Rhob') # rhob matric(ncol,nrow) en kg/m3
        # line E3 sorption (isothm>0)
        Kd = (float(rf)-1.)*poro/rhob
        for l in range(nlay):
            self.writeMatMT3D(Kd[l],f1,'Kd')
        # line E4 2nd sorption coeff not used here
        for l in range(nlay): f1.write('         0  0.0 \n')
        f1.close()
            
        #*************************** write RCT file for 2domain *********************
    def WriteRct1File(self,aqui,Tbase,listE,opt):
        """ writes an RCT file in case of double porosity"""
        f1 = self.CreateFile(opt+'rct.dat','w')
        nlay = aqui.getNbCouches()
        if aqui.getDim() in ['Xsection','Radial']:
            nlay=nrow;nrow=1
        # Rec1 : Isothm, Ireact, Irctop, IGetsc Irctop 0
        # 2domain : Isothm : 5 dual domain( no sorption), igetsc>0 : initial conc read here
        Isothm, Ireact,Irctop, Igetsc = 5,0,1,1
        f1.write('%9i %9i %9i %9i\n' %(Isothm, Ireact,Irctop, Igetsc))
        # Rec 2 : Rohb do not enter if isothm=5
        # Rec3 Prsty2 only for dual domain (isothm 5 or 6)
        # the porosity matrix comes from Pht3D immobile solutions, line Imm_poro
        opt1=opt*1;
        if opt=='MT3D':opt1='Transport'
        mS=obj2matBlockNb(aqui,opt1,'zon');
        m0=mS[0]*0;imm_s=Tbase['Immobile']['Solutions']
        ie=imm_s['rows'].index('Imm_poro');
        for l in range(nlay):
            poro=m0+float(imm_s['data'][ie][1]) # data[1] backgrd
            for s in range(self.nsol-1):
                poro[abs(mS[l])/1000==s+1]=float(imm_s['data'][ie][s+2])
            self.writeMatMT3D(poro,f1,'Poro')
        # Rec4 : if Igetsc>0 initial conc in immob phase for each species 
        # run along the Chemistry to find the species for whic conc are needed
        short=['k','i','kim','p','e','s','kp'];ntot=0
        div=[1000,1000,1000,100,10,100,1]
        lon=['Solutions']*3;lon.extend(['Phases','Exchange','Surface','Phases'])
        for ik in range(len(short)):
            l0=listE[short[ik]]  # list of species present in chemistry
            for esp in l0:
                if esp in ['Imm_poro','Transf_coeff']: continue
                kw=lon[ik];imm=Tbase['Immobile'][kw].copy();ntot+=1
                ie=imm['rows'].index(esp);#print 'mtpht rct',kw,esp,ie
                for l in range(nlay):
                    cnc=m0+float(imm['data'][ie][1]);#print imm['data'][ie][1]
                    nsp=len(imm['cols'])-1
                    for s in range(nsp-1): # to find the place where BC is true solution
                        cnc[abs(mS[l])/div[ik]==s+1]=float(imm['data'][ie][s+2])
                    self.writeMatMT3D(cnc,f1,esp)
        # Rec 5 sorption1 (each species)
        for i in range(ntot): f1.write('        0  0.0 \n')
        # Rec6 sorption 2, here mass transfer coeff for all species
        ie=imm_s['rows'].index('Transf_coeff');
        for i in range(ntot):
            for l in range(nlay):
                tcoeff=m0+float(imm_s['data'][ie][1]) # data[1] backgrd
                for s in range(self.nsol-1): # to find the place where BC is true solution
                    tcoeff[abs(mS[l])/1000==s+1]=float(imm_s['data'][ie][s+2])
                self.writeMatMT3D(tcoeff,f1,'Transf Coeff')
        #REc7 RC1 parm for fisrt order deg1
        for i in range(ntot): f1.write('        0  0.0 \n')
        #REc8 RC2 parm for fisrt order deg 2
        for i in range(ntot): f1.write('        0  0.0 \n')
        f1.close()

    #********************************* Ecire fichier VDF for Seawat ********************
    def WriteVdfFile(self):
        f1 = self.CreateFile('Seawatvdf.dat','w')
##        1. MTDNCONC MFNADVFD NSWTCPL IWTABLE
##        Mtdconc=0 density specified =n dens calculated from n species
##        MFNADVFD=2 centre in sapce, ><2 upstream weigthed
##        NSWTCPL max number of non linear iterations if 0 or 1 explicit coupling
##        iwtable : 0 water table correction not applied, >0 applied
        Mtdnconc,Mfnadvdf,Nswtcpl,Iwtable=1,1,1,0
        f1.write(' %9i %9i %9i %9i   Mtdnconc Mfnadvdf Nswtcpl Iwtable \n' %(Mtdnconc,Mfnadvdf,Nswtcpl,Iwtable))
##        2. DENSEMIN DENSEMAX min an dmax density if 0 not limitation
        Densemin,Densemax=0,0
        f1.write(' %9i %9i   DENSEMIN DENSEMAX \n' %(Densemin,Densemax))
##        If NSWTCPL is greater than 1, then read item 3.
##        3. DNSCRIT convergene criterion difference in density
        Dnscrit=1e-3
        if Nswtcpl>1: f1.write(' %9.4e  \n' %Dnscrit)
##        4. DENSEREF DENSESLP
        Denseref,Denseslp=1000.,.7143 # Care in kg/m3, slp for freash and sea water
        f1.write(' %9i %9i  DENSEREF DENSESLP \n' %(Denseref,Denseslp))
##        5. FIRSTDT ength of first time step
        Firstdt=1e-3
        f1.write(' %9.4e  \n' %Firstdt)
##        FOR EACH STRESS PERIOD (read items 6 and 7 only if MTDNCONC = 0)
##        6. INDENSE if<0 val of dense reused form prev tstep
##          =0 Dense=ref >=1 dense read from item 7 =2 read from 7 but as conc
##        Read item 7 only if INDENSE is greater than zero
##        7. [DENSE(NCOL,NROW)] – U2DREL
##        Item 7 is read for each layer in the grid.
        nper=len(self.tlist);Indense=-1
        for ip in range(nper):
            if Mtdnconc==0: f1.write(' %9i %9i  INDENSE \n' %Indense)
        f1.close()

    #********************************* Ecire fichier Pht3d ********************
    def WritePht3dFile(self,aqui,Tbase,listE,parmk):
        f1 = self.CreateFile('PHT3D_ph.dat','w')
        #PH1 Record: OS TMP_LOC RED_MOD TEMP ASBIN EPS_AQU EPS_PH PACK_SZ
        # OS 1 iterative, 2 sequential. que 2 implemente
        # TMP_LOC : 0 writere dans temp, 1 : writere sur dir local
        # REd mode : 0 pH pe vairables, 1 : pe fixe, 2 : pH et pe fixes (plus rapide)
        # TEmp temperature, ASBIN : 0 : writeture fich binaire, 1 :ascii
        # eps_aqu et eps_ph : si 0 calcul partout
        # pack_sz : taille des paquets pour phreeqc 4000 chiffre OK
        temp=Tbase['PHparm'][0][1]
        os0, tmp, fix0, asbin, eps0, eps1, pack = 2,1,0,0,1e-10,.001,2000
        f1.write('%9i %9i %9i %9.1f %9i %9.1e %9.5f %9i\n' %(os0,tmp,fix0,temp,asbin,eps0,eps1,pack))
        dcharge=Tbase['PHparm'][1][1]
        f1.write('%9i\n' %dcharge)# PH2 v2 diif de charge admissibe
        # determiner le noimbre d'esp cinetiques et en faire la liste
        nInorg=len(listE['i']); #+len(self.lists);
        nKmob = len(listE['k']);nKimob = len(listE['kim']);
        nMinx= len(listE['p']);nExch=len(listE['e'])
        f1.write('%9i\n' %(nInorg))# PH3 nb compose inorganiques
        f1.write('%9i\n' %(nMinx))# PH4 nb mineraux
        f1.write('%9i %9i\n' %(nExch, 0))# PH5 nb ech ions, 0 je sais pas pourquoi
        # PH6 surface complexation 
        nSurf=len(listE['s']);f1.write('%9i\n' %nSurf)
        #PH7 Record: NR_MOB_KIN NR_MIN_KIN NR_SURF_KIN NR_IMOB_KIN
        # nb especes cinetiques mobiles, minerales, surfaces et substeps pour plus tard
        nKsurf,nKmin = 0,len(listE['kp'])
        f1.write('%9i %9i %9i %9i\n' %(nKmob, nKmin, nKsurf, nKimob))
        # PH8 : NR_OUTP_SPEC (complexes) PR_ALKALINITY_FLAG (futur)
        f1.write('%9i %9i\n' %(0,0))
        ## nb unites inutile car pht3d considere que tout est en jour
        Chem=Tbase['Chemistry']
        if Chem.has_key('Rates'):
            rates=Chem['Rates'];
            for nom in listE['k']:
                iek = rates['rows'].index(nom);
                f1.write(nom+'%5i \n '%(parmk[nom]))  #param k
                for ip in range(parmk[nom]):
                    f1.write('%9.5e \n' %float(rates['data'][iek][ip+2]))
                f1.write('-formula '+rates['data'][iek][-1] +'\n') # formula
        #for n in self.lists: f1.write(n+' \n') #  species
        optsu=Tbase['PHparm'][2][1];
        for n in listE['i']:
            add='';
            if optsu.strip()==n: add=' charge'
            f1.write(n.replace('(+','(')+add+'\n') # que reac isntant et AE, pH pe
        # kinetic immobile
        if Chem.has_key('Rates'):
            rates=Chem['Rates'];
            for nom in listE['kim']:
                iek = rates['rows'].index(nom);
                f1.write(nom+'%5i \n '%(parmk[nom]))  #param k
                for ip in range(parmk[nom]):
                    f1.write('%9.5e \n' %float(rates['data'][iek][ip+2]))
                f1.write('-formula '+rates['data'][iek][-1] +'\n') # formula
        for p in listE['p']:
            ip=Chem['Phases']['rows'].index(p)
            f1.write(p+'  '+str(Chem['Phases']['data'][ip][1])+' \n') # phase name + SI backgrd
        for n in listE['e']: f1.write(n+' -1 \n') # exchanger
        if Chem.has_key('Surface'): # surface
            su=Chem['Surface'];l=len(su['cols'])
            for esp in listE['s']:
                st=esp;ies=su['rows'].index(esp)
                for i in range(l-2,l): st+=' '+str(su['data'][ies][i])
                f1.write(st+' \n') 
            optsu=Tbase['PHparm'][3][1]
            if optsu in ['no_edl','diffuse_layer']: f1.write('-'+optsu+'\n')
        if Chem.has_key('Kinetic_Minerals'):
            kp=Chem['Kinetic_Minerals']
            for nom in listE['kp']:
                iek = kp['rows'].index(nom);
                f1.write(nom+'%5i \n '%(parmk[nom]))  #param k
                for ip in range(parmk[nom]):
                    f1.write('%9.5e \n' %float(kp['data'][iek][ip+1]))
        f1.close()

    #  ''''''''''''''''''''''''''''''' fonction writeMatMT3D '''''''''''''''''''''''''''
    def writeVecMT3D(self, v, f1, name=' '):
        l = len(v);a=str(type(v[0]))
        if a[13:16]=='int': typ='I'
        else : typ='G'
        if amin(v)==amax(v):
            f1.write('         0 %7.3e  #'%(amin(v)) +name+'\n')
            return
        if typ=='I': fmt='      100    1      ('+str(l)+'I'+str(ln)+')'
        else : fmt='      100    1.0      ('+str(l)+'G12.4)'            
        f1.write(fmt)
        f1.write('\n')
        
        if typ=='I': fmt='%'+str(ln)+'i'
        else : fmt='%+11.4e '
        for i in range(l):
            f1.write(fmt %v[i])
        f1.write('\n')
        
    def writeMatMT3D(self,m,f1,name=' '):
        if len(shape(m))<=1: return self.writeVecMT3D(m,f1,name)
        [l,c] = shape(m);ln=3;a=str(type(m[0,0]))
        if a[13:16]=='int': typ='I'
        else : typ='G'
        if amin(amin(m))==amax(amax(m)):
            if typ=='I':f1.write('         0 %8i #'%(amin(amin(m))) +name[:6]+'\n' )
            else:f1.write('         0 %7.3e #' %(amin(amin(m))) +name[:6]+'\n' )
            return
        if typ=='I': fmt='      100    1      ('+str(c)+'I'+str(ln)+')'
        else : fmt='      100    1.0      ('+str(c)+'G12.4) #'+name[:6]          
        f1.write(fmt+'\n')
        
        if typ=='I': fmt='%'+str(ln)+'i'
        else : fmt='%11.4e '         
        for i in range(l-1,-1,-1):
            for j in range(c):
                f1.write(fmt %m[i][j])
            f1.write('\n')
        
    def writeBlockMT3D(self,m,f1,name=' '):
        if len(shape(m))==3:
            nlay,a,b=shape(m)
            for l in range(nlay): self.writeMatMT3D(m[l],f1,name)
        else : self.writeMatMT3D(m,f1,name)

    def WritePhreeqc(self,aqui,Tbase,listE):
        """this routine writes a phreeqc file where all solutions are written in
        phreqc format to be able to test their equilibrium before running pht3d
        1. tabke background, then cycle through pht3d zones
        2. get the solution number, phase number...it does not take rates
        3 write them in phreeqc format"""
        f1 = self.CreateFile('solutions.phrq','w')
        f1.write('Database '+self.pPath+'\pht3d_datab.dat \n')
        zones=aqui.getZoneList('PHT3D')
        nzone=len(zones)
        for i in range(nzone):
            z=zones[i];val=z.getVal()
            if type(val)==type([5]): val=int(val[0].split()[1]) #case of transient chemistry
            else : val=int(val)
            f1.write('Solution '+str(i)+' \n units mol/L \n')
            solu=Tbase['Chemistry']['Solutions'];
            nsol=val/1000
            for esp in listE['i']: # go through phase list
                ie=solu['rows'].index(esp);#print esp,phases['rows'],ip,phases['data'][ip] # index of the phase
                conc=solu['data'][ie][nsol+1] #backgr concentration of species
                f1.write(esp+' '+str(conc)+'\n')
            f1.write('Equilibrium_Phases '+str(i)+'\n')
            phases=Tbase['Chemistry']['Phases'];
            nphas=mod(val,1000)/100
            for esp in listE['p']: # go through phase list
                ip=phases['rows'].index(esp);#print esp,phases['rows'],ip,phases['data'][ip] # index of the phase
                IS,conc=phases['data'][ip][nphas*2+1:nphas*2+3] #backgr SI and concentration of phase
                f1.write(esp+' '+str(IS)+' '+str(conc)+'\n')
            f1.write('end \n')
        f1.close()
        
class MP3dReader:

    """ on recupere le nom du projet pour effectuer l'ouverture du projet a partir de ce nom """
    def __init__(self, pPath, pName):
        self.pPath = pPath
        self.pName = pName

    def lireUCN(self, aqui,opt, tstep, iesp): # struct 32*4+6*4+icbund(nrow*ncol)+3*4+Cnc(nrow,ncol)+4?
        """lecture fichier ucn, typ : rt ou pht, donner le tstep, le num de l'espece et aqui"""
        grd  = aqui.getFullGrid()
        x0,dcol,ncol = grd['x0'],grd['dx'],grd['nx']
        y0,drow,nrow = grd['y0'],grd['dy'],grd['ny']
        nlay = aqui.getNbCouches()
        if aqui.getDim() in ['Xsection','Radial']:
            nlay=nrow*1;nrow=1
        if iesp<9: suff='00'
        else : suff='0'
        tlist=aqui.getZoneTransient()['tlist']
        fname=self.pPath+os.sep+opt+suff+str(iesp+1)+'.UCN'
        try: f1=open(fname,'rb')
        except IOError: return None
        m0=zeros((nlay,nrow,ncol))+0.;mult=1;
        if opt=='MT3D': # pb Mt3d sometimes write more time steps...
            lt=self.getMt3dTlist(f1,ncol,nrow,nlay);#print 'ireUcn',tstep,lt
            #print 'mtpht ucn',ncol,nrow,nlay,tstep,lt
            tstep=argmin(abs(tlist[tstep]-lt))+1;#a=arange(len(lt));tstep=max(a[lt==tstep])
        elif opt=='PHT3D':
            tstep=tstep+1
        p0 = (44+ncol*nrow*4)*nlay*tstep;#print 'mp3read',tstep,nlay
        for l in range(nlay):
            pos=p0+(44+ncol*nrow*4)*l+44;f1.seek(pos) # v212
            data = arr2('f');data.fromfile(f1, ncol*nrow)
            m0[l]=reshape(data,(nrow,ncol))
        f1.close()
        if aqui.getDim() in ['Xsection','Radial']:return m0[::-1,:,:]
        else : return m0[:,::-1,:]

    def getPtObs(self,aqui,irow,icol,ilay,iper,opt,iesp=0):
        """a function to values of one variable at given point or points.
        irow, icol and ilay must be lists of the same length. iper is also
        a list containing the periods for which data are needed."""
        grd = aqui.getFullGrid();ncol, nrow = grd['nx'], grd['ny']
        nlay=aqui.getNbCouches();
        if aqui.getDim() in ['Xsection','Radial']:
            nlay=nrow*1;nrow=1
        if iesp<9: suff='00'
        else : suff='0'
        tlist=aqui.getZoneTransient()['tlist']
        fname=self.pPath+os.sep+opt+suff+str(iesp+1)+'.UCN'
        blok=44+ncol*nrow*4;
        try : f1 = open(fname,'rb')
        except IOError: return None
        if aqui.getDim() in ['Xsection','Radial']:
            ilay=irow*1;irow=[0]*len(ilay)
        npts=len(irow);pobs=zeros((len(iper),npts))+0.;
        lt=self.getMt3dTlist(f1,ncol,nrow,nlay)
        #print 'mtpht obs',iper,lt
        for ip in range(len(iper)):
            if opt=='MT3D':
                ip2=argmin(abs(tlist[iper[ip]]-lt))+1#a=arange(len(lt));;ip2=max(a[lt==iper[ip]])
            elif opt=='PHT3D' :
                ip2=iper[ip]+1
            p0=blok*nlay*ip2;
            for i in range(npts):
                f1.seek(p0+blok*ilay[i]+44+irow[i]*ncol*4+icol[i]*4)
                try:
                    data = arr2('f');data.fromfile(f1,1);
                    pobs[ip,i]=float(data[0])
                except EOFError: return pobs
        return pobs
   
    def getMt3dTlist(self,f1,ncol,nrow,nlay):
        tread=[];i=0;blok=(44+ncol*nrow*4)*nlay
        while 3>2:
            f1.seek(blok*i+12);
            try :
                #i1=arr2('i');i1.fromfile(f1,1);
                a=arr2('f');a.fromfile(f1,1);#print 'mt per',i1,a
                tread.append(a[0]);i+=1 #this is the true time given by mt3d
            except EOFError:
                #print ncol,nrow,nlay,tread;
                return array(tread)
