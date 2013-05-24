#if 3>2:
import ctypes as C
import numpy
from scipy import *

if 3>2:
    _lib=numpy.ctypeslib.load_library('ilib/iphtC_dll','.')
    ti=numpy.ctypeslib.ndpointer(dtype = numpy.int_)
    tf=numpy.ctypeslib.ndpointer(dtype = numpy.float_)
    _lib.calcPart.argtypes = [ti,tf,tf,tf,tf,tf,tf,\
                              tf,tf,tf,tf,ti]
    _lib.calcPart.restype = C.c_void_p
    _lib.ptsLigne.argtypes = [ti,tf,tf,tf,tf,\
                              tf,tf,tf,ti]
    _lib.ptsLigne.restype = C.c_void_p
    _lib.interp2d.argtypes = [ti,tf,tf,tf,tf,tf,tf]
    _lib.interp2d.restype = C.c_void_p
##if 3>2:
##    data=[0.,0.,1.1,10.1];dx=[10.]*10;dy=dx*1;
##    vx=ones((10,10))*25.;vy=vx*0.+1e-7
##    clim=ones((10,10));clim[:,-1]=0

def calcPart1(data,dx,dy,vx,vy,clim):
#if 3>2:
    for n in ['data','dx','dy','vx','vy','clim']:
        exec('tmp = numpy.asarray('+n+');'+n+'i = tmp.astype(numpy.float_)')
    ny, nx = vx.shape;it=1;#ndx=len(dx);ndy=len(dy);
    nt=int(max(nx,ny)*1.7);it=array([1]);
    dims = array([nx,ny,nt]);#print data,dims,dx,dy
    tmp = numpy.asarray(dims);dimsi=tmp.astype(numpy.int_);
    tmp = numpy.asarray(it);ito=tmp.astype(numpy.int_);
    for n in ['xp','yp','tp','cu1']:
        exec(n+'o = numpy.empty([nt], dtype=numpy.float_)')
    _lib.calcPart(dimsi,datai,dxi,dyi,vxi,vyi,climi,\
              xpo,ypo,tpo,cu1o,ito)
    return xpo,ypo,tpo,cu1o,ito

def ptsLigne(xp,yp,tp,dt):
#if 3>2:
    dims=array([len(xp)]);dt=array([dt])
    tmp=numpy.asarray(dims);dimsi=tmp.astype(numpy.int_)
    for n in ['xp','yp','tp','dt']:
        exec('tmp = numpy.asarray('+n+');'+n+'i = tmp.astype(numpy.float_)')
    nt=100;it=array([100])
    for n in ['xp','yp','tp']:
        exec(n+'o = numpy.empty([nt], dtype=numpy.float_)')
    tmp = numpy.asarray(it);ito=tmp.astype(numpy.int_);
    _lib.ptsLigne(dimsi,xpi,ypi,tpi,dti,\
              xpo,ypo,tpo,ito)
    return xpo,ypo,tpo,ito

def interp2d(grd1,dx,dy,xp,yp,zp):
    for n in ['dx','dy','xp','yp','zp']:
        exec('tmp = numpy.asarray('+n+');'+n+'i = tmp.astype(numpy.float_)')
    mat=zeros((len(dx),len(dy)))
    tmp = numpy.asarray(zp);dimsi=tmp.astype(numpy.int_);
    _lib.interp2d(dimsi,datai,dxi,dyi,xpi,ypi,zpi,zpo)
    return zpo
