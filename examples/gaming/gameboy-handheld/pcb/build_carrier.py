#!/usr/bin/python3
"""Generate a KiCad carrier from the shared handheld mechanical interface.

Footprints: upstream WeAct Black Pill v3 and stock KiCad 9 libraries.
The stock Waveshare cable connects to J1 in the published VCC/GND/DIN/CLK/CS/DC/RST/BL order.
Run with /usr/bin/python3 (the distribution provides pcbnew).
"""
from pathlib import Path
import json,math,re,hashlib
import pcbnew as p
ROOT=Path(__file__).resolve().parent
spec=json.loads((ROOT.parent/'design-interfaces.json').read_text())
b=p.BOARD()
board_width=spec['pcb']['width'];board_height=spec['pcb']['height']
left=spec['pcb']['center'][0]-board_width/2
top=spec['pcb']['center'][1]+board_height/2
controls={item['id']:item for item in spec['controls']}
mm=p.FromMM
def xy(x,y):return p.VECTOR2I(mm(x),mm(y))
def case_xy(x,y):return x-left,top-y
def line(a,c,layer=p.Edge_Cuts,width=.05):
    s=p.PCB_SHAPE();s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(xy(*a));s.SetEnd(xy(*c));s.SetLayer(layer);s.SetWidth(mm(width));b.Add(s)
def text(s,x,y,size=1,layer=p.F_SilkS):
    t=p.PCB_TEXT(b);t.SetText(s);t.SetPosition(xy(x,y));t.SetTextSize(xy(size,size));t.SetTextThickness(mm(.15));t.SetLayer(layer);b.Add(t)
names=['GND','3V3','PA4','PA5','PA7','PB0','PB1','PA8']+['PB'+str(i) for i in range(3,11)]
nets={}
for name in names:
    net=p.NETINFO_ITEM(b,name);b.Add(net);nets[name]=net

# Concave corner notches clear the case closure posts. Polygon segments sample
# the exact 4.3mm-radius arcs to <=0.01mm chord error; no disconnected islands.
r=4.3
posts={item['id']:case_xy(*item['at'][:2]) for item in spec['caseFasteners']}
# This example routes the current four symmetric corner cutouts.
assert posts['case-tl'][0] == board_width-posts['case-tr'][0]
assert posts['case-tl'][1] == board_height-posts['case-bl'][1]
a=math.degrees(math.acos(posts['case-tl'][0]/r))
c=math.degrees(math.asin(posts['case-tl'][1]/r))
outline=[]
def arc(cx,cy,start,end,n=60):
    for i in range(n+1):
        t=math.radians(start+(end-start)*i/n)
        outline.append((cx+r*math.cos(t),cy+r*math.sin(t)))
arc(*posts['case-tr'],-180+c,-360+a)
arc(*posts['case-br'],-a,-180-c)
arc(*posts['case-bl'],c,-180+a)
arc(*posts['case-tl'],180-a,-c)
for i in range(len(outline)):line(outline[i],outline[(i+1)%len(outline)])

def footprint(lib,name,ref,value,x,y,rot=0,back=False):
    f=p.FootprintLoad(lib,name);assert f,name
    f.SetReference(ref);f.SetValue(value);b.Add(f)
    if back:f.Flip(xy(0,0),False)
    f.SetPosition(xy(x,y));f.SetOrientationDegrees(rot)
    return f
def netpad(f,padnum,name):
    for pad in f.Pads():
        if pad.GetNumber()==str(padnum):pad.SetNet(nets[name])

# Origin is offset by the upstream footprint's body center (x0.12,y3.425).
# Rear-mounted MCU sits beneath the LCD, with a USB-C panel extension to the top.
mcu=footprint(str(ROOT/'vendor'),'WeAct-BlackPill-v3-kicad9','A1','WeAct Black Pill STM32F411CEU6',39.12,25.575,rot=180,back=True)
pinmap={5:'PA8',11:'PB3',12:'PB4',13:'PB5',14:'PB6',15:'PB7',16:'PB8',17:'PB9',19:'GND',28:'PA2',29:'PA3',30:'PA4',31:'PA5',33:'PA7',34:'PB0',35:'PB1',37:'PB10',38:'3V3',39:'GND',44:'GND'}
for num,name in pinmap.items():
    if name in nets:netpad(mcu,num,name)
mcu.Reference().SetVisible(False);mcu.Value().SetVisible(False)
# Keep unconnected module GPIO/SWD pins physically present, with no carrier net.

j=footprint('/usr/share/kicad/footprints/Connector_JST.pretty','JST_PH_B8B-PH-K_1x08_P2.00mm_Vertical','J1','Waveshare LCD PH2.0 cable',56,17)
for i,name in enumerate(['3V3','GND','PA7','PA5','PA4','PB0','PB1','PA8'],1):netpad(j,i,name)
j.Reference().SetVisible(False);j.Value().SetVisible(False)

dpad_x,dpad_y=controls['dpad']['center'][:2]
buttons=[('SW1','UP',dpad_x,dpad_y+8,'PB3'),('SW2','DOWN',dpad_x,dpad_y-8,'PB4'),('SW3','LEFT',dpad_x-8,dpad_y,'PB5'),('SW4','RIGHT',dpad_x+8,dpad_y,'PB6')]
for ref,label,ident,pin in [('SW5','A','btn-a','PB7'),('SW6','B','btn-b','PB8'),('SW7','SELECT','btn-select','PB9'),('SW8','START','btn-start','PB10')]:
    x,y=controls[ident]['center'][:2];buttons.append((ref,label,x,y,pin))
for ref,label,x,y,net in buttons:
    xx,yy=case_xy(x,y)
    f=footprint('/usr/share/kicad/footprints/Button_Switch_THT.pretty','SW_PUSH_6mm',ref,label,xx-3.25,yy-2.25)
    netpad(f,1,net);netpad(f,2,'GND')
    f.Reference().SetVisible(False);f.Value().SetVisible(False)
    text(label,xx,yy+5,.8)

# Local bulk bypass for the removable display cable. Verify the module power
# budget before fabrication; the Black Pill onboard regulator supplies 3V3.
cap=footprint('/usr/share/kicad/footprints/Capacitor_SMD.pretty','C_0805_2012Metric','C1','10uF 6.3V X7R',57,27,rot=90)
netpad(cap,1,'3V3');netpad(cap,2,'GND');cap.Reference().SetVisible(False);cap.Value().SetVisible(False)
cap=footprint('/usr/share/kicad/footprints/Capacitor_SMD.pretty','C_0603_1608Metric','C2','100nF 16V X7R',63,27,rot=90)
netpad(cap,1,'3V3');netpad(cap,2,'GND');cap.Reference().SetVisible(False);cap.Value().SetVisible(False)

for i,m in enumerate(spec['pcb']['mounts'],1):
    x,y=case_xy(*m['at'][:2]);f=p.FOOTPRINT(b);f.SetReference('H'+str(i));f.SetPosition(xy(x,y));b.Add(f)
    pad=p.PAD(f);pad.SetAttribute(p.PAD_ATTRIB_NPTH);pad.SetShape(p.PAD_SHAPE_CIRCLE);pad.SetSize(xy(spec['pcb']['mountHoleDiameter'],spec['pcb']['mountHoleDiameter']));pad.SetDrillSize(xy(spec['pcb']['mountHoleDiameter'],spec['pcb']['mountHoleDiameter']));pad.SetLayerSet(p.LSET.AllCuMask());pad.SetPosition(xy(x,y));f.Add(pad)
    f.Reference().SetVisible(False);f.Value().SetVisible(False)

text('LABWIRED',39,63,2)
text('GAME BOY / WIRE RUNNER',39,67,1)
text('USB POWER - REV A',39,123,1)
text('Engineering prototype',39,127,.8)
# LCD module outline on fabrication/user layer, not a copper or mechanical part.
display_x,display_y=case_xy(*spec['display']['center'][:2])
display_w,display_h=spec['display']['outline']
display_corners=[(display_x-display_w/2,display_y-display_h/2),(display_x+display_w/2,display_y-display_h/2),(display_x+display_w/2,display_y+display_h/2),(display_x-display_w/2,display_y+display_h/2)]
for aa,bb in zip(display_corners,display_corners[1:]+display_corners[:1]):line(aa,bb,p.Dwgs_User,.15)
text('Waveshare 2.4in LCD module above carrier',display_x,display_y,.9,p.Dwgs_User)
b.GetDesignSettings().SetCopperLayerCount(2)
b.GetDesignSettings().SetBoardThickness(mm(spec['pcb']['thickness']))
p.SaveBoard(str(ROOT/'handheld-carrier-unrouted.kicad_pcb'),b)
layout={'schema':'labwired.carrier-layout.v1','units':'mm','pcb_coordinates':{'origin':'top-left','x':'right','y':'down'},'transform_to_case':{'x':f'pcb_x{left:+g}','y':f'{top:g}-pcb_y','z':str(spec['pcb']['center'][2])},'outline':outline,'mounts':spec['pcb']['mounts'],'components':[],'module_pinmap':pinmap,'lcd_connector':{'reference':'J1','pins':['3V3','GND','PA7','PA5','PA4','PB0','PB1','PA8'],'signal_names':['VCC','GND','DIN','CLK','CS','DC','RST','BL']},'sources':{'mcu_footprint':'https://github.com/WeActStudio/WeActStudio.MiniSTM32F4x1/tree/master/Hardware/KiCAD','display_pinout':'https://www.waveshare.com/wiki/2.4inch_LCD_Module'},'status':'placed; routing and DRC pending'}
for f in b.GetFootprints():
    pos=f.GetPosition();layout['components'].append({'ref':f.GetReference(),'value':f.GetValue(),'x':p.ToMM(pos.x),'y':p.ToMM(pos.y),'side':'bottom' if f.IsFlipped() else 'top','pads':[{'number':pad.GetNumber(),'x':p.ToMM(pad.GetPosition().x),'y':p.ToMM(pad.GetPosition().y),'net':pad.GetNetname(),'sx':p.ToMM(pad.GetSize().x),'sy':p.ToMM(pad.GetSize().y),'drill':p.ToMM(pad.GetDrillSize().x),'npth':pad.GetAttribute()==p.PAD_ATTRIB_NPTH,'smd':pad.GetAttribute()==p.PAD_ATTRIB_SMD} for pad in f.Pads()]})
(ROOT/'carrier-layout.json').write_text(json.dumps(layout,indent=2)+'\n')
print(json.dumps({'pcb':str(ROOT/'handheld-carrier-unrouted.kicad_pcb'),'footprints':len(layout['components']),'nets':len(nets),'outline_points':len(outline)}))
