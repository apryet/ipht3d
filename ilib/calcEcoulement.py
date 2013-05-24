from scipy import floor,ceil,ravel,take,clip,arange,sqrt
    
def calcProfilV(self,xy):
    """renvoie les valeurs des vitesses sur une section"""
    vxvy = self.getMfVitesse()
    grd  = self.parent.aquifere.getFullGrid()
    x0,y0,dx,dy,nx,ny = grd['x0'],grd['y0'],grd['dx'],grd['dy'],grd['nx'],grd['ny']
    x,y = zip(*xy)
    xl0, xl1 = x[:2]
    yl0, yl1 = y[:2]
    dd = min(dx,dy)*.95;dxp, dyp = xl1-xl0, yl1-yl0
    ld = max(ceil(abs(dxp/dx)),ceil(abs(dyp/dy)))
    ld = int(ld+1); ddx = dxp/ld; ddy = dyp/ld
    xp2 = xl0+arange(ld+1)*ddx
    yp2 = yl0+arange(ld+1)*ddy
    ix = floor((xp2-x0)/dx);ix=clip(ix.astype(int),0,nx-1)
    iy = floor((yp2-y0)/dy);iy=clip(iy.astype(int),0,ny-1)
    vx = take(ravel(vxvy[0]),iy*nx+ix)
    vy = take(ravel(vxvy[1]),iy*nx+ix)
    V = sqrt(vx**2+vy**2)
    cu = sqrt((xp2-xp2[0])**2+(yp2-yp2[0])**2)
    return [cu,V]
    
        
