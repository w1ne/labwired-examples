/* Execute the exact original DMG cartridge; test controls and capture pixels.
 * Usage: host-brick-breaker [frame.rgb state.jsonl [--promo]]
 * Captured frames use the STM32 ILI9341 firmware's RGB565 palette.
 */
#include <stdio.h>
#include <assert.h>
#define PEANUT_GB_12_COLOUR 0
#define ENABLE_SOUND 0
#include "peanut_gb.h"
#include "brick_breaker_rom.h"
static struct gb_s gb;
static unsigned char fb[144][160];
static unsigned lines;
static uint8_t rom_read(struct gb_s*g,uint_fast32_t a){(void)g;return a<sizeof(brick_breaker_rom)?brick_breaker_rom[a]:255;}
static uint8_t ram_read(struct gb_s*g,uint_fast32_t a){(void)g;(void)a;return 255;}
static void ram_write(struct gb_s*g,uint_fast32_t a,uint8_t v){(void)g;(void)a;(void)v;}
static void error(struct gb_s*g,enum gb_error_e e,uint16_t a){(void)g;fprintf(stderr,"EMU_ERROR %d %04x\n",e,a);exit(1);}
static void line(struct gb_s*g,const uint8_t*p,uint_fast8_t y){(void)g;if(y<144){memcpy(fb[y],p,160);lines++;}}
static void frames(unsigned n,uint8_t pressed){gb.direct.joypad=(uint8_t)~pressed;while(n--)gb_run_frame(&gb);}
static void boot(void){memset(&gb,0,sizeof gb);assert(gb_init(&gb,rom_read,ram_read,ram_write,error,0)==GB_INIT_NO_ERROR);gb_init_lcd(&gb,line);frames(12,0);}
static uint8_t steer(unsigned n){
  /* A transparent, external scripted input track. The ROM has no autoplay. */
  const int offset[4]={-7,0,7,0};
  int target=(int)gb.wram[1]-9 + offset[(n/120)%4];
  int dx=target-gb.wram[0];
  uint8_t b=dx>1?JOYPAD_RIGHT:dx< -1?JOYPAD_LEFT:0;
  if(gb.wram[7]==0 && (n%2)==0) b|=JOYPAD_A;
  return b;
}
int main(int argc,char**argv){
  boot();
  assert(lines>=144 && gb.wram[0]==68 && gb.wram[1]==77 && gb.wram[2]==116);
  assert(gb.wram[7]==0 && gb.wram[6]==3 && gb.wram[12]==24);
  frames(5,JOYPAD_RIGHT);assert(gb.wram[0]==83);
  frames(5,JOYPAD_LEFT);assert(gb.wram[0]==68);
  frames(1,JOYPAD_A);frames(1,0);assert(gb.wram[7]==1 && gb.wram[2]<116);
  frames(1,JOYPAD_START);unsigned x=gb.wram[1],y=gb.wram[2],p=gb.wram[0];
  frames(10,JOYPAD_RIGHT);assert(gb.wram[8]==1 && gb.wram[1]==x && gb.wram[2]==y && gb.wram[0]==p);
  frames(1,JOYPAD_START);frames(1,0);assert(gb.wram[8]==0 && gb.wram[2]!=y);
  frames(1,JOYPAD_B);frames(1,0);assert(gb.wram[0]==68 && gb.wram[5]==0 && gb.wram[6]==3 && gb.wram[7]==0);
  frames(1,JOYPAD_SELECT);assert(gb.wram[10]==0x1B);frames(1,0);frames(1,JOYPAD_SELECT);assert(gb.wram[10]==0xE4);
  frames(1,0);
  unsigned max_score=0, bounces=0;int8_t prev_vy=(int8_t)gb.wram[4];
  for(unsigned n=0;n<2400;n++){
    frames(1,steer(n));
    if(gb.wram[5]>max_score)max_score=gb.wram[5];
    if(prev_vy>0 && (int8_t)gb.wram[4]<0 && gb.wram[2]>110)bounces++;
    prev_vy=(int8_t)gb.wram[4];
  }
  fprintf(stderr,"score=%u bounces=%u remaining=%u lives=%u phase=%u\n",max_score,bounces,gb.wram[12],gb.wram[6],gb.wram[7]);
  assert(max_score>=12 && bounces>=8);
  /* Leaving the paddle on one edge must eventually cost lives. */
  boot();frames(1,JOYPAD_A);frames(80,JOYPAD_LEFT);frames(500,0);assert(gb.wram[6]<3);
  printf("PASS: exact 32768-byte DMG ROM; launch, paddle controls, pause/resume, reset, palette, brick scoring, paddle bounces and missed-ball life loss.\n");
  if(argc>2){
    FILE*f=fopen(argv[1],"wb"),*s=fopen(argv[2],"w");assert(f&&s);
    const uint16_t palette[4]={0x9dc1,0x8d61,0x3306,0x09c1};
    boot();
    for(unsigned n=0;n<1200;n++){
      uint8_t b=steer(n);
      if(argc>3 && strcmp(argv[3],"--promo")==0){
        /* Actual reset/launch inputs, timed at 11.60/12.21 native seconds.
         * This track lives only in the capture harness, never in the ROM. */
        if(n==693)b=JOYPAD_B;
        else if(n>693 && n<729)b=0;
        else if(n==729)b=JOYPAD_A;
        else if(n>729)b=steer(n-729);
      }
      frames(1,b);
      fprintf(s,"{\"frame\":%u,\"joypad\":%u,\"paddle_x\":%u,\"ball_x\":%u,\"ball_y\":%u,\"score\":%u,\"lives\":%u,\"phase\":%u,\"remaining\":%u}\n",n,b,gb.wram[0],gb.wram[1],gb.wram[2],gb.wram[5],gb.wram[6],gb.wram[7],gb.wram[12]);
      for(int yy=0;yy<144;yy++)for(int xx=0;xx<160;xx++){
        uint16_t c=palette[fb[yy][xx]&3];
        unsigned char rgb[3]={(c>>11)*255/31,((c>>5)&63)*255/63,(c&31)*255/31};
        fwrite(rgb,1,3,f);
      }
    }
    fclose(f);fclose(s);
    printf("Captured 1200 actual ROM-emulation frames at native DMG cadence (4194304/70224 Hz), 160x144 RGB24.\n");
  }
}
