from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description="Generate a pixel-equivalence fixture from both actual MCU draw functions")
parser.add_argument('--baseline-main',type=Path,required=True)
parser.add_argument('--candidate-main',type=Path,required=True)
parser.add_argument('--rom-dir',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
base=args.baseline_main.read_text()
fast=args.candidate_main.read_text()
def draw(source,name):
 a=source.index('static void draw_line(');b=source.index('\nint main(',a)
 s=source[a:b].replace('draw_line(',name+'(')
 for symbol in ('hash','scanlines','line_hashes','previous_pixels','line_valid'):
  import re
  s=re.sub(r'\b'+symbol+r'\b',name+'_'+symbol,s)
 return s
head=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#define PEANUT_GB_12_COLOUR 0
#define ENABLE_SOUND 0
#include "fast/peanut_gb.h"
#include "fast/brick_breaker_rom.h"
#define GPIOA 0
static struct gb_s gb;
static uint32_t baseline_hash,baseline_scanlines,baseline_line_hashes[144];
static uint32_t optimized_hash,optimized_scanlines;
static uint8_t optimized_previous_pixels[144][160],optimized_line_valid[144];
static const uint16_t palette[4]={0x9dc1,0x8d61,0x3306,0x09c1};
static uint16_t display[2][240][320];
static unsigned panel,x0,y0,x1,y1,xpos,ypos;
static unsigned long long pixels[2],windows[2];
static void gpio_write(unsigned port,unsigned pin,int high){(void)port;(void)pin;(void)high;}
static void window(unsigned a,unsigned b,unsigned c,unsigned d){
 assert(a<=c&&b<=d&&c<320&&d<240);x0=a;y0=b;x1=c;y1=d;xpos=x0;ypos=y0;windows[panel]++;
}
static void parameter16(uint16_t v){
 assert(ypos<=y1);display[panel][ypos][xpos]=v;pixels[panel]++;
 if(++xpos>x1){xpos=x0;ypos++;}
}
'''
tail=r'''
static uint8_t rom_read(struct gb_s*g,uint_fast32_t a){(void)g;return a<sizeof(brick_breaker_rom)?brick_breaker_rom[a]:255;}
static uint8_t ram_read(struct gb_s*g,uint_fast32_t a){(void)g;(void)a;return 255;}
static void ram_write(struct gb_s*g,uint_fast32_t a,uint8_t v){(void)g;(void)a;(void)v;}
static void error(struct gb_s*g,enum gb_error_e e,uint16_t a){(void)g;fprintf(stderr,"EMU_ERROR %d %04x\n",e,a);assert(0);}
static void line(struct gb_s*g,const uint8_t*p,uint_fast8_t y){
 panel=0;baseline(g,p,y);panel=1;optimized(g,p,y);
}
static uint8_t steer(unsigned n){
 const int offset[4]={-7,0,7,0};int target=(int)gb.wram[1]-9+offset[(n/120)%4];
 int dx=target-gb.wram[0];uint8_t b=dx>1?JOYPAD_RIGHT:dx< -1?JOYPAD_LEFT:0;
 if(gb.wram[7]==0&&(n%2)==0)b|=JOYPAD_A;return b;
}
int main(void){
 for(unsigned p=0;p<2;p++)for(unsigned y=0;y<240;y++)for(unsigned x=0;x<320;x++)display[p][y][x]=0x09c1;
 assert(gb_init(&gb,rom_read,ram_read,ram_write,error,0)==GB_INIT_NO_ERROR);gb_init_lcd(&gb,line);
 for(unsigned f=0;f<2412;f++){
  if(f==12)memset(pixels,0,sizeof pixels),memset(windows,0,sizeof windows);
  gb.direct.joypad=(uint8_t)~(f<12?0:steer(f-12));baseline_hash=optimized_hash=2166136261u;
  gb_run_frame(&gb);
  if(memcmp(display[0],display[1],sizeof display[0])){fprintf(stderr,"LCD mismatch frame%u\n",f);return 1;}
  assert(baseline_hash==optimized_hash);
 }
 printf("PASS: 2400 gameplay frames, exact RGB565 LCD and full-frame hashes.\n");
 printf("pixel_bytes_baseline=%llu pixel_bytes_optimized=%llu windows=%llu/%llu\n",pixels[0]*2,pixels[1]*2,windows[0],windows[1]);
 printf("state: score=%u lives=%u remaining=%u\n",gb.wram[5],gb.wram[6],gb.wram[12]);
 uint8_t p[160]={0};
 for(unsigned y=0;y<144;y++)line(&gb,p,y);
 for(unsigned x=0;x<160;x++){
  p[x]=3;line(&gb,p,x%144);assert(!memcmp(display[0],display[1],sizeof display[0]));
  p[x]=0;line(&gb,p,x%144);assert(!memcmp(display[0],display[1],sizeof display[0]));
 }
 puts("PASS: one-pixel changes and erasures across all160 source columns.");
 return 0;
}
'''
head=head.replace('"fast/peanut_gb.h"', '"'+str((args.rom_dir/'peanut_gb.h').resolve())+'"')
head=head.replace('"fast/brick_breaker_rom.h"', '"'+str((args.rom_dir/'brick_breaker_rom.h').resolve())+'"')
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(head+draw(base,'baseline')+draw(fast,'optimized')+tail)
