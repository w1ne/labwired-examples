from pathlib import Path
import uuid,json,re,shutil
root=Path(__file__).resolve().parents[1]
el=root/'electronics'; el.mkdir(parents=True,exist_ok=True)
libdir=el/'doom-carrier.pretty';libdir.mkdir(exist_ok=True)
def uid(k):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://labwired.com/esp32s3-doom/carrier/rev-a/'+k))
def block(s,start):
 dep=0;ins=False;esc=False
 for i in range(start,len(s)):
  c=s[i]
  if esc:esc=False;continue
  if c=='\\' and ins:esc=True;continue
  if c=='"':ins=not ins
  if not ins:
   if c=='(':dep+=1
   elif c==')':
    dep-=1
    if dep==0:return s[start:i+1]
 raise ValueError('unclosed')
def children(s,key):
 out=[];pos=0
 while True:
  i=s.find('('+key+' ',pos)
  if i<0:return out
  q=block(s,i);out.append(q);pos=i+len(q)
def read_symbol(lib,name):
 s=Path('/usr/share/kicad/symbols/'+lib+'.kicad_sym').read_text();i=s.index('(symbol "'+name+'"');return block(s,i)
libspec={'Socket22':('Connector_Generic','Conn_01x22'),'Display34':('Connector_Generic','Conn_02x17_Odd_Even'),'R':('Device','R'),'C':('Device','C'),'TestPoint':('Connector','TestPoint'),'MountingHole':('Mechanical','MountingHole'),'PWR_FLAG':('power','PWR_FLAG')}
syms={}
for local,(lib,name)in libspec.items():
 s=read_symbol(lib,name)
 s=s.replace('(symbol "'+name+'"','(symbol "'+local+'"',1).replace('(symbol "'+name+'_','(symbol "'+local+'_')
 syms[local]=s
pins={}
for name,s in syms.items():
 pins[name]={}
 for q in children(s,'pin'):
  n=re.search(r'\(number "([^"]+)"',q);a=re.search(r'\(at ([\d.-]+) ([\d.-]+) ([\d.-]+)\)',q)
  if n and a:pins[name][n[1]]=tuple(float(x)for x in a.groups())
print('Symbol pins',pins)
# Local copies keep the project usable without a global library setup.
fp_spec={
 'Socket22':('Connector_PinSocket_2.54mm','PinSocket_1x22_P2.54mm_Vertical'),
 'Display34':('Connector_PinHeader_2.54mm','PinHeader_2x17_P2.54mm_Vertical'),
 'R':('Resistor_SMD','R_0603_1608Metric'),
 'C':('Capacitor_SMD','C_0805_2012Metric'),
 'TestPoint':('TestPoint','TestPoint_Pad_D1.5mm'),
 'MountingHole':('MountingHole','MountingHole_2.7mm_M2.5')}

for local,(lib,name)in fp_spec.items():
 p=Path('/usr/share/kicad/footprints')/(lib+'.pretty')/(name+'.kicad_mod');s=p.read_text().replace('(footprint "'+name+'"','(footprint "'+local+'"',1)
 if local=='MountingHole':
  s=s.replace('(drill 2.7)','(drill 2.9)').replace('2.7mm','2.9mm').replace('(end 2.45 0)','(end 3.5 0)')

 if not (libdir/(local+'.kicad_mod')).exists():(libdir/(local+'.kicad_mod')).write_text(s)
(el/'doom-carrier.kicad_sym').write_text('(kicad_symbol_lib (version 20251024) (generator "kicad_symbol_editor")\n'+'\n'.join(syms.values())+'\n)\n')
(el/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "doom-carrier") (type "KiCad") (uri "${KIPRJMOD}/doom-carrier.kicad_sym") (options "") (descr "Project-local KiCad standard symbols")))\n')
(el/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "doom-carrier") (type "KiCad") (uri "${KIPRJMOD}/doom-carrier.pretty") (options "") (descr "Project-local carrier footprints")))\n')
# GPIO mapping is from Espressif Rev1.0 drawing, not a generic ESP32 footprint.
j1={'1':'3V3','2':'3V3','4':'MCU_D3','5':'MCU_D4','6':'MCU_D5','7':'MCU_D6','8':'MCU_D14','9':'MCU_D15','10':'MCU_WR','11':'MCU_DC','12':'MCU_D7','13':'MCU_D2','15':'MCU_D8','16':'MCU_D9','17':'MCU_D10','18':'MCU_D11','19':'MCU_D12','20':'MCU_D13','22':'GND'}
j2={'1':'GND','4':'MCU_D0','5':'MCU_D1','9':'MCU_BL','10':'MCU_RST','18':'MCU_CS','21':'GND','22':'GND'}
display={'1':'LCD_CS','2':'LCD_DC','3':'LCD_WR','4':'LCD_RD','5':'LCD_RST','22':'LCD_SD_CS','23':'LCD_BL','24':'3V3','25':'3V3','26':'GND','27':'GND','32':'LCD_FLASH_CS','33':'LCD_TOUCH_CS',**{str(i+6):'LCD_D'+str(i) for i in range(16)}}
components=[
 {'ref':'J1','lib':'Socket22','value':'SSW-122-01-G-S','at':(58.42,83.82),'net':j1,'mpn':'SSW-122-01-G-S','manufacturer':'Samtec'},
 {'ref':'J2','lib':'Socket22','value':'SSW-122-01-G-S','at':(124.46,83.82),'net':j2,'mpn':'SSW-122-01-G-S','manufacturer':'Samtec'},
 {'ref':'J3','lib':'Display34','value':'TSW-117-07-G-D','at':(279.4,81.28),'net':display,'mpn':'TSW-117-07-G-D','manufacturer':'Samtec'},
]
signals=[*['D'+str(i) for i in range(16)],'WR','DC','CS','RST','BL']
for i,net in enumerate(signals):
 components.append({'ref':'R'+str(i+1),'lib':'R','value':'33R 1%','at':(172.72+30.48*(i%3),45.72+22.86*(i//3)),'net':{'1':'MCU_'+net,'2':'LCD_'+net},'mpn':'RC0603FR-0733RL','manufacturer':'Yageo'})
for i,net in enumerate(['RD','SD_CS','FLASH_CS','TOUCH_CS'],22):
 components.append({'ref':'R'+str(i),'lib':'R','value':'10k 1%','at':(269.24+25.4*(i-22),142.24),'net':{'1':'3V3','2':'LCD_'+net},'mpn':'RC0603FR-0710KL','manufacturer':'Yageo'})
for i,(value,mpn,x) in enumerate([('10u 10V X7R','C2012X7R1A106K125AC',96.52),('100n 50V X8R','C2012X8R1H104K125AA',127.0)],1):
 components.append({'ref':'C'+str(i),'lib':'C','value':value,'at':(x,165.1),'net':{'1':'3V3','2':'GND'},'mpn':mpn,'manufacturer':'TDK'})
for i,net in enumerate(['3V3','GND','LCD_WR','LCD_CS'],1):components.append({'ref':'TP'+str(i),'lib':'TestPoint','value':net,'at':(172.72+30.48*(i-1),215.9),'net':{'1':net}})
for i in range(1,5):components.append({'ref':'H'+str(i),'lib':'MountingHole','value':'M2.5 / 2.9 mm NPTH','at':(48.26+30.48*(i-1),210.82),'net':{}})
for i,net in enumerate(['3V3','GND'],1):components.append({'ref':'#FLG0'+str(i),'lib':'PWR_FLAG','value':'PWR_FLAG','at':(48.26+25.4*(i-1),165.1),'net':{'1':net}})
sch_id=uid('schematic');pieces=[]
def effects(size=1.27,just=''):
 return '(effects (font (size '+str(size)+' '+str(size)+'))'+(' (justify '+just+')' if just else '')+')'
def prop(k,v,x,y,hidden=False):
 return '(property '+json.dumps(k)+' '+json.dumps(v)+' (at '+f'{x:g} {y:g} 0'+') '+('(hide yes) 'if hidden else '')+effects()+')'
def label(name,x,y):
 return '(label '+json.dumps(name)+' (at '+f'{x:g} {y:g} 0'+') '+effects(1.27,'left bottom')+' (uuid "'+uid('label/'+name+'/'+str(x)+'/'+str(y))+'"))'
for c in components:
 ref=c['ref'];name=c['lib'];x,y=c['at'];sid=uid('symbol/'+ref);c['uuid']=sid
 p=['(symbol (lib_id "doom-carrier:'+name+'") (at '+f'{x:g} {y:g} 0'+') (unit 1) (in_bom '+('no'if ref.startswith(('#','TP','H'))else'yes')+') (on_board '+('no'if ref.startswith('#')else'yes')+') (dnp no) (uuid "'+sid+'")']
 p += [prop('Reference',ref,x+3.81,y-30.48 if name=='Socket22' else y-7.62 if name=='Display34' else y-5.08,ref.startswith('#')),prop('Value',c['value'],x+3.81,y+30.48 if name=='Socket22'else y+7.62 if name=='Display34'else y+5.08,name in ['PWR_FLAG','TestPoint'])]
 if name in fp_spec:p.append(prop('Footprint','doom-carrier:'+name,x,y,True))
 for key in ['mpn','manufacturer']:
  if key in c:p.append(prop('MPN'if key=='mpn'else'Manufacturer',c[key],x,y,True))
 for pin in pins[name]:p.append('(pin "'+pin+'" (uuid "'+uid('pin/'+ref+'/'+pin)+'"))')
 p.append('(instances (project "doom-carrier" (path "/'+sch_id+'" (reference "'+ref+'") (unit 1))))')
 pieces.append('\n'.join(p)+')')
 for pin,(px,py,angle)in pins[name].items():
  xx=x+px;yy=y-py
  if pin in c['net']:
   # Wires to labels keep the connectivity legible and explicit.
   dx=(-7.62 if px<0 else 7.62) if name in ['Socket22','Display34']else 0
   dy=-5.08 if name in ['R','C']and pin=='1'else 5.08 if name in ['R','C','TestPoint','PWR_FLAG']else 0
   ex,ey=xx+dx,yy+dy
   if dx or dy:pieces.append('(wire (pts (xy '+f'{xx:g} {yy:g}'+') (xy '+f'{ex:g} {ey:g}'+')) (stroke (width 0) (type default)) (uuid "'+uid('wire/'+ref+'/'+pin)+'"))')
   pieces.append(label(c['net'][pin],ex,ey))
  else:pieces.append('(no_connect (at '+f'{xx:g} {yy:g}'+') (uuid "'+uid('nc/'+ref+'/'+pin)+'"))')
def note(text,x,y,size=1.27):pieces.append('(text '+json.dumps(text)+' (at '+f'{x:g} {y:g} 0'+') '+effects(size,'left top')+' (uuid "'+uid('text/'+text)+'"))')
note('ESP32-S3 I80 Doom carrier - rev A',25.4,15.24,2.54)
note('U1: Espressif ESP32-S3-DevKitC-1-N16R8, PCB Rev1.0 only. RGB=GPIO48.\nJ1/J2 match the two 22-pin rows. USB-to-UART is the sole power/input port.\nDo not use Rev1.1: its RGB LED shares display reset GPIO38.\nThe carrier does not connect the DevKit 5V or EN pins.',25.4,24.13)
note('D0..D15 = GPIO1..GPIO16. WR=17, DC=18, CS=21, RST=38, BL=39.\nR1..R21 are 33 ohm source series resistors; LCD_CAM clock = 10 MHz.\nGPIO3 is a strapping input. DB2 has no external pull resistor.\nNo GPIO26..37, native USB19/20, UART43/44, or strap0/45/46 is driven.',155,24.13)
note('DISP1: LCDWIKI/QDtech MRB3205, 16-bit mode: R16=0R, R8 open.\nSupply is 3V3: CLOSE module jumper J1 (LDO bypass).\nJ3 pin1..34 connects pin-for-pin via Samtec IDSD-17-D-04.00-G.\nRed stripe = pin1 at both connectors; verify continuity before power.\nRD is pulled high; SD/touch/flash CS are pulled high.\nTouch, SD, flash and audio are not used by this build.',265,174)
note('80 x 100 x 1.6 mm, two copper layers; 2.9 mm NPTH at (4,4), (76,4), (4,96), (76,96).\nFull BOM includes the DevKit, display, cable, fasteners and enclosure.\nPower/current, signal integrity and physical fit remain prototype checks.',25.4,236.22)
embedded='\n'.join(s.replace('(symbol "'+n+'"','(symbol "doom-carrier:'+n+'"',1)for n,s in syms.items())
content='(kicad_sch (version 20260101) (generator "eeschema") (uuid "'+sch_id+'") (paper "A3") (title_block (title "ESP32-S3 I80 Doom carrier") (date "2026-11-18") (rev "A") (company "LabWired") (comment 1 "DevKitC-1-N16R8 Rev1.0 / MRB3205 / 16-bit I80 / 3V3 only"))\n(lib_symbols\n'+embedded+'\n)\n'+'\n'.join(pieces)+'\n(embedded_fonts no)\n)\n'
(el/'doom-carrier.kicad_sch').write_text(content)
(el/'doom-carrier.kicad_pro').write_text(json.dumps({'meta':{'filename':'doom-carrier.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_clearance':0.2,'min_track_width':0.25,'min_via_diameter':0.6,'min_through_hole_diameter':0.3,'min_via_annular_width':0.15,'min_copper_edge_clearance':0.5,'min_hole_clearance':0.25,'min_hole_to_hole':0.25},'rule_severities':{},'drc_exclusions':[]}},'net_settings':{'classes':[{'name':'Default','clearance':0.2,'track_width':0.3,'via_diameter':0.6,'via_drill':0.3,'bus_width':12,'wire_width':6,'line_style':0,'schematic_color':'rgba(0, 0, 0, 0.000)','pcb_color':'rgba(0, 0, 0, 0.000)'}],'meta':{'version':3}}},indent=2)+'\n')
(root/'electronics'/'authoring-metadata.json').write_text(json.dumps({'schematic_uuid':sch_id,'components':components},indent=2)+'\n')
print('Wrote schematic',len(content),'bytes')
