#!/usr/bin/env python3
"""Validate the compiled AM32 target against the routed KiCad board and guards.
Run with KiCad 10's Python module available (Debian: /usr/bin/python3).
"""
import argparse, hashlib, json, re, subprocess, tempfile
from pathlib import Path
import pcbnew

PCB_SHA = "13a9b74e8a0afc65c016302d155bd7b4e10d3edd8cc331822bfb9ccc9e182249"

def check(macros, board):
    errors, bindings = [], []
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    def require(condition, detail):
        if not condition: errors.append(detail)
    def pin_gpio(prefix):
        port = macros.get(prefix + "_PORT", "")
        pin = macros.get(prefix, "")
        m = re.fullmatch(r"GPIO_PINS_(\d+)", pin)
        return "P" + port[-1:] + m[1] if m and port in ["GPIOA", "GPIOB"] else None
    # QFN28 physical pad numbers, from AT32F421 datasheet package pinout.
    # The copied pin-function labels on restored NC pads are corrected in
    # validation/pad-function-correction-20261118.json. Physical pad numbers
    # and the manufacturer package drawing remain the mapping authority.
    package_pad = {"PA0":"6", "PA1":"7", "PA2":"8", "PA3":"9", "PA4":"10", "PA5":"11", "PA6":"12", "PA7":"13", "PB0":"14", "PB1":"15", "PA8":"18", "PA9":"19", "PA10":"20", "PA13":"21", "PA14":"22", "PA15":"23", "PB3":"24", "PB4":"25", "PB5":"26", "PB6":"27", "PB7":"28"}
    def pad_for_gpio(fp, gpio):
        return next((p for p in fp.Pads() if p.GetNumber() == package_pad.get(gpio)), None)
    for i, (mcu_ref, driver_ref) in enumerate([( "U2", "U4"), ("U5", "U6"), ("U7", "U8"), ("U9", "U10")], 1):
        mcu, driver = footprints[mcu_ref], footprints[driver_ref]
        require(mcu.GetValue() == "AT32F421G8U7", f"{mcu_ref}: exact MCU")
        for phase_index, phase in enumerate("ABC", 1):
            for level, suffix in [("HIGH", "H"), ("LOW", "L")]:
                key = f"PHASE_{phase}_GPIO_{level}"
                port = macros.get(f"PHASE_{phase}_GPIO_PORT_{level}", "")
                bit = macros.get(key, "")
                match = re.fullmatch(r"GPIO_PINS_(\d+)", bit)
                gpio = "P" + port[-1:] + match[1] if match and port in ["GPIOA", "GPIOB"] else None
                pad = pad_for_gpio(mcu, gpio)
                net = f"/ESC{i}/{phase}{suffix}"
                endpoint = next((p for p in driver.Pads() if p.GetPinFunction().startswith(f"{suffix}IN{phase_index}_")), None)
                require(pad is not None and pad.GetNetname() == net and endpoint is not None and endpoint.GetNetname() == net, f"{mcu_ref}: {phase}{suffix} compiled {gpio} does not reach {driver_ref} {suffix}IN{phase_index}")
                bindings.append({"mcu": mcu_ref, "gpio": gpio, "net": net, "driver": driver_ref, "input": f"{suffix}IN{phase_index}"})
            compare_gpio = {"0x400000E5":"PA0", "0x400000C5":"PA4", "0x400000D5":"PA5"}.get(macros.get(f"PHASE_{phase}_COMP"))
            pad = pad_for_gpio(mcu, compare_gpio)
            require(pad is not None and pad.GetNetname() == f"/ESC{i}/FB{phase}", f"{mcu_ref}: comparator {phase} route")
        inp = pad_for_gpio(mcu, pin_gpio("INPUT_PIN"))
        resistors = [f for f in footprints.values() if f.GetValue() == "220R" and {p.GetNetname() for p in f.Pads() if p.GetNumber()} == {f"/M{i}", inp.GetNetname() if inp else ""}]
        require(inp is not None and len(resistors) == 1, f"{mcu_ref}: DShot channel resistor route")
        require(next(p for p in footprints['J1'].Pads() if p.GetNumber() == str(i+4)).GetNetname() == f"/M{i}", f"J1 motor {i}")
        for gpio in ["PA3", "PA6", "PB6"]:
            pad = pad_for_gpio(mcu, gpio)
            require(pad is not None and pad.GetNetname().startswith("unconnected-"), f"{mcu_ref}: {gpio} must remain explicitly unconnected")
    require(macros.get("IC_TIMER_REGISTER") == "TMR3" and macros.get("INPUT_DMA_CHANNEL") == "DMA1_CHANNEL4", "PB4 capture timer/DMA mapping")
    require("TARGET_NO_EXTERNAL_SENSE" in macros, "floating voltage/current ADC must be disabled")
    require("USE_SERIAL_TELEMETRY" not in macros, "serial telemetry pin is unconnected")
    require(macros.get("DEAD_TIME") == "60", "native target dead time")
    return errors, bindings

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    package=Path(__file__).resolve().parents[2]
    pcb=package/'hardware/esc-4in1/4in1.kicad_pcb'
    assert hashlib.sha256(pcb.read_bytes()).hexdigest()==PCB_SHA, 'native PCB identity changed'
    raw=subprocess.check_output(['gcc','-E','-dM','-DOPENESC_30_F421','-x','c',str(args.source/'Inc/targets.h')],text=True)
    macros={m[1]:m[2] for line in raw.splitlines() if (m:=re.match(r'#define (\w+)(?: (.*))?$',line))}
    board=pcbnew.LoadBoard(str(pcb));errors,bindings=check(macros,board);assert not errors, errors
    negatives=[]
    for label,mutations in [
        ('wrong DShot pin',{'INPUT_PIN':'GPIO_PINS_2','INPUT_PIN_PORT':'GPIOA'}),
        ('swapped high-side gates',{'PHASE_A_GPIO_HIGH':'GPIO_PINS_9'}),
        ('wrong comparator mux',{'PHASE_A_COMP':'0x400000C5'}),
        ('invented serial telemetry',{'USE_SERIAL_TELEMETRY':''}),
        ('floating external sensing',{'TARGET_NO_EXTERNAL_SENSE':None})]:
        altered=dict(macros)
        for k,v in mutations.items():
            if v is None: altered.pop(k,None)
            else: altered[k]=v
        failure,_=check(altered,board);assert failure,label;negatives.append({'case':label,'rejected':True,'errors':failure})
    sensor_cases=[]
    with tempfile.TemporaryDirectory(prefix='am32-sensor-contract-') as d:
        root=Path(d);test=root/'contract.c'
        test.write_text('#include "target_sensors.h"\n#include <assert.h>\nint main(void){ for(unsigned v=0;v<3;v++)for(unsigned c=0;c<3;c++){ unsigned char e=target_sensor_errors(v,c);\n#ifdef TARGET_NO_EXTERNAL_SENSE\nassert(e==((v?1:0)|(c?2:0)));\n#else\nassert(e==0);\n#endif\n}return 0;}\n')
        for sense in [False,True]:
            binary=root/('absent' if sense else 'normal');cmd=['gcc','-std=c11','-Wall','-Wextra','-Werror','-I'+str(args.source/'Inc'),str(test),'-o',str(binary)]+(['-DTARGET_NO_EXTERNAL_SENSE'] if sense else [])
            subprocess.run(cmd,check=True);subprocess.run([str(binary)],check=True);sensor_cases.append({'absentExternalSense':sense,'combinations':9,'passed':True})
        for mode in ['USE_ADC_INPUT','USE_NTC','VOLTAGE_BASED_RAMP','FIXED_DUTY_MODE','FIXED_SPEED_MODE']:
            r=subprocess.run(['gcc','-fsyntax-only','-I'+str(args.source/'Inc'),'-DTARGET_NO_EXTERNAL_SENSE','-D'+mode,str(test)],capture_output=True,text=True)
            assert r.returncode!=0 and 'no external ADC channels' in r.stderr,mode
            sensor_cases.append({'unsupportedMode':mode,'rejected':True})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    result={'pcbSha256':PCB_SHA,'kicadVersion':pcbnew.GetBuildVersion(),'sourceFiles':{f:hashlib.sha256((args.source/f).read_bytes()).hexdigest() for f in ['Inc/targets.h','Inc/target_sensors.h','Mcu/f421/Src/ADC.c','Src/main.c','Src/dshot.c','Mcu/f421/Startup/startup_at32f421.s']},'gateBindings':bindings,'negativeControls':negatives,'sensorGuards':sensor_cases,'ok':True,'scope':'Native pad/net and compiled-target validation. No physical switching, motor, current-rating or flight qualification.'}
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(f'PASS: {len(bindings)} native gate paths, four capture paths, twelve comparator paths, five binding negatives and 23 sensor configuration cases')
if __name__=='__main__':main()
