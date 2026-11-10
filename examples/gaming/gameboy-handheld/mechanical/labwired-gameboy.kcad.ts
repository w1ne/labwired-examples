// Generated from ../design-interfaces.json. Edit that file, then rerun generate_enclosure.py.
// Interface SHA-256: 538c35c16001219509d9a0f504cf3ba7d4d06bd59296706bc3d551184b0cee6a
// Units: mm. A packaging concept, not a physically verified production release.
const I = {
  "schema": "labwired.handheld-mechanical-interfaces.v1",
  "units": "mm",
  "coordinateSystem": {
    "x": "right",
    "y": "toward top of handheld",
    "z": "toward front",
    "origin": "rear bottom center"
  },
  "status": "engineering-concept; component heights and fit require supplier drawing confirmation",
  "case": {
    "width": 90,
    "height": 148,
    "depth": 30,
    "wall": 2.4,
    "radius": 7,
    "seamZ": 16,
    "seamGap": 0.25
  },
  "pcb": {
    "id": "main-pcb",
    "width": 78,
    "height": 132,
    "thickness": 1.6,
    "center": [
      0,
      74,
      14.2
    ],
    "radius": 3,
    "mountHoleDiameter": 2.8,
    "mounts": [
      {
        "id": "pcb-mount-tl",
        "at": [
          -29,
          132,
          13.4
        ]
      },
      {
        "id": "pcb-mount-tr",
        "at": [
          29,
          132,
          13.4
        ]
      },
      {
        "id": "pcb-mount-bl",
        "at": [
          -29,
          16,
          13.4
        ]
      },
      {
        "id": "pcb-mount-br",
        "at": [
          29,
          16,
          13.4
        ]
      }
    ]
  },
  "caseFasteners": [
    {
      "id": "case-tl",
      "at": [
        -36,
        136,
        16
      ]
    },
    {
      "id": "case-tr",
      "at": [
        36,
        136,
        16
      ]
    },
    {
      "id": "case-bl",
      "at": [
        -36,
        12,
        16
      ]
    },
    {
      "id": "case-br",
      "at": [
        36,
        12,
        16
      ]
    }
  ],
  "display": {
    "id": "lcd1",
    "catalogType": "ili9341",
    "manufacturer": "Waveshare",
    "model": "2.4inch LCD Module",
    "source": "https://www.waveshare.com/wiki/2.4inch_LCD_Module",
    "outline": [
      70.5,
      43.3
    ],
    "activeArea": [
      48.96,
      36.72
    ],
    "heightAllowance": 6,
    "center": [
      0,
      107,
      24.2
    ],
    "window": [
      50,
      38
    ],
    "bezel": [
      75,
      60
    ],
    "note": "XY dimensions from manufacturer; connector and height keep-outs are provisional"
  },
  "controls": [
    {
      "id": "dpad",
      "kind": "cross",
      "center": [
        -24,
        54,
        30
      ],
      "span": 23,
      "bar": 7.2
    },
    {
      "id": "btn-b",
      "kind": "round",
      "center": [
        18,
        52,
        30
      ],
      "diameter": 10.4
    },
    {
      "id": "btn-a",
      "kind": "round",
      "center": [
        33,
        64,
        30
      ],
      "diameter": 10.4
    },
    {
      "id": "btn-select",
      "kind": "pill",
      "center": [
        -8,
        28,
        30
      ],
      "size": [
        11,
        4.6
      ]
    },
    {
      "id": "btn-start",
      "kind": "pill",
      "center": [
        9,
        28,
        30
      ],
      "size": [
        11,
        4.6
      ]
    }
  ],
  "connectors": [
    {
      "id": "usb1",
      "type": "usb-c",
      "center": [
        0,
        148,
        10
      ],
      "opening": [
        10,
        4
      ],
      "note": "Panel-mounted USB-C extension/pigtail to the rear-mounted WeAct Black Pill; not directly aligned with the MCU connector. Exact purchased connector and cable require fit confirmation."
    }
  ],
  "battery": {
    "id": "battery-envelope",
    "size": [
      48,
      58,
      7
    ],
    "center": [
      0,
      47,
      5.8
    ],
    "note": "Reserved geometric envelope only; no cell or power circuit selected"
  },
  "speaker": {
    "id": "speaker1",
    "center": [
      26,
      22,
      26.0
    ],
    "diameter": 19,
    "height": 3,
    "slots": 5
  }
};

// Screw-on two-shell pattern adapted from KernelCAD's enclosure-lid-with-screw-bosses cookbook.
const W = param('caseWidth', I.case.width, { min: 90, max: 90 });
const H = param('caseHeight', I.case.height, { min: 148, max: 148 });
const D = param('caseDepth', I.case.depth, { min: 30, max: 30 });
const wall = param('wall', I.case.wall, { min: 2.2, max: 2.6 });
const seam = I.case.seamZ;
const gap = I.case.seamGap;
const corner = I.case.radius;
const cy = H.divide(2);
const innerW = W.subtract(wall.multiply(2));
const innerH = H.subtract(wall.multiply(2));
const frontFloor = D.subtract(wall);
const a = assembly('labwired-gameboy-handheld');

function rounded(w,h,r,z,t,x=0,y=0) {
  return extrudeRoundedRect(w,h,r,t).translate(x,y,z);
}
function cross(span,bar,z,t,x,y) {
  return extrudeRect(span,bar,t).union(extrudeRect(bar,span,t)).translate(x,y,z);
}
function addFixed(name, shape, at, material='abs', parent=rear, parentName='rear-shell') {
  const p = a.part(name,shape,{material});
  parent.connector(name, { type:'frame', origin:{kind:'vec3',value:at} });
  p.connector('mount', { type:'frame', origin:{kind:'vec3',value:at} });
  a.mate(name, `${parentName}.${name}`, `${name}.mount`, 'fastened');
  return p;
}

let back = rounded(W,H,corner,0,seam,0,cy)
  .subtract(rounded(innerW,innerH,corner-I.case.wall,wall,seam+1,0,cy));
// Rear service cover opening. A separate inset cover provides battery access.
back = back.subtract(rounded(53.6,65.6,4.3,-0.5,4,0,47));
for (const fastener of I.caseFasteners) {
  const x=fastener.at[0], y=fastener.at[1];
  back=back.union(cylinder(seam-I.case.wall+0.1,4).translate(x,y,I.case.wall-0.1));
  back=back.subtract(cylinder(seam+1,1.05).translate(x,y,2.8));
}
for (const point of I.pcb.mounts) {
  back=back.union(cylinder(point.at[2]-I.case.wall,3).translate(point.at[0],point.at[1],I.case.wall));
  back=back.subtract(cylinder(12,1.05).translate(point.at[0],point.at[1],3));
}
// Top USB-C aperture is generated from the shared connector keep-out.
const usb=I.connectors[0];
const usbCut=box(usb.opening[0],8,usb.opening[1],false)
  .translate(usb.center[0]-usb.opening[0]/2,usb.center[1]-4,usb.center[2]-usb.opening[1]/2);
back=back.subtract(usbCut).finish('abs',{color:'#c7c5bc'});
const rear=a.part('rear-shell',back,{material:'abs'});

let face=rounded(W,H,corner,seam+gap,D.subtract(seam+gap),0,cy)
  .subtract(rounded(innerW,innerH,corner-I.case.wall,seam+gap-0.1,frontFloor.subtract(seam+gap).add(0.1),0,cy));
const lcd=I.display;
face=face.subtract(rounded(lcd.window[0],lcd.window[1],1.1,26,7,lcd.center[0],lcd.center[1]));
for (const fastener of I.caseFasteners) {
  const x=fastener.at[0], y=fastener.at[1];
  face=face.union(cylinder(frontFloor.subtract(seam+gap).add(0.1),3.8).translate(x,y,seam+gap));
  face=face.subtract(cylinder(18,1.4).translate(x,y,seam));
  face=face.subtract(cylinder(2.1,2.6).translate(x,y,D.subtract(1.2)));
}
for (const button of I.controls) {
  const x=button.center[0], y=button.center[1];
  if(button.kind==='cross') face=face.subtract(cross(button.span+0.6,button.bar+0.6,26,8,x,y));
  if(button.kind==='round') face=face.subtract(cylinder(8,(button.diameter+0.6)/2).translate(x,y,26));
  if(button.kind==='pill') face=face.subtract(rounded(button.size[0]+0.6,button.size[1]+0.6,(button.size[1]+0.6)/2,26,8,x,y));
}
for(let i=0;i<I.speaker.slots;i++) {
  face=face.subtract(rounded(1.6,13,0.8,26,8,I.speaker.center[0]-6+i*3,I.speaker.center[1]));
}
// Integral side ledges seat the LCD module without penetrating its board.
for(const side of [-1,1]) face=face.union(box(9.2,12,1.9,false).translate(side>0?33.5:-42.7,101,20.5));
face=face.finish('abs',{color:'#e0ddd3'});
const front=addFixed('front-shell',face,[38,136,seam+gap/2]);

const cover=rounded(53,65,4,0.2,2.0,0,47)
  .subtract(rounded(14,2,0.8,-0.1,0.65,0,21))
  .finish('abs',{color:'#b9b7af'});
const batteryCover=addFixed('battery-service-cover',cover,[26.6,47,1.2]);

// The display aperture and active glass follow the selected Waveshare module.
const bezel=rounded(lcd.bezel[0],lcd.bezel[1],6,30.05,1.5,lcd.center[0],lcd.center[1])
  .subtract(rounded(lcd.window[0],lcd.window[1],1,29.9,3,lcd.center[0],lcd.center[1]))
  .finish('abs',{color:'#44454a'});
addFixed('display-bezel',bezel,[32,107,30.03],'abs',front,'front-shell');
const lcdBoard=rounded(lcd.outline[0],lcd.outline[1],1.4,22.6,1.6,lcd.center[0],lcd.center[1])
  .finish('abs',{color:'#194a36'});
const lcdSupport=addFixed('lcd1-pcb-envelope',lcdBoard,[34.5,107,22.5],'abs',front,'front-shell');
const displayFrame=rounded(52.4,40.8,1,24.3,2.7,0,107)
  .subtract(rounded(lcd.activeArea[0]+0.4,lcd.activeArea[1]+0.4,0.3,24.2,3,0,107))
  .finish('abs',{color:'#171b1b'});
addFixed('lcd1-frame-envelope',displayFrame,[25.5,107,24.25],'abs',lcdSupport,'lcd1-pcb-envelope');
const glass=rounded(lcd.activeArea[0],lcd.activeArea[1],0.2,24.4,2.4,0,107)
  .material({baseColor:'#829d58',metalness:0.05,roughness:0.22});
addFixed('lcd1-active-glass',glass,[0,107,24.3],'abs',lcdSupport,'lcd1-pcb-envelope');

let pcb=rounded(I.pcb.width,I.pcb.height,I.pcb.radius,I.pcb.center[2]-I.pcb.thickness/2,I.pcb.thickness,I.pcb.center[0],I.pcb.center[1]);
for(const point of I.pcb.mounts) pcb=pcb.subtract(cylinder(3,I.pcb.mountHoleDiameter/2).translate(point.at[0],point.at[1],12.9));
// Clear the four case closure posts, distinct from PCB mounting posts.
for(const fastener of I.caseFasteners) pcb=pcb.subtract(cylinder(3,4.3).translate(fastener.at[0],fastener.at[1],12.9));
addFixed('main-pcb-envelope',pcb.finish('abs',{color:'#24583c'}),[I.pcb.mounts[0].at[0]+2,I.pcb.mounts[0].at[1],I.pcb.mounts[0].at[2]]);

for(const button of I.controls) {
  const x=button.center[0], y=button.center[1];
  let shape;
  if(button.kind==='cross') {
    shape=cross(button.span,button.bar,27.3,5,x,y)
      .union(cylinder(1.2,13).translate(x,y,26.1));
  } else if(button.kind==='round') {
    shape=cylinder(5,button.diameter/2).translate(x,y,27.3)
      .union(cylinder(1.1,button.diameter/2+1.5).translate(x,y,26.2));
  } else {
    shape=rounded(button.size[0],button.size[1],button.size[1]/2,27.3,4.1,x,y)
      .union(rounded(button.size[0]+1.8,button.size[1]+1.8,(button.size[1]+1.8)/2,26.2,1.1,x,y));
  }
  const color=button.kind==='round'?'#8c2b52':button.kind==='cross'?'#242830':'#6a6b71';
  const bx=x+(button.kind==='cross'?10:button.kind==='round'?button.diameter/2+0.6:button.size[0]/2+0.5);
  const by=y+(button.kind==='cross'?4.1:0);
  addFixed(button.id,shape.finish('abs',{color}),[bx,by,27.45],'abs',front,'front-shell');
}

// Reserving this envelope does not select a cell or claim a battery circuit exists.
const battery=I.battery;
addFixed('battery-reserved-envelope',rounded(battery.size[0],battery.size[1],3,battery.center[2]-battery.size[2]/2,battery.size[2],battery.center[0],battery.center[1])
  .finish('abs',{color:'#6684a7'}),[0,47,2.5],'abs',batteryCover,'battery-service-cover');
const speaker=I.speaker;
addFixed('speaker-reserved-envelope',cylinder(speaker.height,speaker.diameter/2)
  .translate(speaker.center[0],speaker.center[1],speaker.center[2]-speaker.height/2)
  .finish('steel',{color:'#45484a'}),[35,22,27.55],'mild-steel',front,'front-shell');

return a.solvedModel({});
