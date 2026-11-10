/* Behavior tests execute the same cartridge and Peanut-GB core as the MCU. */
#include <stdio.h>
#include <assert.h>
#define PEANUT_GB_12_COLOUR 0
#include "peanut_gb.h"
#include "wire_runner_rom.h"
static struct gb_s gb;
static unsigned char fb[144][160];
static unsigned lines;
static uint8_t rom_read(struct gb_s*g,uint_fast32_t a){(void)g;return a<sizeof(wire_runner_rom)?wire_runner_rom[a]:255;}
static uint8_t ram_read(struct gb_s*g,uint_fast32_t a){(void)g;(void)a;return 255;}
static void ram_write(struct gb_s*g,uint_fast32_t a,uint8_t v){(void)g;(void)a;(void)v;}
static void error(struct gb_s*g,enum gb_error_e e,uint16_t a){(void)g;fprintf(stderr,"EMU_ERROR %d %04x\n",e,a);exit(1);}
static void line(struct gb_s*g,const uint8_t*p,uint_fast8_t y){(void)g;if(y<144){memcpy(fb[y],p,160);lines++;}}
static void frames(unsigned n,uint8_t pressed){gb.direct.joypad=(uint8_t)~pressed;while(n--)gb_run_frame(&gb);}
int main(int argc,char**argv){
  assert(gb_init(&gb,rom_read,ram_read,ram_write,error,0)==GB_INIT_NO_ERROR);
  gb_init_lcd(&gb,line);frames(12,0);
  fprintf(stderr,"pc=%04x lcd=%02x ly=%u lines=%u x=%u y=%u\n",gb.cpu_reg.pc.reg,gb.hram_io[0x40],gb.hram_io[0x44],lines,gb.wram[0],gb.wram[1]);
  assert(lines>=144);assert(gb.wram[0]==48);assert(gb.wram[1]==80);
  frames(10,JOYPAD_RIGHT);assert(gb.wram[0]==58);
  frames(10,JOYPAD_LEFT|JOYPAD_A);assert(gb.wram[0]==38);
  frames(1,JOYPAD_START);unsigned pause_x=gb.wram[0];frames(10,JOYPAD_RIGHT);assert(gb.wram[0]==pause_x);
  frames(1,JOYPAD_START);frames(1,0);assert(gb.wram[6]==0);
  frames(1,JOYPAD_B);assert(gb.wram[0]==48 && gb.wram[2]==0);
  frames(62,JOYPAD_RIGHT);assert(gb.wram[2]==1); // Actual ROM collision increments score.
  unsigned y=gb.wram[1];frames(5,JOYPAD_UP);assert(gb.wram[1]==y-5);
  frames(5,JOYPAD_DOWN);assert(gb.wram[1]==y);
  frames(1,JOYPAD_SELECT);assert(gb.wram[7]==0x1B);frames(1,0);frames(1,JOYPAD_SELECT);assert(gb.wram[7]==0xE4);
  frames(1,JOYPAD_B);frames(2,0);
  if(argc>1){FILE*f=fopen(argv[1],"wb");assert(f);fprintf(f,"P6\n160 144\n255\n");const uint8_t palette[4][3]={{155,188,15},{139,172,15},{48,98,48},{15,56,15}};for(int yy=0;yy<144;yy++)for(int x=0;x<160;x++)fwrite(palette[fb[yy][x]&3],1,3,f);fclose(f);}
  printf("PASS: original 32768-byte DMG ROM; all 8 controls; collision/score; pause; palette; %u scanlines.\n",lines);
}
