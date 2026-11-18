#!/usr/bin/env python3
"""Build an original, playable 32 KiB DMG brick-breaker cartridge.

The SM83 bytecode owns gameplay, collisions, graphics and controls. There is
no native MCU game substitute. The ROM runs in the same Peanut-GB emulator
on the STM32 firmware and in the deterministic host capture harness.
"""
from pathlib import Path
import hashlib, json
from brick_breaker_font import FONT

ROOT = Path(__file__).resolve().parent
rom = bytearray(32768)
labels, fixups = {}, []
pc = 0x150
def emit(*data):
    global pc
    rom[pc:pc+len(data)] = bytes(data)
    pc += len(data)
def label(name):
    assert name not in labels, name
    labels[name] = pc
def jp(name, opcode=0xC3):
    emit(opcode,0,0); fixups.append((pc-2,name,'abs'))
def jr(name, opcode=0x18):
    emit(opcode,0); fixups.append((pc-1,name,'rel'))
def call(name): jp(name,0xCD)
def lda(addr): emit(0xFA,addr&255,addr>>8)
def sta(addr): emit(0xEA,addr&255,addr>>8)
def imm(v): emit(0x3E,v&255)
def setmem(addr,v): imm(v); sta(addr)
def copy(dest,src,count):
    emit(0x21,dest&255,dest>>8,0x11,src&255,src>>8,0x01,count&255,count>>8)
    call('copy')
def message(s):
    for i,ch in enumerate(s.ljust(12)):
        setmem(0x9944+i,ord(ch))  # row 10, column 4

# Cartridge header. No proprietary boot ROM or downloaded game is needed.
rom[0x100:0x104] = bytes([0,0xC3,0x50,0x01])
rom[0x134:0x144] = b'BRICK BREAKER'.ljust(16,b'\0')
rom[0x147:0x14D] = bytes([0,0,0,1,0x33,0])

# WRAM: paddleX, ballX, ballY, velocityX, velocityY, score, lives,
# state (0=ready,1=playing,2=over), pause, previous buttons, palette,
# animation tick, remaining bricks. Coordinates are actual screen pixels.
P,X,Y,VX,VY,SCORE,LIVES,STATE,PAUSE,PREV,PAL,TICK,LEFT = range(0xC000,0xC00D)
label('entry'); emit(0xF3,0x31,0xFE,0xDF,0xAF,0xE0,0x40)
copy(0x8000,0x1000,2048)
copy(0x9800,0x2000,1024)
emit(0x21,0,0xFE,0x06,160,0xAF)
label('clear_oam'); emit(0x22,0x05); jr('clear_oam',0x20)
copy(0xFE00,0x2400,16)
setmem(PREV,0); setmem(PAL,0xE4); setmem(TICK,0)
call('reset')
imm(0xE4); emit(0xE0,0x47,0xE0,0x48,0xE0,0x49)
imm(0x93); emit(0xE0,0x40)

label('frame')
label('wait_visible'); emit(0xF0,0x44,0xFE,144); jr('wait_visible',0x30)
label('wait_vblank'); emit(0xF0,0x44,0xFE,144); jr('wait_vblank',0x38)
lda(TICK); emit(0x3C); sta(TICK)
imm(0x20); emit(0xE0,0,0xF0,0,0xF0,0,0x2F,0xE6,15,0x47) # B = directions
imm(0x10); emit(0xE0,0,0xF0,0,0xF0,0,0x2F,0xE6,15,0x4F) # C = actions
imm(0x30); emit(0xE0,0)
lda(PREV); emit(0x2F,0xA1,0x57,0x79); sta(PREV) # D = rising actions
emit(0xCB,0x4A); jr('no_reset',0x28) # B reset
emit(0xC5,0xD5); call('reset'); emit(0xD1,0xC1)
label('no_reset'); emit(0xCB,0x52); jr('no_palette',0x28)
lda(PAL); emit(0xEE,0xFF); sta(PAL); emit(0xE0,0x47,0xE0,0x48)
label('no_palette'); emit(0xCB,0x5A); jr('no_pause',0x28)
lda(PAUSE); emit(0xEE,1); sta(PAUSE)
label('no_pause'); lda(PAUSE); emit(0xB7); jp('draw',0xC2)

# Left/right move the 24-pixel paddle by three pixels per frame.
emit(0xCB,0x40); jr('no_right',0x28)
lda(P); emit(0xC6,3,0xFE,130); jr('right_ok',0x38); imm(130)
label('right_ok'); sta(P)
label('no_right'); emit(0xCB,0x48); jr('no_left',0x28)
lda(P); emit(0xD6,3,0xFE,7); jr('left_ok',0x30); imm(7)
label('left_ok'); sta(P)
label('no_left'); lda(STATE); emit(0xFE,2); jr('not_over',0x20)
emit(0xCB,0x42); jp('draw',0xCA); call('reset'); jp('draw')
label('not_over'); emit(0xB7); jr('play',0x20)
lda(P); emit(0xC6,9); sta(X); setmem(Y,116)
emit(0xCB,0x42); jp('draw',0xCA)
setmem(STATE,1); setmem(VX,2); setmem(VY,-2)
message('')

label('play')
lda(VX); emit(0x47); lda(X); emit(0x80); sta(X)
emit(0xFE,8); jr('not_left_wall',0x30)
setmem(X,8); setmem(VX,2)
label('not_left_wall'); lda(X); emit(0xFE,146); jr('not_right_wall',0x38)
setmem(X,146); setmem(VX,-2)
label('not_right_wall'); lda(VY); emit(0x47); lda(Y); emit(0x80); sta(Y)
emit(0xFE,24); jr('not_ceiling',0x30)
setmem(Y,24); setmem(VY,2)
label('not_ceiling')

# Read the actual background tile under the ball centre. Only tile IDs
# 8..13 are bricks. Clear both tile halves atomically on a collision.
lda(Y); emit(0xC6,3,0xFE,32); jr('no_brick',0x38)
emit(0xFE,56); jr('no_brick',0x30)
emit(0xE6,0x38,0x87,0x87,0x47) # B = tile row * 32
lda(X); emit(0xC6,3,0xCB,0x3F,0xCB,0x3F,0xCB,0x3F,0xB0,0x6F,0x26,0x98)
emit(0x7E,0xFE,8); jr('no_brick',0x38)
emit(0xFE,14); jr('no_brick',0x30)
emit(0x7D,0xE6,0xFE,0x6F,0x3E,32,0x22,0x77)
lda(VY); emit(0x2F,0x3C); sta(VY)
lda(SCORE); emit(0x3C,0xFE,100); jr('score_ok',0x38); emit(0xAF)
label('score_ok'); sta(SCORE)
lda(LEFT); emit(0x3D); sta(LEFT); jr('no_brick',0x20)
call('new_bricks'); call('serve'); jp('draw')
label('no_brick')

# A descending ball bounces from the paddle. The contact half selects
# the horizontal direction, so the player can steer toward remaining bricks.
lda(VY); emit(0xCB,0x7F); jr('not_paddle',0x20)
lda(Y); emit(0xFE,118); jr('not_paddle',0x38)
emit(0xFE,126); jr('not_paddle',0x30)
lda(P); emit(0x47); lda(X); emit(0xC6,5,0xB8); jr('not_paddle',0x38)
lda(P); emit(0xC6,24,0x47); lda(X); emit(0xB8); jr('not_paddle',0x30)
setmem(Y,118); setmem(VY,-2)
lda(P); emit(0xC6,12,0x47); lda(X); emit(0xC6,3,0x90)
emit(0xFE,5); jr('bounce_middle',0x38)
emit(0xFE,252); jr('bounce_middle',0x30)
emit(0xCB,0x7F); jr('bounce_right',0x28)
setmem(VX,-2); jr('not_paddle')
label('bounce_right'); setmem(VX,2); jr('not_paddle')
label('bounce_middle'); lda(VX); emit(0xCB,0x7F); jr('middle_right',0x28)
setmem(VX,-1); jr('not_paddle')
label('middle_right'); setmem(VX,1)
label('not_paddle'); lda(Y); emit(0xFE,137); jp('draw',0xDA)
lda(LIVES); emit(0x3D); sta(LIVES); jr('game_over',0x28)
call('serve'); jp('draw')
label('game_over'); setmem(STATE,2); message('GAME OVER')

label('draw')
# Sprite positions. Ball tile is 6x6; three paddle tiles form 24x6 pixels.
lda(Y); emit(0xC6,16); sta(0xFE00)
lda(X); emit(0xC6,8); sta(0xFE01)
lda(P); emit(0xC6,8); sta(0xFE05); emit(0xC6,8); sta(0xFE09); emit(0xC6,8); sta(0xFE0D)
# Two decimal score digits, lives and the pause mark.
lda(SCORE); emit(0x06,48)
label('score_tens'); emit(0xFE,10); jr('score_digits',0x38); emit(0xD6,10,0x04); jr('score_tens')
label('score_digits'); emit(0xC6,48); sta(0x9828); emit(0x78); sta(0x9827)
lda(LIVES); emit(0xC6,48); sta(0x9831)
lda(PAUSE); emit(0xB7); jr('unpaused_mark',0x28); imm(ord('P')); jr('write_pause')
label('unpaused_mark'); imm(32)
label('write_pause'); sta(0x982B)
jp('frame')

label('reset')
setmem(P,68); setmem(SCORE,0); setmem(LIVES,3); setmem(PAUSE,0)
call('new_bricks'); call('serve'); emit(0xC9)
label('serve')
setmem(STATE,0); setmem(VX,2); setmem(VY,-2)
lda(P); emit(0xC6,9); sta(X); setmem(Y,116)
message('A TO LAUNCH'); emit(0xC9)
label('new_bricks')
copy(0x9882,0x2480,16); copy(0x98A2,0x2490,16); copy(0x98C2,0x24A0,16)
setmem(LEFT,24); emit(0xC9)
label('copy'); emit(0x1A,0x22,0x13,0x0B,0x78,0xB1); jr('copy',0x20); emit(0xC9)

for at,name,kind in fixups:
    v=labels[name]
    if kind=='abs': rom[at:at+2]=v.to_bytes(2,'little')
    else:
        d=v-(at+1); assert -128<=d<=127,(name,d); rom[at]=d&255
assert pc<0x1000, hex(pc)

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
tile(1,['03333000','33333300','33113300','33113300','33333300','03333000','00000000','00000000'])
tile(2,['03333333','33111111','31122222','32222222','33333333','03333333','00000000','00000000'])
tile(3,['33333333','11111111','22222222','22222222','33333333','33333333','00000000','00000000'])
tile(4,['33333330','11111133','22222113','22222223','33333333','33333330','00000000','00000000'])
for row,shade in enumerate((2,1,2)):
    # Each 16x8 brick has a two-pixel gutter; neighbouring tiles do not
    # merge into a bar. A bright top face and dark edge remain legible.
    tile(8+row*2,['00000000','03333333','03111111','03'+str(shade)*6,'03'+str(shade)*6,'03333333','00000000','00000000'])
    tile(9+row*2,['00000000','33333330','11111130',str(shade)*6+'30',str(shade)*6+'30','33333330','00000000','00000000'])

tilemap=bytearray([32]*1024)
def text(row,s):
    x=(20-len(s))//2
    tilemap[row*32+x:row*32+x+len(s)]=s.encode()
text(0,'BRICK BREAKER')
tilemap[32+1:32+9]=b'SCORE 00'
tilemap[32+12:32+18]=b'LIFE 3'
text(17,'A PLAY   B RESET')
rom[0x2000:0x2400]=tilemap
rom[0x2400:0x2410]=bytes([132,85,1,0,140,76,2,0,140,84,3,0,140,92,4,0])
for row in range(3): rom[0x2480+row*16:0x2490+row*16]=bytes([8+row*2,9+row*2]*8)
checksum=0
for b in rom[0x134:0x14D]: checksum=(checksum-b-1)&255
rom[0x14D]=checksum
rom[0x14E:0x150]=(sum(rom)&65535).to_bytes(2,'big')
(ROOT/'brick_breaker.gb').write_bytes(rom)
chunks=[]
for start in range(0,len(rom),16):
    row=rom[start:start+16]
    if any(row): chunks.append(f'  [0x{start:04x}] = '+','.join(f'0x{x:02x}' for x in row)+',')
(ROOT/'brick_breaker_rom.h').write_text('/* Original Brick Breaker homebrew, MIT. Generated by build_brick_breaker.py. */\nstatic const unsigned char brick_breaker_rom[32768] = {\n'+'\n'.join(chunks)+'\n};\n')
manifest={'title':'Brick Breaker','platform':'DMG / SM83','bytes':len(rom),'sha256':hashlib.sha256(rom).hexdigest(),'license':'MIT','boot_rom':'none','code_end':hex(pc),'labels':labels,'state':{'paddle_x':0,'ball_x':1,'ball_y':2,'vx':3,'vy':4,'score':5,'lives':6,'phase':7,'paused':8,'remaining_bricks':12}}
(ROOT/'brick-breaker-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:manifest[k] for k in ('title','bytes','code_end','sha256')}))
