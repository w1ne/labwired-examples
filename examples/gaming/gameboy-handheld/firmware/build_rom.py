#!/usr/bin/env python3
"""Build the original Wire Runner DMG homebrew cartridge, with no ROM downloads.

The bytecode runs on the Game Boy SM83 CPU. The embedded firmware interprets
this ROM through Peanut-GB. Graphics, game logic and this assembler are MIT.
"""
from pathlib import Path
import hashlib, json

ROOT = Path(__file__).resolve().parent
rom = bytearray(32768)
labels, fixups = {}, []
pc = 0x150
def emit(*data):
    global pc
    rom[pc:pc+len(data)] = bytes(data)
    pc += len(data)
def label(name): labels[name] = pc
def jp(name, opcode=0xC3):
    emit(opcode,0,0); fixups.append((pc-2,name,'abs'))
def jr(name, opcode=0x18):
    emit(opcode,0); fixups.append((pc-1,name,'rel'))
def call(name): jp(name,0xCD)
def lda(addr): emit(0xFA,addr&255,addr>>8)
def sta(addr): emit(0xEA,addr&255,addr>>8)
def imm(v): emit(0x3E,v)
def setmem(addr,v): imm(v); sta(addr)
def copy(dest,src,count):
    emit(0x21,dest&255,dest>>8,0x11,src&255,src>>8,0x01,count&255,count>>8)
    call('copy')

# Cartridge header. The emulator starts at 0x100 without a proprietary boot ROM.
rom[0x100:0x104] = bytes([0x00,0xC3,0x50,0x01])
rom[0x134:0x144] = b'WIRE RUNNER'.ljust(16,b'\0')
rom[0x147:0x14D] = bytes([0,0,0,1,0x33,0]) # ROM only, 32 KiB, no SRAM

label('entry'); emit(0xF3,0x31,0xFE,0xDF,0xAF,0xE0,0x40)
copy(0x8000,0x1000,2048)
copy(0x9800,0x2000,1024)
emit(0x21,0x00,0xFE,0x06,160,0xAF)
label('clear_oam'); emit(0x22,0x05); jr('clear_oam',0x20)
copy(0xFE00,0x2400,8)
setmem(0xC000,48); setmem(0xC001,80); setmem(0xC002,0)
setmem(0xC003,0); setmem(0xC004,112); setmem(0xC005,80)
setmem(0xC006,0); setmem(0xC007,0xE4)
imm(0xE4); emit(0xE0,0x47,0xE0,0x48,0xE0,0x49)
imm(0x93); emit(0xE0,0x40)

label('frame')
label('wait_visible'); emit(0xF0,0x44,0xFE,144); jr('wait_visible',0x30)
label('wait_vblank'); emit(0xF0,0x44,0xFE,144); jr('wait_vblank',0x38)
imm(0x20); emit(0xE0,0x00,0xF0,0x00,0xF0,0x00,0x2F,0xE6,15,0x47); sta(0xC008)
imm(0x10); emit(0xE0,0x00,0xF0,0x00,0xF0,0x00,0x2F,0xE6,15,0x4F); sta(0xC009)
imm(0x30); emit(0xE0,0x00)
lda(0xC003); emit(0x2F,0xA1,0x57,0x79); sta(0xC003)
emit(0xCB,0x5A); jr('no_pause',0x28) # BIT 3,D
lda(0xC006); emit(0xEE,1); sta(0xC006)
label('no_pause'); emit(0xCB,0x52); jr('no_palette',0x28)
lda(0xC007); emit(0xEE,0xFF); sta(0xC007); emit(0xE0,0x47)
label('no_palette'); emit(0xCB,0x4A); jr('no_reset',0x28)
setmem(0xC000,48); setmem(0xC001,80); setmem(0xC002,0)
label('no_reset'); lda(0xC006); emit(0xB7); jp('draw',0xC2)
# A held gives two movement passes, otherwise one.
emit(0x1E,1,0xCB,0x41); jr('speed_done',0x28); emit(0x1E,2)
label('speed_done'); label('move')
emit(0xCB,0x40); jr('no_right',0x28); lda(0xC000); emit(0xFE,144); jr('no_right',0x30); emit(0x3C); sta(0xC000)
label('no_right'); emit(0xCB,0x48); jr('no_left',0x28); lda(0xC000); emit(0xFE,16); jr('no_left',0x38); emit(0x3D); sta(0xC000)
label('no_left'); emit(0xCB,0x50); jr('no_up',0x28); lda(0xC001); emit(0xFE,56); jr('no_up',0x38); emit(0x3D); sta(0xC001)
label('no_up'); emit(0xCB,0x58); jr('no_down',0x28); lda(0xC001); emit(0xFE,120); jr('no_down',0x30); emit(0x3C); sta(0xC001)
label('no_down'); emit(0x1D); jp('move',0xC2)
# Collision: signed differences within [-6,6], expressed via +6 < 13.
lda(0xC004); emit(0x57); lda(0xC000); emit(0x92,0xC6,6,0xFE,13); jp('draw',0xD2)
lda(0xC005); emit(0x57); lda(0xC001); emit(0x92,0xC6,6,0xFE,13); jp('draw',0xD2)
lda(0xC002); emit(0x3C,0xFE,10); jr('score_ok',0x38); emit(0xAF)
label('score_ok'); sta(0xC002)
# Alternate target between top-left and lower-right. A complete playable loop.
lda(0xC004); emit(0xEE,0x50); sta(0xC004)
lda(0xC005); emit(0xEE,0x20); sta(0xC005)
label('draw')
lda(0xC001); sta(0xFE00); lda(0xC000); sta(0xFE01)
lda(0xC005); sta(0xFE04); lda(0xC004); sta(0xFE05)
lda(0xC002); emit(0xC6,48); sta(0x984F)
lda(0xC006); emit(0xB7); jr('running',0x28); imm(ord('P')); jr('state_draw')
label('running'); imm(ord(' '))
label('state_draw'); sta(0x9842)
jp('frame')

label('copy'); emit(0x1A,0x22,0x13,0x0B,0x78,0xB1); jr('copy',0x20); emit(0xC9)
for at,name,kind in fixups:
    v=labels[name]
    if kind=='abs': rom[at:at+2]=v.to_bytes(2,'little')
    else:
        d=v-(at+1)
        assert -128<=d<=127,(name,d)
        rom[at]=d&255
assert pc<0x1000

# Original 5x7 pixel font, left-to-right row strings, in 8x8 two-bit tiles.
FONT={
'A':['01110','10001','10001','11111','10001','10001','10001'],
'B':['11110','10001','10001','11110','10001','10001','11110'],
'C':['01111','10000','10000','10000','10000','10000','01111'],
'D':['11110','10001','10001','10001','10001','10001','11110'],
'E':['11111','10000','10000','11110','10000','10000','11111'],
'F':['11111','10000','10000','11110','10000','10000','10000'],
'G':['01111','10000','10000','10111','10001','10001','01111'],
'H':['10001','10001','10001','11111','10001','10001','10001'],
'I':['11111','00100','00100','00100','00100','00100','11111'],
'J':['00111','00010','00010','00010','10010','10010','01100'],
'K':['10001','10010','10100','11000','10100','10010','10001'],
'L':['10000','10000','10000','10000','10000','10000','11111'],
'M':['10001','11011','10101','10101','10001','10001','10001'],
'N':['10001','11001','10101','10011','10001','10001','10001'],
'O':['01110','10001','10001','10001','10001','10001','01110'],
'P':['11110','10001','10001','11110','10000','10000','10000'],
'Q':['01110','10001','10001','10001','10101','10010','01101'],
'R':['11110','10001','10001','11110','10100','10010','10001'],
'S':['01111','10000','10000','01110','00001','00001','11110'],
'T':['11111','00100','00100','00100','00100','00100','00100'],
'U':['10001','10001','10001','10001','10001','10001','01110'],
'V':['10001','10001','10001','10001','10001','01010','00100'],
'W':['10001','10001','10001','10101','10101','10101','01010'],
'X':['10001','10001','01010','00100','01010','10001','10001'],
'Y':['10001','10001','01010','00100','00100','00100','00100'],
'Z':['11111','00001','00010','00100','01000','10000','11111'],
'0':['01110','10001','10011','10101','11001','10001','01110'],
'1':['00100','01100','00100','00100','00100','00100','01110'],
'2':['01110','10001','00001','00010','00100','01000','11111'],
'3':['11110','00001','00001','01110','00001','00001','11110'],
'4':['00010','00110','01010','10010','11111','00010','00010'],
'5':['11111','10000','10000','11110','00001','00001','11110'],
'6':['01110','10000','10000','11110','10001','10001','01110'],
'7':['11111','00001','00010','00100','01000','01000','01000'],
'8':['01110','10001','10001','01110','10001','10001','01110'],
'9':['01110','10001','10001','01111','00001','00001','01110'],
':':['00000','00100','00100','00000','00100','00100','00000'],
'-':['00000','00000','00000','11111','00000','00000','00000'],
}
for char,rows in FONT.items():
    at=0x1000+ord(char)*16
    for y,row in enumerate(rows):
        b=int(row,2)<<2; rom[at+y*2:at+y*2+2]=bytes([b,b])
def tile(number,rows):
    at=0x1000+number*16
    for y,row in enumerate(rows):
        lo=sum((int(c)&1)<<(7-x) for x,c in enumerate(row))
        hi=sum((int(c)>>1)<<(7-x) for x,c in enumerate(row))
        rom[at+y*2:at+y*2+2]=bytes([lo,hi])
tile(1,['33333333','31111113','31333313','31300313','31300313','31333313','31111113','33333333'])
tile(2,['00033000','00322300','03211230','32111123','32111123','03211230','00322300','00033000'])
tile(3,['22222222','21111112','21000012','21000012','21000012','21000012','21111112','22222222'])
tile(4,['00000000','00000000','00000000','00010000','00000000','00000000','00000000','00000000'])
tilemap=bytearray([32]*1024)
def text(row,s):
    x=(20-len(s))//2
    tilemap[row*32+x:row*32+x+len(s)]=s.encode()
text(0,'LABWIRED'); text(1,'WIRE RUNNER'); text(2,'SCORE:0')
# Fixed score location corresponds to row2,col15.
tilemap[2*32:3*32]=bytes([32]*32)
tilemap[2*32+9:2*32+16]=b'SCORE:0'
for y in range(4,14):
    for x in range(1,19): tilemap[y*32+x]=3 if y in (4,13) or x in(1,18) else 4
text(15,'A:DASH B:RESET'); text(16,'START:PAUSE'); text(17,'SELECT:PALETTE')
rom[0x2000:0x2400]=tilemap
rom[0x2400:0x2408]=bytes([80,48,1,0,80,112,2,0])
checksum=0
for b in rom[0x134:0x14D]: checksum=(checksum-b-1)&255
rom[0x14D]=checksum
rom[0x14E:0x150]=(sum(rom)&65535).to_bytes(2,'big')
(ROOT/'wire_runner.gb').write_bytes(rom)
# Sparse, designated initialization is readable and avoids bloated binary text.
chunks=[]
for start in range(0,len(rom),16):
    row=rom[start:start+16]
    if any(row): chunks.append(f'  [0x{start:04x}] = '+','.join(f'0x{x:02x}' for x in row)+',')
(ROOT/'wire_runner_rom.h').write_text('/* Original Wire Runner homebrew, MIT. Generated by build_rom.py. */\nstatic const unsigned char wire_runner_rom[32768] = {\n'+'\n'.join(chunks)+'\n};\n')
(ROOT/'rom-manifest.json').write_text(json.dumps({'title':'Wire Runner','platform':'DMG / SM83','bytes':len(rom),'sha256':hashlib.sha256(rom).hexdigest(),'license':'MIT','boot_rom':'none','code_end':hex(pc),'labels':labels},indent=2)+'\n')
print(json.dumps({'rom':str(ROOT/'wire_runner.gb'),'bytes':len(rom),'code_end':hex(pc),'sha256':hashlib.sha256(rom).hexdigest()}))
