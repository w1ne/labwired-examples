#!/usr/bin/python3
"""Create the routed-carrier input from the exported native schematic netlist.

This script preserves symbol UUIDs and derives every pad net from KiCad's XML.
Route the native input through labwired_pcb_route_imported, then finish_routing.py.
KiCad ERC/DRC and schematic parity are the acceptance checks.
"""
import pcbnew as k
import json,math,uuid,pathlib,xml.etree.ElementTree as E
root=pathlib.Path(__file__).resolve().parents[1];el=root/'electronics'
meta=json.loads((el/'authoring-metadata.json').read_text());b=k.BOARD();b.SetCopperLayerCount(2)
d=b.GetDesignSettings();d.SetBoardThickness(k.FromMM(1.6));d.m_MinClearance=k.FromMM(.2);d.m_TrackMinWidth=k.FromMM(.25);d.m_ViasMinSize=k.FromMM(.6);d.m_ViasMinAnnularWidth=k.FromMM(.15);d.m_CopperEdgeClearance=k.FromMM(.5);d.m_HoleClearance=k.FromMM(.25)
def pt(p):return k.VECTOR2I(int(round(p[0]*1e6)),int(round(p[1]*1e6)))
def mm(p):return(round(p.x/1e6,6),round(p.y/1e6,6))
netmap={};padnet={};xml=E.parse(root/'manufacturing/doom-carrier.net.xml').getroot()
for n in xml.findall('./nets/net'):
 name=n.get('name');net=k.NETINFO_ITEM(b,name,int(n.get('code')));b.Add(net);netmap[name]=net
 for node in n.findall('node'):padnet[(node.get('ref'),node.get('pin'))]=net
placements={'J1':(25.4,38.66,0),'J2':(48.26,38.66,0),'J3':(19.68,12,90),'C1':(65,28,0),'C2':(65,32,0),'R22':(67,40,0),'R23':(67,44,0),'R24':(67,48,0),'R25':(67,52,0),'TP1':(68,66,0),'TP2':(68,72,0),'TP3':(68,78,0),'TP4':(68,84,0),'H1':(4,4,0),'H2':(76,4,0),'H3':(4,96,0),'H4':(76,96,0)}
by_ref={c['ref']:c for c in meta['components']}
for i in range(1,22):
 c=by_ref['R'+str(i)];net=c['net']['1']
 ref,pin=next((a['ref'],p) for a in meta['components'] if a['ref'] in ['J1','J2'] for p,v in a['net'].items() if v==net)
 x,y,_=placements[ref];placements[c['ref']]=(x-5.08 if ref=='J1' else x+5.08,y+(int(pin)-1)*2.54,180 if ref=='J1' else 0)
fps={};pads={}
for c in meta['components']:
 ref=c['ref']
 if ref.startswith('#'):continue
 f=k.FootprintLoad(str(el/'doom-carrier.pretty'),c['lib']);f.SetReference(ref);f.SetValue(c['value']);f.SetFPIDAsString('doom-carrier:'+c['lib'])
 path=k.KIID_PATH();path.push_back(k.KIID(meta['schematic_uuid']));path.push_back(k.KIID(c['uuid']));f.SetPath(path)
 x,y,a=placements[ref];f.SetPosition(pt((x,y)));f.SetOrientationDegrees(a)
 if ref.startswith(('H','TP')):f.SetExcludedFromBOM(True)
 for key in ['mpn','manufacturer']:
  if key in c:
   n='MPN'if key=='mpn'else'Manufacturer';f.SetField(n,c[key]);f.GetField(n).SetVisible(False);f.GetField(n).SetPosition(pt((x,y)))
 f.Value().SetVisible(False);f.Reference().SetTextSize(pt((1.0,1.0)));f.Reference().SetTextThickness(k.FromMM(.12));f.Reference().SetTextAngle(k.EDA_ANGLE(0,k.DEGREES_T))
 if ref in ['J1','J2']:f.Reference().SetPosition(pt((x,y-2.8)))
 elif ref=='J3':f.Reference().SetPosition(pt((40,6)))
 elif ref.startswith('R') and int(ref[1:])<=21:f.Reference().SetPosition(pt((x-3.2 if x<25.4 else x+3.2,y)))
 elif ref.startswith(('R','C')):f.Reference().SetPosition(pt((x,y-1.8)))
 elif ref.startswith('TP'):f.Reference().SetPosition(pt((x,y-1.8)))
 else:f.Reference().SetVisible(False)
 for p in f.Pads():
  if(ref,p.GetNumber())in padnet:p.SetNet(padnet[(ref,p.GetNumber())])
  pads[(ref,p.GetNumber())]=mm(p.GetPosition())
 b.Add(f);fps[ref]=f

def track(a,z,net,layer=k.F_Cu,width=.25):
 t=k.PCB_TRACK(b);t.SetStart(pt(a));t.SetEnd(pt(z));t.SetWidth(k.FromMM(width));t.SetLayer(layer);t.SetNet(netmap['/'+net]);b.Add(t)
for i in range(1,22):
 c=by_ref['R'+str(i)];net=c['net']['1'];ref,pin=next((a['ref'],p)for a in meta['components']if a['ref']in ['J1','J2']for p,v in a['net'].items()if v==net)
 track(pads[ref,pin],pads[c['ref'],'1'],net)
track(pads['J1','1'],pads['J1','2'],'3V3',width=.6)
# Seed bottom-layer escapes for the three dense center data-bus pins. The
# native router keeps these source-side connections and finishes the bus.
for ref in ['R10','R11','R12']:
 net=by_ref[ref]['net']['2'];x,y=pads[ref,'2'];escape=(16.9,y)
 track((x,y),escape,net)
 via=k.PCB_VIA(b);via.SetPosition(pt(escape));via.SetWidth(k.FromMM(.8));via.SetDrill(k.FromMM(.4));via.SetViaType(k.VIATYPE_THROUGH);via.SetLayerPair(k.F_Cu,k.B_Cu);via.SetNet(netmap['/'+net]);b.Add(via)

def line(a,z,layer=k.Edge_Cuts,width=.05):
 s=k.PCB_SHAPE();s.SetShape(k.SHAPE_T_SEGMENT);s.SetStart(pt(a));s.SetEnd(pt(z));s.SetLayer(layer);s.SetWidth(k.FromMM(width));b.Add(s)
def arc(a,m,z):
 s=k.PCB_SHAPE();s.SetShape(k.SHAPE_T_ARC);s.SetArcGeometry(pt(a),pt(m),pt(z));s.SetLayer(k.Edge_Cuts);s.SetWidth(k.FromMM(.05));b.Add(s)
line((2,0),(78,0));arc((78,0),(79.414214,.585786),(80,2));line((80,2),(80,98));arc((80,98),(79.414214,99.414214),(78,100));line((78,100),(2,100));arc((2,100),(.585786,99.414214),(0,98));line((0,98),(0,2));arc((0,2),(.585786,.585786),(2,0))
def text(s,p,size=1,layer=k.F_SilkS):
 size=max(1.0,size)
 t=k.PCB_TEXT(b);t.SetText(s);t.SetPosition(pt(p));t.SetTextSize(pt((size,size)));t.SetTextThickness(k.FromMM(.15 if size>=1 else .12));t.SetLayer(layer);b.Add(t)
text('LABWIRED DOOM I80 A',(40,21),1.2);text('MRB3205  3V3 ONLY',(40,17),.9);text('PIN 1',(15,12),.8)
text('DEVKITC-1 N16R8 V1.0',(36.83,60),.8);text('USB UART v',(36.83,65),1);text('R16=0R / R8=OPEN',(40,25),.8);text('DISPLAY J1=CLOSED',(40,28),.8)
for i,label in enumerate(['3V3','GND','WR','CS'],1):x,y,_=placements['TP'+str(i)];text(label,(x+5,y),.8)
for a,z in [((24.13,37.26),(49.53,37.26)),((49.53,37.26),(49.53,100)),((49.53,100),(24.13,100)),((24.13,100),(24.13,37.26))]:line(a,z,k.Dwgs_User,.1)
text('DevKitC-1 Rev1.0 envelope',(36.83,70),.8,k.Dwgs_User)
for i,(x,y)in enumerate([(4,4),(76,4),(4,96),(76,96)],1):
 z=k.ZONE(b);z.SetIsRuleArea(True);z.SetZoneName('mount-keepout-'+str(i));z.SetLayerSet(k.LSET.AllCuMask(2));z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowPads(False);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowFootprints(False)
 o=z.Outline();o.NewOutline()
 for j in range(48):a=2*math.pi*j/48;o.Append(int(k.FromMM(x+3.5*math.cos(a))),int(k.FromMM(y+3.5*math.sin(a))))
 b.Add(z)
# Manufacturer Rev1.0 drawing: last header pin is 8 mm from the USB edge;
# first pin is 62.74 - 8 - 21*2.54 = 1.4 mm from the antenna-end PCB edge.
# The module antenna overhangs the antenna-end PCB edge. Retain a copper-free
# region underneath and around it; this example does not enable a radio.
# This is a copper exclusion: socket plastic/courtyards may cross its edge,
# while pads, tracks, vias and copper fills remain forbidden on both layers.
rf=[(21.13,27.76),(52.53,27.76),(52.53,37.1),(21.13,37.1)]
z=k.ZONE(b);z.SetIsRuleArea(True);z.SetZoneName('DevKit antenna copper keepout');z.SetLayerSet(k.LSET.AllCuMask(2));z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowPads(True);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowFootprints(False);o=z.Outline();o.NewOutline()
for p in rf:o.Append(pt(p))
b.Add(z)
b.BuildConnectivity();k.SaveBoard(str(el/'doom-carrier-unrouted.kicad_pcb'),b)
(root/'manufacturing/board-authoring-summary.json').write_text(json.dumps({'kicad_version':k.Version(),'board_mm':[80,100,1.6],'footprints':len(fps),'nets_including_isolated_nc':len(netmap),'preconnected_tracks':len(list(b.GetTracks())),'placements':placements,'pad_coordinates':{ref:{p.GetNumber():mm(p.GetPosition())for p in f.Pads()}for ref,f in fps.items()},'rf_keepout':rf},indent=2)+'\n')
print('Created',len(fps),'footprints;',len(netmap),'nets')
