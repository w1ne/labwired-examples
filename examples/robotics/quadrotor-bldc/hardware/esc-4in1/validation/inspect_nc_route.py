import pcbnew as k, math, collections
D='/work'
b=k.LoadBoard(D+'/4in1-candidate.kicad_pcb')
missing={'U2':['8','23','24'],'U5':['8','23','24'],'U7':['8','23','24'],'U9':['23','24'],'U6':['5','7'],'U10':['5','7','8']}
f={x.GetReference():x for x in b.GetFootprints()}
def mm(x):return round(k.ToMM(x),4)
def xy(v):return (mm(v.x),mm(v.y))
def dist_point_seg(p,a,z):
 x,y=p;s,t=a;u,v=z; dx=u-s;dy=v-t
 w=max(0,min(1,((x-s)*dx+(y-t)*dy)/(dx*dx+dy*dy))) if dx or dy else 0
 return math.dist((x,y),(s+w*dx,t+w*dy))
for ref,nums in missing.items():
 for pin in nums:
  fp=f[ref];pad=fp.FindPadByNumber(pin); pos=xy(pad.GetPosition());print('\nPAD',ref,pin,'location',pos, 'WH',xy(pad.GetSize()),'net',pad.GetNetname())
  tracks=[]
  for t in b.GetTracks():
   a=xy(t.GetStart());z=xy(t.GetEnd())
   dis=dist_point_seg(pos,a,z)
   if dis<1.1:
    tracks.append((dis,t.GetNetname(),t.GetLayerName(),type(t).__name__,xy(t.GetWidth()) if hasattr(t.GetWidth(),'x') else mm(t.GetWidth()),a,z))
  for t in sorted(tracks,key=lambda x:x[0])[:28]:print('  track',*(f'{w:.3f}' if isinstance(w,float) else w for w in t))
