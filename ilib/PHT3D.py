import os
from phtDbase import *
from scipy import zeros
from MtphtWriter import *

class PHT3D:
    """A class that gathers thhe actions for Pht3d, except writing that is left to
    rtphtwriter"""
    def __init__(self, model):
        self.model, self.aqui, self.ecoul = model,model.Aquifere,model.Ecoulement;
        self.initBase()
        
    def initBase(self):
        self.Base= {}
        self.Base['Chemistry']={'Solutions':None,'Rates':None,'Phases':None,
                'Exchange':None,'Surface':None,'Kinetic_Minerals':None}
        self.Base['DualPoro']=[('Immob_porosity',0.),('Transf_coeff',0.)]
        self.Base['Recharge']=[]
        self.Base['PHparm']=[('Temp',25),('Delta_charge',0.),('charge_on_element',' '),\
                ('option_surface',' '),('Nb of solutions',4)]
        self.Base['Immobile']={'Solutions':None,'Phases':None,'Exchange':None,'Surface':None}
        self.temp={}
        self.temp['Dbase']={}
        self.temp['DBfile']=''
        self.temp['reac']=[0,0,0]  #isoth, ireac, isolver
        self.temp['period']=[0]  # liste de duree et conc de chque periode
        self.temp['run']=0  # Pht3d n'a pas tourne
        self.nsol=4
        self.listTemps,self.listUserEsp=[],[' ']
        self.Eactuel,self.Uactuel=0,'mmol/L'
        
    def getBase(self): return self.Base
    def setBase(self,base):
        for k in base.keys():
            if k in ['Chemistry','Immobile']:
                self.Base[k]=base[k].copy();continue
            if len(self.Base[k])==0: continue
            lb0,val0=zip(*self.Base[k])
            lb1,val1=zip(*base[k]);
            self.Base[k]=[]
            lb0=list(lb0);val0=list(val0);
            for i in range(len(lb0)):
                if lb0[i] in lb1:
                    i1=lb1.index(lb0[i])
                    val0[i]=val1[i1]
            self.Base[k]=zip(lb0,val0)

    # version 1_k
        if self.Base.has_key('Recharge')==False: self.Base['Recharge']=[]
        if self.Base.has_key('PHparm')==False:
            self.Base['PHparm']=[('Temp',25),('Delta_charge',0.),('charge_on_element',' '),\
                ('option_surface',' '),('Nb of solutions',4)]

    def getParm(self,nom):
        if nom=='Variable': return ['','PH_Source','PH_Rech']
        else: return self.Base[nom]
        
    def setParm(self,nom,lst2): self.Base[nom] = lst2
    def getParmDetail(self,nom):
        l1=self.Base['PHparm'];
        n,v=zip(*l1);
        ind=n.index(nom)
        return v[ind]
        
    def getListTemps(self):
        return self.aqui.getZoneTransient()['tlist']
    def getEactuel(self): return self.Eactuel
    def setUserEsp(self,lEsp): self.listUserEsp=lEsp
    def setSolutions(self,solu):
        self.Base['Chemistry']['Solutions']=solu;#print solu
        self.nsol=len(solu['cols'])+1
    
    def doAction(self,nom):
        if nom=='Import':
            if 'pht3d_datab.dat' not in os.listdir(self.model.getProject()[0]):
                return 'fichier pht3d_datab.dat absent'
            fname = str(self.model.getProject()[0]+os.sep+'pht3d_datab.dat')
            self.tempDbase,self.npk= importDB(fname);
            self.updateChemistry()
            return 'Database importee'
        if nom=='Write':
            a=self.ecrireMP3();
            if a!=None: return ['Fichiers PHT3D ecrits']
        if nom=='Run':
            dirFich = self.model.getProjectPath()
            lf = os.listdir(dirFich);
            if 'PHT3D.nam' not in lf: return 'Fichiers non ecrits'
            add='pht3dv217.exe" pht3d.nam'
            cmd = '"'+self.model.gui.mainDir+os.sep+'bin'+os.sep+add
            os.chdir(dirFich);os.system(cmd)
            self.temp['run']=1    

    def getObject(self,nom,tag,itemps,plan,ori='Z'):
        #ramener un array de resultats :
        #nom : dans la liste des boites de visu, tag : valeur de liste nom
        [A,B]=self.aqui.getMeshCentre(ori,plan)
        esp=self.Eactuel;
        if nom in ['Especes','User'] : self.Eactuel=esp=tag
        elif nom=='Units': self.Uactuel=units=tag
        iesp, mult = 0,1.
        if esp in self.listEspece : iesp = self.listEspece.index(esp)
        if esp not in ['pH','pe']:
            if self.Uactuel=='mol/L':mult=1.
            elif self.Uactuel=='mmol/L':mult=1000.
            elif self.Uactuel=='umol/L':mult=1e6
            elif self.Uactuel=='nmol/L':mult=1e9
        # case of user defined species
        if esp in self.listUserEsp[0]:
            ie=self.listUserEsp[0].index(esp);eq=self.listUserEsp[1][ie];
            a='self.MP3dReader.lireUCN(self.aqui,\"PHT3D\",'+str(itemps)
            for es in self.listEspece:
                if eq.rfind(es)>-1:
                    eq=eq.replace(es,a+','+str(self.listEspece.index(es))+')')
            exec('c0='+eq)
        else : c0=self.MP3dReader.lireUCN(self.aqui,'PHT3D',itemps,iesp)
        if c0==None: self.model.gui.OnMessage('pas de fichier')
        if self.aqui.getDim() in ['Xsection','Radial']:
            ori='Y';plan=0
        if ori=='Z':conc = c0[plan,:,:]*mult
        elif ori=='Y':conc = c0[:,plan,:]*mult
        elif ori=='X':conc = c0[:,:,plan]*mult
        return [A,B,conc]
    
    def setReader(self):
        pPath, pName = self.model.getProjectPath(),self.model.getProjectName()
        self.MP3dReader = MP3dReader(pPath, pName)

    def calcNbParm(self):
        """calculer le nb d eparm par espece : utile si la DB n'a aps ete
        importee ce coup-ci"""
        mxp=0;parmk={}
        rates=self.Base['Chemistry']['Rates'];
        npk=len(rates['cols'])-2
        if rates==None: return parmk
        for n in rates['rows']:
            iek=rates['rows'].index(n);mxp=0
            for ip in range(1,npk): # compter le nb de parametres
                if rates['data'][iek][ip+1]!=0:mxp=ip
            parmk[n]=mxp
            if mxp>npk: npk=mxp
        kmin=self.Base['Chemistry']['Kinetic_Minerals']
        if kmin==None: return parmk
        for n in kmin['rows']:
            iek=kmin['rows'].index(n);mxp=0
            for ip in range(1,len(kmin['cols'])): # compter le nb de parametres
                if kmin['data'][iek][ip]>0:mxp=ip
            parmk[n]=mxp
            if mxp>npk: npk=mxp
        return parmk
        
    def updateChemistry(self):
        """update the Chemistry dictionnary from the database
        elements, rates and phases,. Data is a list of lists, one list for
        one colon, the list are ordered according to the rows names"""
        # for chemistry
        old=self.Base['Chemistry'].copy();dic={};#print old['Solutions']
        for n in ['Solutions','Rates','Phases','Exchange','Surface','Kinetic_Minerals','Species']:
            dic[n]={}
            dic[n]['rows'],dic[n]['cols'],dic[n]['data'],dic[n]['mmol']=[],[],[],[];
        # update all dictionnaries
        kw=['Solutions','Rates','Phases','Exchange','Kinetic_Minerals','Surface']
        dbkw=['SOLUTION_MASTER_SPECIES','RATES','PHASES','EXCHANGE_SPECIES',\
              'RATES','SURFACE_MASTER_SPECIES']
        lc1=['C','Backgrd'];
        nsolu=self.getParmDetail('Nb of solutions')
        if old['Solutions']!=None: nsolu=max(nsolu,len(old['Solutions']['cols'])-1)
        for i in range(nsolu-1): lc1.append('Solu'+str(i+1))
        lcolk=['C','IM'];lcolk.extend(['parm'+str(i+1) for i in range(self.npk)])
        lcolk.append('Formula');
        lc2=['C','Backg_SI','Backg_Moles','Ass1_SI','Ass1_Moles','Ass2_SI','Ass2_Moles',\
            'Ass3_SI','Ass3_Moles','Ass4_SI','Ass4_Moles']
        lc3=['C','Backgrd','Assembl1','Assembl2','Assembl3','Assembl4','Assembl5']
        lc4=['C','Site_back','Sites1','Sites2','Sites3','Sites4','Specif_area','mass']
        lckp=lcolk[:-1];lckp.remove('IM')
        lcols=[lc1,lcolk,lc2,lc3,lckp,lc4]
        le1=self.tempDbase['PHASES']
        l0=self.tempDbase['RATES'];l2=[]
        for r in l0:
            if r not in le1: l2.append(r)
        lexclude=[None,le1,None,None,l2,None]
        for i in range(len(kw)):
            dic=self.updateDict(dic,old,kw[i],dbkw[i],lcols[i],lexclude[i])
        self.Base['Chemistry'] = dic;#print dic
        
        # for immobile : dual domain poro
        if self.Base.has_key('Immobile'): old=self.Base['Immobile'].copy()
        else : old={'Solutions':None,'Phases':None,'Exchange':None,'Surface':None}
        dic={};
        # add poro and exch to solutions
        self.tempDbase['SOLUTION_MASTER_SPECIES']['Imm_poro']=''
        self.tempDbase['SOLUTION_MASTER_SPECIES']['Transf_coeff']=''
        kw=['Solutions','Phases','Exchange','Surface']
        for n in kw:
            dic[n]={}
            dic[n]['rows'],dic[n]['cols'],dic[n]['data'],dic[n]['mmol']=[],[],[],[];
        # update all dictionnaries
        dbkw=['SOLUTION_MASTER_SPECIES','PHASES','EXCHANGE_SPECIES','SURFACE_MASTER_SPECIES']
        lcols=[lc1,lc2,lc3,lc4]
        for i in range(len(kw)):
            dic=self.updateDict(dic,old,kw[i],dbkw[i],lcols[i],None)
        self.Base['Immobile'] = dic; #print 'Immob',dic
        
    def getChemDict(self,keyword):
        return self.Base['Chemistry'][keyword]
    
    def setChemDict(self,keyword,dict):
        self.Base['Chemistry'][keyword]=dict
        
    def updateDict(self,dic,old,kw,dbkw,lcols,lexclude=None):
        lrows=self.tempDbase[dbkw].keys();lrows.sort();lrows2=[]
        if lexclude!=None:
            for r in lrows:
                if r not in lexclude: lrows2.append(r)
            lrows=lrows2*1
        if len(lrows)!=0:
            dic[kw]['rows']=lrows;dic[kw]['cols']=lcols
            for i in range(len(lrows)):
                if kw=='Rates':
                    a=[False,False];a.extend([0.]*(len(lcols)-2))
                else :
                    a=[False];a.extend([0.]*(len(lcols)-1))
                dic[kw]['data'].append(a)
            if old[kw]!=None:
                for esp in lrows: # get data from current phases
                    if esp not in old[kw]['rows']: continue
                    iold=old[kw]['rows'].index(esp);
                    inew=dic[kw]['rows'].index(esp)
                    for col in lcols:
                        icnew=lcols.index(col);oldcol=old[kw]['cols']
                        if col not in oldcol: continue
                        icold=oldcol.index(col)
                        dic[kw]['data'][inew][icnew]=old[kw]['data'][iold][icold]
        return dic
    
    def getMmol(self,esp):
        lesp1=self.Base['Chemistry']['Solutions']['rows']
        lesp2=self.Base['Chemistry']['Rates']['rows']
        if esp in lesp1:
            iesp=lesp1.index(esp)
            mmol=self.Base['Chemistry']['Solutions']['mmol'][iesp]
        if esp in lesp2:
            iesp=lesp2.index(esp)
            mmol=self.Base['Chemistry']['Rates']['mmol'][iesp]
        else : mmol=0.
        return float(mmol)

    def ecrireMP3(self):
        pPath, pName = self.model.getProjectPath(),self.model.getProjectName()
        fullPath = pPath+os.sep+pName;#print pName
        writer = MP3dWriter(self.model, pPath, pName)
        Tbase = self.model.Transport.getBase().copy();Tbase.update(self.Base)
        t0 = self.ecoul.getParm('Temps');
        listsE=self.getListEsp();
        tf=float(t0[0][1]);dur=t0[1][1];nstep=t0[2][1];
        lstress=arange(dur,tf*1.01,dur)
        parmk=self.calcNbParm();
        writer.WriteMP3dFile(self.aqui,listsE,Tbase,[lstress,nstep],'PHT3D',parmk)
        self.setListEsp()
        a=self.listEspece*1;#a.extend(self.listUserEsp[0]);
        self.model.setGlistGroup('PHT3D',a)
        return 'ok'
    
    def setListEsp(self):
        """ uses database and getLisEsp to retrieve the full list of species
        this list is then stored in self.listEspece
        the MP3 reader is also set here """
        pPath, pName = self.model.getProjectPath(),self.model.getProjectName()
        self.MP3dReader = MP3dReader(pPath, pName)
        listE=self.getListEsp();a=[]
        for k in ['k','i','kim','p','e','s','kp']: a.extend(listE[k])
        self.listEspece = a
        if self.model.gui!=None: self.model.gui.afficheTree.setNames('PHT3D_Especes_L',a)
        
    def getListEsp(self):
        aqui=self.aqui;chem=self.Base['Chemistry'];listE={}
        if chem['Solutions']==None:
            return {'k':[],'i':[],'kim':[],'p':[],'e':[],'kp':[],'s':[]}
        #for previous versions
        for kw in ['Kinetic_Minerals','Surface']:
            if chem.has_key(kw)==False:chem[kw]=None
        #rates
        listE['k']=[];listE['kim']=[]
        if chem['Rates']!=None:
            rates=chem['Rates'];
            for ir in range(len(rates['rows'])):
                if rates['data'][ir][0]:
                    if rates['data'][ir][1]: # if true immobile kinetics
                        listE['kim'].append(rates['rows'][ir])
                    else :
                        listE['k'].append(rates['rows'][ir])
        # solutions
        listE['i']=[]
        solu=chem['Solutions'];rows=solu['rows']
        self.nsol=len(solu['data'][0])-2;#print self.nsol
        nrow=len(rows);anySol=[False]*self.nsol;#print anySol
        for ir in range(nrow):
            esp = rows[ir]
            if solu['data'][ir][0]:
                if esp not in listE['kim']:
                    listE['i'].append(rows[ir])
                for s in range(self.nsol):
                    if float(solu['data'][ir][2+s])!=0.: anySol[s]=True
        #remove species already present in kinetic
        for n in listE['k']:
            if n in listE['i']: listE['i'].remove(n)
        mcomp=len(listE['i'])+len(listE['k'])
        # phases,exchange,kinet minerals,surface
        kw=['Kinetic_Minerals','Phases','Exchange','Surface']
        short=['kp','p','e','s']
        for ik in range(len(kw)):
            listE[short[ik]]=[]
            if chem[kw[ik]]!=None:
                d=chem[kw[ik]];
                for ir in range(len(d['rows'])):
                    if (short[ik]=='p') and (d['rows'][ir] in listE['kp']):
                        continue  # case of phases defined in kinetic minerals
                    if (d['data'][ir][0]): listE[short[ik]].append(d['rows'][ir]) 
        # other dissolved species (complexes...)
##        lists=[]
##        if chem.has_key('Species'):
##            for n in chem['Species']['rows']:lists.append(n);
        ncomp=mcomp+len(listE['kim'])
        for k in ['p','e','s','kp']:ncomp+=len(listE[k])
        listE['ncomp']=ncomp;listE['mcomp']=mcomp-2;listE['anySol']=anySol
        return listE

    def getPtObs(self,irow,icol,ilay,per,esp):
        l0 = self.getListEsp();lesp=[]
        for k in ['k','i','kim','p','e','s','kp']:lesp.extend(l0[k])
        pt=[]
        for i in range(len(esp)):
            iesp = lesp.index(esp[i])
            pt.append(self.MP3dReader.getPtObs(self.aqui,irow,icol,ilay,per,'PHT3D',iesp))
        return pt

