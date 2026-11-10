/* LabWired handheld: actual DMG emulation on STM32F411, USB powered.
 * Game logic executes from wire_runner.gb; no native-game substitute.
 * CPU reset clock: HSI 16 MHz. Display is ILI9341 over SPI1, landscape.
 * Audio, cartridge socket and battery charge control are not implemented.
 */
#include <stdint.h>
#define PEANUT_GB_12_COLOUR 0
#define ENABLE_SOUND 0
#include "peanut_gb.h"
#include "wire_runner_rom.h"

#define REG(a) (*(volatile uint32_t *)(a))
#define GPIOA 0x40020000u
#define GPIOB 0x40020400u
#define RCC 0x40023800u
#define USART2 0x40004400u
#define SPI1 0x40013000u
static struct gb_s gb;
static uint32_t frame_number, scanlines;
static uint8_t previous_input=255;
static uint32_t last_hash;
static uint32_t hash;
static uint32_t line_hashes[144];
static uint8_t last_x,last_y,last_score;
static const uint16_t palette[4]={0x9dc1,0x8d61,0x3306,0x09c1};

static void delay(uint32_t n){for(volatile uint32_t i=0;i<n;i++)__asm__ volatile("nop");}
static void uart_char(char c){while(!(REG(USART2)&(1u<<7))){}REG(USART2+4)=(uint8_t)c;}
static void uart(const char*s){while(*s)uart_char(*s++);}
static void hex(uint32_t v){for(int n=28;n>=0;n-=4)uart_char("0123456789abcdef"[(v>>n)&15]);}
static void decimal(uint32_t v){char b[11];unsigned n=0;do{b[n++]=(char)('0'+v%10);v/=10;}while(v);while(n)uart_char(b[--n]);}
static void gpio_mode(uint32_t port,unsigned pin,unsigned mode){REG(port)=(REG(port)&~(3u<<(pin*2)))|(mode<<(pin*2));}
static void gpio_af(uint32_t port,unsigned pin,unsigned af){unsigned a=port+0x20+(pin/8)*4,shift=(pin%8)*4;REG(a)=(REG(a)&~(15u<<shift))|(af<<shift);}
static void gpio_write(uint32_t port,unsigned pin,int high){REG(port+0x18)=1u<<(pin+(high?0:16));}
static void spi(uint8_t v){while(!(REG(SPI1+8)&2)){}*(volatile uint8_t*)(SPI1+12)=v;while(!(REG(SPI1+8)&1)){}(void)*(volatile uint8_t*)(SPI1+12);}
static void command(uint8_t c){gpio_write(GPIOB,0,0);spi(c);gpio_write(GPIOB,0,1);}
static void parameter16(uint16_t v){spi(v>>8);spi(v);}
static void window(unsigned x0,unsigned y0,unsigned x1,unsigned y1){command(0x2A);parameter16(x0);parameter16(x1);command(0x2B);parameter16(y0);parameter16(y1);command(0x2C);}
static void hw_init(void){
  REG(RCC+0x30)|=3;REG(RCC+0x40)|=1u<<17;REG(RCC+0x44)|=1u<<12;
  gpio_mode(GPIOA,2,2);gpio_mode(GPIOA,3,2);gpio_af(GPIOA,2,7);gpio_af(GPIOA,3,7);
  REG(USART2+8)=139;REG(USART2+12)=(1u<<13)|(1u<<3)|(1u<<2);
  gpio_mode(GPIOA,5,2);gpio_mode(GPIOA,7,2);gpio_af(GPIOA,5,5);gpio_af(GPIOA,7,5);
  gpio_mode(GPIOA,4,1);gpio_mode(GPIOB,0,1);gpio_mode(GPIOB,1,1);gpio_mode(GPIOA,8,1);
  gpio_write(GPIOA,4,1);gpio_write(GPIOB,0,1);gpio_write(GPIOB,1,1);gpio_write(GPIOA,8,1);
  for(unsigned p=3;p<=10;p++){gpio_mode(GPIOB,p,0);REG(GPIOB+0x0C)=(REG(GPIOB+0x0C)&~(3u<<(p*2)))|(1u<<(p*2));}
  REG(SPI1)=(1u<<9)|(1u<<8)|(1u<<6)|(1u<<3)|(1u<<2); // master,8 bit,software CS,4 MHz
  gpio_write(GPIOB,1,0);delay(16000);gpio_write(GPIOB,1,1);delay(160000);
  gpio_write(GPIOA,4,0);
  command(0x01);delay(160000);command(0x11);delay(320000);
  command(0x36);spi(0x28);command(0x3A);spi(0x55);command(0x29);
  window(0,0,319,239);for(unsigned i=0;i<320*240;i++)parameter16(0x09C1);
  gpio_write(GPIOA,4,1);uart("LABWIRED DMG BOOT\n");
}
static uint8_t read_buttons(void){
  uint32_t pins=REG(GPIOB+0x10);uint8_t out=255;
  const uint8_t masks[8]={JOYPAD_UP,JOYPAD_DOWN,JOYPAD_LEFT,JOYPAD_RIGHT,JOYPAD_A,JOYPAD_B,JOYPAD_SELECT,JOYPAD_START};
  for(unsigned i=0;i<8;i++)if(!(pins&(1u<<(i+3))))out&=~masks[i];
  return out;
}
static uint8_t rom_read(struct gb_s*g,uint_fast32_t a){(void)g;return a<sizeof(wire_runner_rom)?wire_runner_rom[a]:255;}
static uint8_t ram_read(struct gb_s*g,uint_fast32_t a){(void)g;(void)a;return 255;}
static void ram_write(struct gb_s*g,uint_fast32_t a,uint8_t v){(void)g;(void)a;(void)v;}
static void emu_error(struct gb_s*g,enum gb_error_e e,uint16_t a){(void)g;uart("DMG_ERROR ");hex(e);uart(" address=");hex(a);uart("\n");for(;;){}}
static void draw_line(struct gb_s*g,const uint8_t*p,uint_fast8_t line){
  (void)g;if(line>=144)return;
  uint32_t lh=2166136261u;
  for(unsigned x=0;x<160;x++){lh^=p[x]&3;lh*=16777619u;hash^=p[x]&3;hash*=16777619u;}
  scanlines++;
  if(line_hashes[line]==lh)return;
  line_hashes[line]=lh;
  // 160x144 -> 240x216 nearest-neighbour scale. Preserve aspect ratio.
  unsigned y0=12+(line*3)/2,y1=12+((line+1)*3)/2-1;
  gpio_write(GPIOA,4,0);window(40,y0,279,y1);
  for(unsigned y=y0;y<=y1;y++)for(unsigned x=0;x<240;x++){uint8_t shade=p[(x*2)/3]&3;parameter16(palette[shade]);}
  gpio_write(GPIOA,4,1);
}
int main(void){
  hw_init();
  if(gb_init(&gb,rom_read,ram_read,ram_write,emu_error,0)!=GB_INIT_NO_ERROR){uart("DMG_INIT_FAILED\n");for(;;){}}
  gb_init_lcd(&gb,draw_line);
  uart("DMG_ROM_OK title=WIRE_RUNNER bytes=32768\n");
  for(;;){
    gb.direct.joypad=read_buttons();
    if(gb.direct.joypad!=previous_input){uart("INPUT=");hex(gb.direct.joypad);uart("\n");previous_input=gb.direct.joypad;}
    hash=2166136261u;gb_run_frame(&gb);frame_number++;
    if(frame_number<=3 || gb.wram[0]!=last_x || gb.wram[1]!=last_y || gb.wram[2]!=last_score || hash!=last_hash){
      uart("DMG_FRAME=");decimal(frame_number);uart(" x=");decimal(gb.wram[0]);uart(" y=");decimal(gb.wram[1]);uart(" score=");decimal(gb.wram[2]);uart(" hash=");hex(hash);uart(" lines=");decimal(scanlines);uart("\n");
      last_x=gb.wram[0];last_y=gb.wram[1];last_score=gb.wram[2];last_hash=hash;
    }
  }
}
