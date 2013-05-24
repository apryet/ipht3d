""" Batch to run several times a pht3d model with varying something in the
input file
to run it just complete the directories below, uncomment the senetences you want
to use in the batch and press F5"""

from iPht3dModel import *;import os

""" first fill the directory where the original model is"""
fdir='d://ipht3d//ex//fernando//fernando1'
fname='fernando1'  # the name of the file
"""and the place where the ipht3D lies"""
ipdir='d://ipht3d//lib1_j'

######################## several useful function #################
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

def changeZone(model,variable,zname,zcoord,zval):
    z=model.Aquifere.getZoneByName(variable,zname)
    z.setXy(zcoord);z.setVal(zval)

    
########################## the batch itself #################""""""""
model = iPht3dModel(None,ipdir);
model.setProject([fdir,fname])  # set the directories and name file
op(model);  # open the models (with above function

"""here we want to move a Pht3d zone to a new place, and rewrite the whole
in a new directory"""
zcoord=[(.51,6.49),(1.49,6.49),(1.49,6.01),(.51,6.01),(.51,6.49)]
zval=-2000
changeZone(model,'PHT3D'

