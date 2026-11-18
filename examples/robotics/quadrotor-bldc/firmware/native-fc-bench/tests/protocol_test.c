// SPDX-License-Identifier: GPL-3.0-or-later
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "protocol.h"
#include "fixtures/am32-stopped.h"

// Independent wire generator: AM32 make_dshot_package, pinned19df1ec.
// The16-symbol map is the encoder; the firmware uses the inverse32-entry map.
static const unsigned encode[16]={25,27,18,19,29,21,22,23,26,9,10,11,30,13,14,15};
static void wire(uint16_t raw, uint32_t out[4], unsigned bit_clocks) {
    unsigned code=0; bool level[21]; level[0]=false;
    for(int n=12;n>=0;n-=4) code=(code<<5)|encode[(raw>>n)&15];
    for(unsigned i=0;i<20;++i) level[i+1]=level[i]^((code>>(19-i))&1);
    memset(out,0,16);
    for(unsigned i=0;i<128;++i) {
        unsigned bit=(18u*(i+1))/bit_clocks;
        bool high=bit<21?level[bit]:true;
        if(high) out[i/32]|=1u<<(31-i%32);
    }
}
int main(void) {
    assert(dshot_frame(0)==0x000f); assert(dshot_frame(48)==0x0609);
    assert(dshot_frame(100)==0x0c8b); assert(dshot_frame(2047)==0xffe1);
    unsigned cases=4;
    for(unsigned payload=0;payload<4096;++payload) {
        unsigned crc=~(payload^(payload>>4)^(payload>>8))&15;
        uint16_t raw=(uint16_t)((payload<<4)|crc), got=0;
        for(unsigned period=99;period<=101;++period) {
            uint32_t samples[4]; wire(raw,samples,period);
            assert(telemetry_decode(samples,&got)==TELEMETRY_OK); assert(got==payload); ++cases;
        }
        uint32_t broken[4];wire(raw^1u,broken,100);
        assert(telemetry_decode(broken,&got)==TELEMETRY_CRC);++cases;
    }
    uint32_t flat[4]={0};uint16_t got=0;
    assert(telemetry_decode(flat,&got)!=TELEMETRY_OK);++cases;
    memset(flat,255,sizeof flat);assert(telemetry_decode(flat,&got)==TELEMETRY_START);++cases;
    assert(telemetry_period_us(0xfff)==0);assert(telemetry_erpm(0xfff)==0);
    assert(telemetry_period_us(100)==100);assert(telemetry_erpm(100)==600000);
    cases += 4;
    assert(!telemetry_is_erpm(0)); assert(!telemetry_is_erpm(0x234));
    assert(!telemetry_is_erpm(0x456)); assert(!telemetry_is_erpm(0xe00));
    assert(!telemetry_is_erpm(0x1000)); assert(telemetry_is_erpm(0xfff));
    assert(telemetry_is_erpm(0x301)); assert(telemetry_period_us(0x234)==0);
    cases += 8;
    for(unsigned i=0;i<4;++i) {
        assert(telemetry_decode(am32_stopped_samples[i],&got)==TELEMETRY_OK);
        assert(got==0xfff); ++cases;
    }
    printf("protocol cases=%u passed\n",cases);
}
