import os

def importDB(fname):
#if 3>2:
    dicDB={'RATES':None}
    keyw=['SOLUTION_MASTER_SPECIES','SOLUTION_SPECIES','PHASES','RATES',
          'EXCHANGE_MASTER_SPECIES','EXCHANGE_SPECIES','SURFACE_MASTER_SPECIES',
          'SURFACE_SPECIES','END']
    klow=['log_k','delta_h','-gamma']
    for k in keyw: dicDB[k]={}
    f1=open(fname)
    curkw='';bufr='';cursp='';parmk={};npk=0;master={}
    for li in f1:
        li2=li.strip()
        if li2=='':continue
        if li2[0]=='#':continue
        li2=li2.split('#')[0];
        if li2 in keyw:
            curkw=li2;continue
        if curkw=='SOLUTION_MASTER_SPECIES': #master species
            a=li.split()
            master[a[0]]=a[1:]
                
        if curkw=='PHASES': # mineraux
            li3=li2.split();
            if len(li2.split('='))>1 or li3[0] in ['-analytic','log_k','delta_h']: a=0
            else:
                dicDB['PHASES'][li3[0]]='';bufr='' # store name of the phase
             

        if curkw=='RATES': # cinetiques
            li3=li2.strip()
            if (li3 in master.keys()) or (li3 in dicDB['PHASES']):
                cursp=li3
            else: bufr=bufr+li
            if li2[:4]=='-end': # stocker les donnees
                dicDB['RATES'][cursp]=bufr;mxp=1
                for i in range(1,20): # compter le nb de parametres
                    if bufr.count('parm('+str(i)+')')>0:mxp=i
                bufr='';parmk[cursp]=mxp
                if mxp>npk: npk=mxp

        if curkw=='EXCHANGE_SPECIES': # exchange species
            a=li.replace('\n','');a=a.split('=');
            if len(a)>1:dicDB[curkw][a[-1]]=0

        if curkw=='SURFACE_MASTER_SPECIES': #surface master species
            a=li.split()
            dicDB[curkw][a[0]]=0
                
    elts=master.keys();
    # enlever les especes de base si redox present
    for esp in elts:
        if len(esp.split('('))>1:
            debut=esp.split('(')[0];
            if master.has_key(debut):
                master.pop(debut);
    for n in ['E','O(-2)']:
        if master.has_key(n): master.pop(n)
    master['pH']='';master['pe']='';
    dicDB[keyw[0]]=master;
    f1.close(); 
    return dicDB,npk

