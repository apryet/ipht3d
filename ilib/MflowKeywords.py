groups={
'1.dis':['1.1','1.2','1.3','1.4','1.5','1.6','1.7','1.8'],
'2.ba6':['2.1','2.2','2.3','2.4','2.5'],
'3.bcf':['3.1','3.2','3.3','3.4','3.5','3.6','3.7','3.8','3.9'],
'4.lpf':['4.1','4.2','4.3','4.4','4.5','4.6','4.7','4.8','4.9','4.10','4.11','4.12','4.13'],
'5.wel':['5.1','5.2'],
'6.rch':['6.1','6.2'],
'7.sip':['7.1','7.2'],
'8.pcg':['8.1','8.2'],
'9.sor':['9.1','9.2'],
'10.de4':['10.1','10.2']
}
lines={
'1.1':{'comm':'Title','cond':'','kw':['title'],'detail':[],'type':''},
'1.2':{'comm':'Model properties','cond':'','kw':['NLAY','NROW','NCOL','NPER','ITMUNI','LENUNI'],
       'detail':['Nb of layers','Nb of rows','Nb of columns','Nb of periods',['time units','-','sec','min','hours','days','years'],
        ['length units','-','ft','m','cm']],'type':''},
'1.3':{'comm':'type of layer','cond':'','kw':['LAYCBD'],'detail':[],'type':'string'},
'1.4':{'comm':'Col width','cond':'','kw':['DELR(NCOL)'],'detail':[],'type':'vec'},
'1.5':{'comm':'Row height','cond':'','kw':['DELC(NROW)'],'detail':[],'type':'vec'},
'1.6':{'comm':'Top','cond':'','kw':['TOP(NCOL,NROW)'],'detail':[],'type':'arr'},
'1.7':{'comm':'Bottom','cond':'','kw':['BOTM(NLAY,NCOL,NROW)'],'detail':[],'type':'arr'},
'1.8':{'comm':'Periods characteristics','cond':'','kw':['PERLEN(NPER)','NSTP(NPER)','TSMULT(NPER)','SsTr(NPER)'],
       'detail':[],'type':'nvec'},

'2.1':{'comm':'Bas title 1','cond':'','kw':['title'],'detail':[],'type':''},
'2.2':{'comm':'Bas options','cond':'','kw':['bas_opt'],'detail':[],'type':''},
'2.3':{'comm':'Boundary conditions','cond':'','kw':['IBOUND(NLAY,NCOL,NROW)'],'detail':[],'type':'arr'},
'2.4':{'comm':'value of head for no flow','cond':'','kw':['HNOFLO'],'detail':[],'type':''},
'2.5':{'comm':'Starting head','cond':'','kw':['STRT(NCOL,NROW)'],'detail':[],'type':'arr'},

'3.1':{'comm':'General flags','cond':'','kw':['IBCFCB','HDRY','IWDFLG','WETFCT','IWETIT','IHDWET'],
       'detail':[['write budget','no','yes'],'head for dry cells',['wetting','inactive','active'],
                 'factor to wet','iteration interval for wetting',['wetting equation','eq1','eq2']],'type':''},
'3.2':{'comm':'Type of layer (average/confinement)','cond':'','kw':['Ltype(NLAY)'],'detail':[],'type':'string'},
'3.3':{'comm':'anisotropy factor','cond':'','kw':['TRPY(NLAY)'],'detail':[],'type':'vec'},
'3.4':{'comm':'First storage coeff','cond':'NPER>1','kw':['Sf1(NCOL,NROW)'],'detail':[],'type':'arr'},
'3.5':{'comm':'Transmissivity','cond':'LAYCON in [0,2]','kw':['Tran(NCOL,NROW)'],'detail':[],'type':'arr'},
'3.6':{'comm':'Hydraulic conductivity','cond':'LAYCON in [1,3]','kw':['HY(NCOL,NROW)'],'detail':[],'type':'arr'},
'3.7':{'comm':'Vertical conductance','cond':'NLAY>1','kw':['Vcont(NCOL,NROW)'],'detail':[],'type':'arr'},
'3.8':{'comm':'2nd storage coeff','cond':'NPER>1 and LAYCON>=2','kw':['Sf2(NCOL,NROW)'],'detail':[],'type':'arr'},
'3.9':{'comm':'','cond':'IWDFLG!=0 and LAYCON in [1,3]','kw':['WETDRY(NCOL,NROW)'],'detail':[],'type':'arr'},

'4.1':{'comm':'General flags','cond':'','kw':['ILPFCB','HDRY','NPLPF'],
       'detail':[['write budget','no','yes'],'head for dry cells','Nb Lpf params'],'type':''},
'4.2':{'comm':'Type of layer (confinement)','cond':'','kw':['LAYTYP(NLAY)'],'detail':[],'type':'string'},
'4.3':{'comm':'Type of averaging','cond':'','kw':['LAYAVG(NLAY)'],'detail':[],'type':'string'},
'4.4':{'comm':'anisotropy flag','cond':'','kw':['CHANI(NLAY)'],'detail':[],'type':'string'},
'4.5':{'comm':'flag for vertical cond','cond':'','kw':['LAYVKA(NLAY)'],'detail':[],'type':'string'},
'4.6':{'comm':'wetting active or inactive','cond':'','kw':['LAYWET(NLAY)'],'detail':[],'type':'string'},
'4.7':{'comm':'calculation of wetting','cond':'LAYWET>0','kw':['WETFCT','IWETIT','IHDWET'],'detail':[],'type':''},
'4.8':{'comm':'Hydraulic conductivity','cond':'','kw':['HK(NLAY,NCOL,NROW)'],'detail':[],'type':'larr'},
'4.9':{'comm':'Vertical conductivity','cond':'','kw':['VKA(NCOL,NROW)'],'detail':[],'type':'larr'},
'4.10':{'comm':'First storage coeff','cond':'NPER>1','kw':['Sf1(NCOL,NROW)'],'detail':[],'type':'larr'},
'4.11':{'comm':'2nd storage coeff','cond':'NPER>1 and LAYTYP>0','kw':['Sf2(NCOL,NROW)'],'detail':[],'type':'larr'},
'4.12':{'comm':'Vertical conductivity confined bed','cond':'LAYCBD>0','kw':['VKCB(NCOL,NROW)'],'detail':[],'type':'larr'},
'4.13':{'comm':'Threshold wetting and neighbours','cond':'LAYWET!=0 and LAYTYP!=0','kw':['WETDRY(NCOL,NROW)'],'detail':[],'type':'larr'},

'5.1':{'comm':'Flags for Wells','cond':'','kw':['MXACTW','IWELCB'],'detail':['total nb of wells','save budget'],'type':''},
'5.2':{'comm':'Wells','cond':'','kw':['WLayer','WRow','WColumn','WQ'],'detail':[],'type':'npoints'},

'6.1':{'comm':'Flags for recharge','cond':'','kw':['NRCHOP','IRCHCB'],'detail':['position of recharge','save to budget'],'type':''},
'6.2':{'comm':'Recharge value','cond':'','kw':['RECH'],'detail':[],'type':'parr'},

'7.1':{'comm':'SIP globals','cond':'','kw':['MXITER','NPARM'],'detail':['Mx nb of iteration','Nb of iteration variables'],'type':''},
'7.2':{'comm':'Steps','cond':'','kw':['SACCL','SHCLOSE','IPCALC','WSEED','IPRSIP'],'detail':['Acceleration','tolerance for head',['seed','given','calculated'],'seed value','print interval'],'type':''},

'8.1':{'comm':'PCG globals','cond':'','kw':['MXITER','ITER1','NPCOND'],'detail':['Mx nb of iteration','inner iterations',['solution','-','Cholesky','Polynomial']],'type':''},
'8.2':{'comm':'Steps','cond':'','kw':['PHCLOSE','RCLOSE','RELAX','NBPOL','IPRPCG','MUTPCG','DAMP'],'detail':['Head tolerance,','residual volume convergence','Relaxation',['upper bound','-','calculated','=2'],'print interval',['print','all tables','nb of iterations','no print','if fail'],'Damping factor'],'type':''},

'9.1':{'comm':'SOR globals','cond':'','kw':['MXITER'],'detail':['Mx nb of iteration'],'type':''},
'9.2':{'comm':'SOR globals','cond':'','kw':['OACCL','OHCLOSE','IPRSOR'],'detail':['Accelaeration','head tolerance','print interval'],'type':''},

'10.1':{'comm':'DE4 globals','cond':'','kw':['ITMX','MXUP','MXLOW','MXBW'],'detail':['Mx nb of iteration','Mx eq upper','Mx eq lower','Mx eq Bwidth'],'type':''},
'10.2':{'comm':'Steps','cond':'','kw':['IFREQ','MUTD4','DACCL','DHCLOSE','IPRD4'],'detail':['Flag for Freq','Flag for print','acceleration','head tolerance','time step to print'],'type':''},

}
