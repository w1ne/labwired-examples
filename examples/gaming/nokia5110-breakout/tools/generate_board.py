#!/usr/bin/env python3
import pcbnew as k,json,math,uuid,pathlib,xml.etree.ElementTree as E
root=pathlib.Path(__file__).resolve().parents[1]
el=root/'electronics'
meta=json.loads((el/'authoring-metadata.json').read_text())
b=k.BOARD();b.SetCopperLayerCount(2)
d=b.GetDesignSettings();d.SetBoardThickness(k.FromMM(1.6));d.m_MinClearance=k.FromMM(.2);d.m_TrackMinWidth=k.FromMM(.25);d.m_ViasMinSize=k.FromMM(.6);d.m_ViasMinAnnularWidth=k.FromMM(.15);d.m_CopperEdgeClearance=k.FromMM(.5);d.m_HoleClearance=k.FromMM(.25)
def pt(p):return k.VECTOR2I(k.FromMM(p[0]),k.FromMM(p[1]))
def mm(p):return (round(p.x/1e6,6),round(p.y/1e6,6))
netmap={};padnet={}
for n in E.parse(root/'manufacturing/nokia-carrier.net.xml').getroot().findall('./nets/net'):
 name=n.get('name');net=k.NETINFO_ITEM(b,name,int(n.get('code')));b.Add(net);netmap[name]=net
 for node in n.findall('node'):padnet[(node.get('ref'),node.get('pin'))]=net
placements={'J1':(69.13,32.616,0),'J2':(20.87,18.9,180),'J3':(69.13,54.46,0),'J4':(45,16,0),'J5':(45,47,0),'R1':(56,54,0),'R2':(61,54,0),'C1':(38,21.08,180),'C2':(38,47,180),'C3':(38,43,180),'TP1':(11,42,0),'TP2':(32,17,0),'TP3':(25,50,0),'TP4':(51,59.7,0),'TP5':(65,59.7,0),'H1':(5,5,0),'H2':(85,5,0),'H3':(5,61,0),'H4':(85,61,0),'H5':(36.745,6.2,0),'H6':(53.255,6.2,0)}
fps={};pads={}
for c in meta['components']:
 ref=c['ref'];lib=c.get('footprint',c['lib'])
 f=k.FootprintLoad(str(el/'nokia-carrier.pretty'),lib)
 assert f,lib
 f.SetReference(ref);f.SetValue(c['value']);f.SetFPIDAsString('nokia-carrier:'+lib)
 path=k.KIID_PATH();path.push_back(k.KIID(meta['schematic_uuid']));path.push_back(k.KIID(c['uuid']));f.SetPath(path)
 b.Add(f);x,y,a=placements[ref];f.SetPosition(pt((x,y)))
 if ref in ['J1','J2','J3']:f.Flip(pt((x,y)),False)
 f.SetOrientationDegrees(a)
 if ref.startswith(('H','TP')):f.SetExcludedFromBOM(True)
 for key in ['mpn','manufacturer']:
  if key in c:
   n='MPN' if key=='mpn' else 'Manufacturer';f.SetField(n,c[key]);f.GetField(n).SetVisible(False);f.GetField(n).SetPosition(pt((x,y)))
 f.Value().SetVisible(False);f.Reference().SetTextSize(pt((.8,.8)));f.Reference().SetTextThickness(k.FromMM(.12));f.Reference().SetTextAngle(k.EDA_ANGLE(0,k.DEGREES_T))
 f.Reference().SetPosition(pt((x+4,y)))
 if ref.startswith('H'):f.Reference().SetVisible(False)
 if ref in ['C1','C2','C3','R1','R2']:f.Reference().SetPosition(pt((x,y-1.7)))
 if ref.startswith('TP'):f.Reference().SetVisible(False)
 for p in f.Pads():
  if(ref,p.GetNumber())in padnet:p.SetNet(padnet[(ref,p.GetNumber())])
  pads[(ref,p.GetNumber())]=mm(p.GetPosition())
 fps[ref]=f
# Exact ST MB1136C Arduino header registration in the finished 70 x 82.5 mm board frame.
for ref,count,dy in [('J1',10,-2.54),('J2',8,2.54),('J3',8,-2.54),('J4',8,2.54),('J5',4,2.54)]:
 x,y,_=placements[ref]
 for n in range(1,count+1):
  assert pads[ref,str(n)]==(x,round(y+(n-1)*dy,6)),(ref,n,pads[ref,str(n)])
def net(name):return netmap.get('/'+name,netmap.get(name))
def seg(a,z,name,layer='F.Cu',w=.3):
 if a==z:return
 t=k.PCB_TRACK(b);t.SetStart(pt(a));t.SetEnd(pt(z));t.SetWidth(k.FromMM(w));t.SetLayer(b.GetLayerID(layer));t.SetNet(net(name));b.Add(t)
def route(points,name,layer='F.Cu',w=.3):
 for a,z in zip(points,points[1:]):seg(a,z,name,layer,w)
def via(p,name):
 v=k.PCB_VIA(b);v.SetPosition(pt(p));v.SetWidth(k.FromMM(.6));v.SetDrill(k.FromMM(.3));v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNet(net(name));b.Add(v)
# 1 MHz LCD SPI and control. DC uses the rear layer to cross CE without an electrical crossover.
route([pads['J1','6'],(60,19.916),(56.296,23.62),pads['J4','4']],'LCD_CLK_PA5')
route([pads['J1','4'],(60,24.996),(58.836,26.16),pads['J4','5']],'LCD_DIN_PA7')
route([pads['J1','3'],(62,27.536),(58.296,31.24),pads['J4','7']],'LCD_CE_PB6')
route([pads['J1','2'],(60,30.076),(58.624,28.70),pads['J4','6']],'LCD_DC_PC7','B.Cu')
route([pads['J1','1'],(64,32.616),(62.836,33.78),pads['J4','8']],'LCD_RST_PA9')
# LCD supply branches around the capacitor's grounded pad.
route([pads['J2','4'],(28,26.52),(32.44,22.08),(40.5,22.08),(41.5,21.08),pads['J4','3']],'+3V3',w=.5)
route([pads['C1','1'],(41.5,21.08)],'+3V3',w=.5)
route([(41.5,21.08),(41.5,18.5),(40,17),pads['TP2','1']],'+3V3')
# 5 V sensor supply has local 100 nF plus 10 uF bypass.
route([pads['J2','5'],(25,29.06),(30,34.06),(30,46),(32,48),(40.5,48),(41.5,47),pads['J5','1']],'+5V',w=.5)
route([pads['C2','1'],(41.5,47)],'+5V',w=.5)
route([pads['C3','1'],(41.5,43),(41.5,47)],'+5V',w=.5)
route([(30,46),(30,48),(28,50),pads['TP3','1']],'+5V')
route([pads['J3','8'],(60,36.68),(52,44.68),(52,49.54),pads['J5','2']],'TRIG_PA8')
route([pads['J5','3'],(49.92,52.08),(51.84,54),pads['R1','1']],'ECHO_5V')
route([pads['R1','2'],pads['R2','1']],'ECHO_3V3_PB10')
route([pads['J3','7'],(64,39.22),(59,44.22),(59,54)],'ECHO_3V3_PB10')
route([(51.84,54),(51.84,58.86),pads['TP4','1']],'ECHO_5V')
route([(59,54),(59,56.5),(62.2,59.7),pads['TP5','1']],'ECHO_3V3_PB10')
# Ground copper is explicitly connected before adding the return plane.
route([(15,14),(15,58),(76,58),(76,17.376),pads['J1','7']],'GND','B.Cu',.5)
for n in ['6','7']:route([pads['J2',n],(15,pads['J2',n][1])],'GND','B.Cu',.5)
route([(15,14),(35,14),(35,21.08)],'GND','B.Cu',.5)
for n in ['1','2']:route([pads['J4',n],(35,pads['J4',n][1])],'GND','B.Cu',.5)
route([pads['J5','4'],(45,58)],'GND','B.Cu',.5)
route([pads['R2','2'],(63,54)],'GND',w=.5);via((63,54),'GND');route([(63,54),(63,58)],'GND','B.Cu',.5)
for ref in ['C1','C2','C3']:
 x,y=pads[ref,'2'];route([(x,y),(35,y)],'GND',w=.5);via((35,y),'GND')
route([(35,43),(35,58)],'GND','B.Cu',.5)
route([pads['TP1','1'],(13,42)],'GND');via((13,42),'GND');route([(13,42),(15,42)],'GND','B.Cu',.5)
def line(a,z,layer=k.Edge_Cuts,width=.05):
 s=k.PCB_SHAPE();s.SetShape(k.SHAPE_T_SEGMENT);s.SetStart(pt(a));s.SetEnd(pt(z));s.SetLayer(layer);s.SetWidth(k.FromMM(width));b.Add(s)
def arc(a,m,z):
 s=k.PCB_SHAPE();s.SetShape(k.SHAPE_T_ARC);s.SetArcGeometry(pt(a),pt(m),pt(z));s.SetLayer(k.Edge_Cuts);s.SetWidth(k.FromMM(.05));b.Add(s)
line((2,0),(88,0));arc((88,0),(89.414214,.585786),(90,2));line((90,2),(90,64));arc((90,64),(89.414214,65.414214),(88,66));line((88,66),(2,66));arc((2,66),(.585786,65.414214),(0,64));line((0,64),(0,2));arc((0,2),(.585786,.585786),(2,0))
def text(s,p,size=1,layer=k.F_SilkS):
 t=k.PCB_TEXT(b);t.SetText(s);t.SetPosition(pt(p));t.SetTextSize(pt((size,size)));t.SetTextThickness(k.FromMM(.15 if size>=1 else .12));t.SetLayer(layer);b.Add(t)
text('LABWIRED BREAKOUT',(48,63.5),1.25);text('NUCLEO-L476RG  /  REV A',(48,65.1),.85)
text('LCD REV2 3V3',(48,13),.85);text('HC-SR04 5V',(44,40),.85)
text('USB / ST-LINK ^',(15,3),.8)
text('USER',(28.5,6.2),.8);text('RESET',(62,6.2),.8)
for label,p in [('GND',(11,39.5)),('3V3',(32,14.5)),('5V',(25,52.5)),('ECHO 5V',(51,57)),('ECHO 3V3',(65,57))]:text(label,p,.8)
# Physical Nucleo perimeter and hardware-access holes remain distinct from carrier fabrication.
for a,z in [((10,-23),(80,-23)),((80,-23),(80,59.5)),((80,59.5),(10,59.5)),((10,59.5),(10,-23))]:line(a,z,k.Dwgs_User,.1)
text('Purchased NUCLEO-L476RG below carrier',(45,-15),1,k.Dwgs_User)
for ref,r in [('H1',3.5),('H2',3.5),('H3',3.5),('H4',3.5),('H5',5.6),('H6',5.6)]:
 x,y,_=placements[ref];z=k.ZONE(b);z.SetIsRuleArea(True);z.SetZoneName(ref+'-hardware-clearance');z.SetLayerSet(k.LSET.AllCuMask(2));z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowPads(False);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowFootprints(False);o=z.Outline();o.NewOutline()
 for j in range(64):
  a=2*math.pi*j/64;o.Append(pt((x+r*math.cos(a),y+r*math.sin(a))))
 b.Add(z)
z=k.ZONE(b);z.SetLayer(k.B_Cu);z.SetNet(net('GND'));z.SetLocalClearance(k.FromMM(.25));z.SetThermalReliefGap(k.FromMM(.3));z.SetThermalReliefSpokeWidth(k.FromMM(.3));z.SetPadConnection(k.ZONE_CONNECTION_THERMAL);z.SetMinThickness(k.FromMM(.2));o=z.Outline();o.NewOutline()
for p in [(1,1),(89,1),(89,65),(1,65)]:o.Append(pt(p))
b.Add(z);b.BuildConnectivity();k.ZONE_FILLER(b).Fill(b.Zones());k.SaveBoard(str(el/'nokia-carrier.kicad_pcb'),b)
out={'kicad_version':k.Version(),'dimensions_mm':[90,66,1.6],'footprints':len(list(b.GetFootprints())),'nets':len(netmap),'track_items':len(list(b.GetTracks())),'pad_coordinates':{ref:{p.GetNumber():mm(p.GetPosition())for p in f.Pads()}for ref,f in fps.items()},'nucleo_alignment':{'carrier_to_nucleo_xy_mm':[-10,23],'nucleo_finished_outline_mm':[70,82.5],'source':'ST MB1136C native PcbDoc / Mechanical 1'}}
(root/'manufacturing/board-authoring-summary.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k]for k in ['dimensions_mm','footprints','nets','track_items']}))
