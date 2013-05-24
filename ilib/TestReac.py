# Aquifere
from VisualRflowModel import *;from Aquifere import *
model = VisualRflowModel(None,'d://rflowpy//lib2_2a');
################### Ecoulement #########################
from Ecoulement import *;from modflowWriter import *;import os
def ec(model,aqui):
    ecoul = Ecoulement(model)
##    s=ecoul.getParm('Solver');s['hclose']=1e-15;s['rclose']=1e-15;
##    s['mxiter']=1;s['iter1']=15000;ecoul.setParm('Solver',s)
    #### lancer modflow
    cwd=os.getcwd();bindir = 'd://rflowpy//lib2_2a//bin'
    path = model.getProject()[0];name=model.getProject()[1]
    mfwrite = ModflowWriter(path,name)
    mfwrite.WriteModflowFile(aqui, ecoul, model)
    os.chdir(path);os.system(bindir+'//mf2k1_10 '+name+'.nam')
    os.chdir(cwd)
    mfread = ModflowReader(path,name)
    ecoul.setModflow([mfread.ReadHeadFile(aqui),mfread.ReadFloFile(aqui)])
    return ecoul
#########################################################
def op(model):
    filename = model.project[0] + os.sep + model.project[1] + '.rflow'
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
##model.setProject(['d://rflowpy//validetr//homogen','homogen0'])
##model.setProject(['d://rflowpy//validereac//homog1c','homog1c'])
##model.setProject(['d://rflowpy//validetr//diago','diago0'])
##model.setProject(['d://rflowpy//validetr//carre','carre0'])
#op(model);aqui=model.Aquifere;ecoul=ec(model,aqui)
##reac=model.Reaction
##trac.setParmVal('Sxy',zip([1.,1.],[24.01,37.99])); pour irreg
##trac.setParmVal('Sxy',zip([6.,12.],[16.,10.])); pour diago
# trac.setParmVal('Sxy',zip([4.35,4.88],[7.17,5.59])); pour borden
################### Traceur ##############################
from Traceur import *;from calcTraceur import *
trac = Traceur(model)
if 3>2:
    trac.setParmVal('Sxy',model.Traceur.getParmVal('Sxy'))
    trac.setParmVal('aL',model.Traceur.getParmVal('aL'));
    trac.setParmVal('aT',model.Traceur.getParmVal('aT'));
    trac.setTactuel(trac.getTactuel())
def tr(model,aqui,ecoul):
    opt=0
    [xp,yp,tp,cua,cub,V,Large,Cy]=calcTubes2D(mod,aqui,ecoul,trac,opt)
    [xp1,yp1,tp1,cu1,Fleau] = trac.centrer(xp,yp,tp,cub,V,Large)
    for k in ['xp1','yp1','tp1','cu1','Cy','Large']:
        exec('trac.setTarray(\"'+k+'\",'+k+')')
    tf=trac.getTactuel()
    inj=trac.getParm('inj');Ct=calcTemps(trac,inj,0.,1.,tf); # Ct=calcTemps2(trac,2.,10.,0.,1.) 
    trac.setTarray('Ct',Ct);#trac.setTarray('Flux',Fleau*Ct);
    return trac

#xp1=trac.getTarray('xp1');yp1=trac.getTarray('yp1');Ct=trac.getTarray('Ct');
import matplotlib.pylab as py
#contour(py.array(xp1),py.array(yp1),py.array(Ct),arange(11)/10.)
#axis([0,500,0,100])
####################### graphisme
from matplotlib import rcParams;from matplotlib.pylab import *
rcParams['interactive']=True

#####################" test Sutra ############################
from sutraWriter import *
##path = model.getProject()[0];name=model.getProject()[1]
##suW=SutraWriter(path,name)
##suW.WriteSutraFile(aqui,ecoul,trac,xp,yp,Cy)
##xp = trac.getTarray('xp');[nt,np]=shape(xp)
##[p,c]=suW.ReadRst(nt,np)
###################################################################
################### Dissolution ##############################
##from Dissolution import *;from calcDissolution import *
##def di(model):
##    diss = Dissolution(model);
##    diss.setParm('LNAPL',[('sol',['sable_moyen',['sable_moyen','sable_fin',
##            'sable_grossier','sable_limoneux','limon']]),('Largeur',1.),
##            ('Longueur',1.),('Hauteur',.5)]);
##    diss.setMelange('Essence')
##    diss.doAction('RunP')
##    return diss
##diss=di(model)
######################### Reaction #################################
from Reaction import *; from calcReaction import *
def rr(model):
    re = Reaction(model);
    re.setParC('nom',['Benzene']);re.setParC('Co',ones((1,1))*13.)
    re.setParC('nC',1);re.setParC('mm',[78.]);re.setParC('ne',ones((4,1))*30.)
    re.setParC('k',ones((4,1))*100.);re.setParC('Rf',[1.]);re.setParC('typ',ones((4,1))*2)
    re.setParM('Co',[8.,0.,0.,0.])
    return re
##
#####################################################################
##################### Rt3d ##############################
##from Rt3d import *;from rtphtWriter import *;rt3d = Rt3d(model)
##
##def rt(aqui):
##    bindir = 'd://rflowpy//lib1_2d//bin';cwd = 'd://rflowpy//lib2_1a//tests'
##    rtwrite = Rt3dWriter(cwd,'test0')
##    #zones source dans deux premiers niveaux
##    aqui.addZone('Source','S',10,1,['Source',0,0],zip([2.,2.],[45.05,54.95]))
##    aqui.addZone('Source','S',10,1,['Source',1,1],zip([2.,2.],[45.05,54.95]))
##    #tp= trac.getTparm();
##    lt=[10.,1.,.1,1.,10.];rt3d.setTemps([0.,.5,2.]) # lt :aL,aT,aZ,rf,Co
##    rtwrite.WriteRt3dFile(aqui,lt,rt3d.getParm(),'rt')
##    #rtread=Rt3dReader(cwd,'test0')
##    #c3=rtread.lireUCN(aqui,'rt',4,0)  # pour tstep .5 .. 2
##    #return c3

#################### comparer
