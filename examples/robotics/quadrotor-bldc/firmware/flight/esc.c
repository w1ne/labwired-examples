// LabWired quadrotor ESC node: command-driven six-step BLDC control.
// One STM32L476 instance is compiled per rotor with ESC_ID 1..4.
#include <stdint.h>
#include <stdbool.h>
#ifndef ESC_ID
#define ESC_ID 1
#endif
#define CAT2_(a,b) a##b
#define CAT2(a,b) CAT2_(a,b)
#define STR_(x) #x
#define STR(x) STR_(x)
#define PREFIX "ESC " STR(ESC_ID) " "
#define REG(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define RCC_AHB2ENR REG(0x4002104C)
#define RCC_APB1ENR1 REG(0x40021058)
#define RCC_APB2ENR REG(0x40021060)
#define GPIOA_MODER REG(0x48000000)
#define GPIOA_AFRL REG(0x48000020)
#define GPIOA_AFRH REG(0x48000024)
#define GPIOA_IDR REG(0x48000010)
#define GPIOB_MODER REG(0x48000400)
#define GPIOB_IDR REG(0x48000410)
#define GPIOB_ODR REG(0x48000414)
#define GPIOB_AFRH REG(0x48000424)
#define GPIOC_MODER REG(0x48000800)
#define GPIOC_IDR REG(0x48000810)
#define USART2_CR1 REG(0x40004400)
#define USART2_BRR REG(0x4000440C)
#define USART2_ISR REG(0x4000441C)
#define USART2_TDR REG(0x40004428)
#define TIM1_CR1 REG(0x40012C00)
#define TIM1_EGR REG(0x40012C14)
#define TIM1_CCMR1 REG(0x40012C18)
#define TIM1_CCMR2 REG(0x40012C1C)
#define TIM1_CCER REG(0x40012C20)
#define TIM1_PSC REG(0x40012C28)
#define TIM1_ARR REG(0x40012C2C)
#define TIM1_CCR1 REG(0x40012C34)
#define TIM1_CCR2 REG(0x40012C38)
#define TIM1_CCR3 REG(0x40012C3C)
#define TIM1_BDTR REG(0x40012C44)
#define SYST_CSR REG(0xE000E010)
#define SYST_RVR REG(0xE000E014)
#define SYST_CVR REG(0xE000E018)
#define MOE 0x8000u
#define CPU_HZ 4000000u
#define PWM_HZ 1000u
#define PWM_PERIOD_TICKS (CPU_HZ/((3u+1u)*PWM_HZ))
#define CONTROL_HZ 10000u
#define COMMAND_FRAME_TICKS 100u
#define COMMAND_MIN_PERMILLE 180u
#define COMMAND_MAX_PERMILLE 720u
#define COMMAND_TIMEOUT_FRAMES 4u
#define PWM_DEAD_TIME_TICKS 2u
static const uint16_t comm_table[8]={0,(1u<<8)|(1u<<6),(1u<<4)|(1u<<2),(1u<<8)|(1u<<2),(1u<<0)|(1u<<10),(1u<<0)|(1u<<6),(1u<<4)|(1u<<10),0};
static const uint8_t order[6]={1,5,4,6,2,3};
static void text(const char*s){while(*s){while(!(USART2_ISR&(1u<<7))){}USART2_TDR=(uint8_t)*s++;}}
static void stop_inverter(void){TIM1_BDTR&=~MOE;TIM1_CCER=0;}
static void start_inverter(void){TIM1_BDTR|=MOE;}
static void fatal(const char*name){stop_inverter();GPIOB_ODR&=~1u;text(PREFIX);text(name);text(PREFIX "LATCHED OFF\r\n");for(;;){__asm__ volatile("nop");}}
static void commutate(uint32_t hall,uint32_t duty_permille){
 uint32_t duty=(duty_permille*PWM_PERIOD_TICKS)/1000u,low=PWM_PERIOD_TICKS-1u-duty,a=0,b=0,c=0;
 switch(hall){case 1:b=low;c=duty;break;case 2:a=low;b=duty;break;case 3:a=low;c=duty;break;case 4:a=duty;c=low;break;case 5:a=duty;b=low;break;case 6:b=duty;c=low;break;default:break;}
 TIM1_CCR1=a;TIM1_CCR2=b;TIM1_CCR3=c;TIM1_CCER=comm_table[hall&7u];
}
static void init(void){
 RCC_AHB2ENR|=7u;RCC_APB1ENR1|=1u<<17;RCC_APB2ENR|=1u<<11;
 // PA0 is the flight-controller duty command. PA2 is UART; PA8/9/10 are high-side gates.
 uint32_t aclear=(3u<<0)|(3u<<4)|(3u<<16)|(3u<<18)|(3u<<20);
 GPIOA_MODER=(GPIOA_MODER&~aclear)|(2u<<4)|(2u<<16)|(2u<<18)|(2u<<20);
 GPIOA_AFRL=(GPIOA_AFRL&~(15u<<8))|(7u<<8);GPIOA_AFRH=(GPIOA_AFRH&~0xfffu)|0x111u;
 uint32_t bclear=(3u<<0)|(3u<<12)|(3u<<14)|(3u<<26)|(3u<<28)|(3u<<30);
 GPIOB_MODER=(GPIOB_MODER&~bclear)|1u|(2u<<26)|(2u<<28)|(2u<<30);GPIOB_AFRH=(GPIOB_AFRH&~(0xfffu<<20))|(0x111u<<20);
 GPIOC_MODER&=~0xffffu;GPIOB_ODR=1u;
 USART2_BRR=(CPU_HZ+57600u)/115200u;USART2_CR1=(1u<<0)|(1u<<3);
 SYST_RVR=CPU_HZ/CONTROL_HZ-1u;SYST_CVR=0;SYST_CSR=(1u<<2)|1u;
 TIM1_PSC=3;TIM1_ARR=PWM_PERIOD_TICKS-1u;TIM1_CCR1=0;TIM1_CCR2=0;TIM1_CCR3=0;
 TIM1_CCMR1=(6u<<4)|(1u<<3)|(6u<<12)|(1u<<11);TIM1_CCMR2=(6u<<4)|(1u<<3);TIM1_EGR=1;TIM1_BDTR=0x30;TIM1_CR1=1;
}
int main(void){
 init();text(PREFIX "READY command_pwm=PA0\r\n");
 uint32_t old_hall=GPIOC_IDR&7u,old_enc=(GPIOC_IDR>>3)&3u;
 uint32_t edge_t=0,startup_t=0,startup_idx=0,sequence=0,in_band=0,stall_t=0,invalid_t=0;
 uint32_t driver_t=0,overcurrent_t=0,undervoltage_t=0,enc_edges=0;
 uint32_t command_phase=0,command_high=0,command_permille=0,command_age=COMMAND_TIMEOUT_FRAMES,motor_phase=0;
 bool hall_mode=false,target=false,running=false;
 for(;;){
  if((SYST_CSR&(1u<<16))==0)continue;
  uint32_t c=GPIOC_IDR,b=GPIOB_IDR;
  if(GPIOA_IDR&1u)command_high++;
  if(++command_phase>=COMMAND_FRAME_TICKS){
   command_phase=0;
   uint32_t next=command_high*10u;command_high=0;
   if(next>=COMMAND_MIN_PERMILLE&&next<=COMMAND_MAX_PERMILLE){command_permille=next;command_age=0;}
   else {if(command_age<COMMAND_TIMEOUT_FRAMES)command_age++;if(command_age>=COMMAND_TIMEOUT_FRAMES)command_permille=0;}
  }
  driver_t=(b&(1u<<7))?driver_t+1:0;overcurrent_t=(b&(1u<<6))?overcurrent_t+1:0;undervoltage_t=(c&(1u<<7))?undervoltage_t+1:0;
  if(driver_t>=20)fatal("FAULT DRIVER\r\n");if(overcurrent_t>=20)fatal("FAULT OVERCURRENT\r\n");if(undervoltage_t>=20)fatal("FAULT UNDERVOLTAGE\r\n");
  if(command_permille==0){if(running){running=false;stop_inverter();text(PREFIX "DISARMED\r\n");}hall_mode=false;sequence=0;startup_t=0;stall_t=0;continue;}
  if(!running){running=true;start_inverter();text(PREFIX "ARMED\r\n");}
  if(++motor_phase<20u)continue; motor_phase=0;
  uint32_t hall=c&7u,enc=(c>>3)&3u;if(enc!=old_enc)enc_edges++;old_enc=enc;edge_t++;startup_t++;
  if(hall==0||hall==7){if(++invalid_t>=100)fatal("FAULT HALL\r\n");continue;}invalid_t=0;
  if(hall!=old_hall){int oi=-1,ni=-1;for(int i=0;i<6;i++){if(order[i]==old_hall)oi=i;if(order[i]==hall)ni=i;}
   if(oi>=0&&ni==(oi+1)%6)sequence++;else sequence=0;old_hall=hall;uint32_t period=edge_t;edge_t=0;stall_t=0;if(sequence>=3)hall_mode=true;
   if(hall_mode){commutate(hall,command_permille);in_band=period>=1&&period<=20?in_band+1:0;if(!target&&in_band>=2&&enc_edges>0){target=true;text(PREFIX "HALL LOCKED\r\n");text("ROTOR " STR(ESC_ID) " HALL LOCKED\r\n");}}
  }else{stall_t++;if(hall_mode&&stall_t>=20)fatal("FAULT STALL\r\n");}
  if(hall_mode)commutate(hall,command_permille);else{if(startup_t%5==0)commutate(order[(++startup_idx)%6],command_permille);if(startup_t>=5000)fatal("FAULT STARTUP\r\n");}
 }
}
