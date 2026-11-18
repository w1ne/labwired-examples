#!/usr/bin/env python3
"""Check target macros against native schematic connectivity, with wrong-target controls."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

PACKAGE = Path(__file__).resolve().parent
BOARD = PACKAGE.parents[1] / "hardware/flight-controller-openfc-lite-rev2-lw1"
VERSIONS = json.loads((PACKAGE / "source-versions.json").read_text())
# Physical connector / component pins establish the intended function; the
# GPIO number is derived independently from the MCU node in each native net.
ENDPOINTS = {
    "MOTOR1_PIN": ("P1", "5"), "MOTOR2_PIN": ("P1", "6"),
    "MOTOR3_PIN": ("P1", "7"), "MOTOR4_PIN": ("P1", "8"),
    "UART0_TX_PIN": ("U8", "3"), "UART0_RX_PIN": ("U8", "4"),
    "PIOUART0_TX_PIN": ("CN1", "4"), "PIOUART0_RX_PIN": ("CN1", "3"),
    "I2C0_SDA_PIN": ("U14", "5"), "I2C0_SCL_PIN": ("U14", "6"),
    "GYRO_1_CS_PIN": ("U9", "12"), "GYRO_1_EXTI_PIN": ("U9", "4"),
    "SPI0_SCK_PIN": ("U9", "13"), "SPI0_SDO_PIN": ("U9", "14"),
    "SPI0_SDI_PIN": ("U9", "1"), "SPI1_SCK_PIN": ("Card1", "5"),
    "SPI1_SDO_PIN": ("Card1", "3"), "SPI1_SDI_PIN": ("Card1", "7"),
    "SDCARD_SPI_CS_PIN": ("Card1", "2"), "ADC_CURR_PIN": ("R6", "1"),
    "ADC_VBAT_PIN": ("R1", "1"), "ADC_RSSI_PIN": ("R7", "1"),
    "ADC_EXTERNAL1_PIN": ("R8", "1"),
    "UART1_TX_PIN": ("J13", "1"), "UART1_RX_PIN": ("U8", "6"),
    "PIOUART1_TX_PIN": ("U14", "4"), "PIOUART1_RX_PIN": ("P1", "4"),
    "OSD_W_PIN": ("R32", "1"), "OSD_EN_PIN": ("U10", "6"),
    "OSD_SYNC_PIN": ("U12", "1"), "BEEPER_PIN": ("Q1", "1"),
    "PINIO1_PIN": ("U6", "2"), "LED0_PIN": ("R15", "1"),
    "LED_STRIP_PIN": ("Q2", "2"),
}

def macro_values(text):
    return {key: (value or "") for key, value in re.findall(r"^#define[ \t]+(\w+)(?:[ \t]+([^\n/]*))?", text, re.M)}

def check(text, native):
    macros = macro_values(text)
    findings = []
    for macro, endpoint in ENDPOINTS.items():
        nets = [net for net in native.findall("nets/net") if any(
            (n.get("ref"), n.get("pin")) == endpoint for n in net.findall("node"))]
        assert len(nets) == 1, (macro, endpoint, len(nets))
        mcu = [n for n in nets[0].findall("node") if n.get("ref") == "U2"]
        assert len(mcu) == 1, (macro, "no unique MCU pad")
        gpio = int(re.match(r"GPIO(\d+)", mcu[0].get("pinfunction", ""))[1])
        actual = macros.get(macro, "").strip()
        assert actual == f"PA{gpio}", (macro, actual, gpio)
        assert nets[0].get("name") not in ["GND", "+3.3V", "+5V"]
        findings.append({"macro": macro, "gpio": gpio, "mcu_pad": mcu[0].get("pin"),
                         "endpoint": list(endpoint), "net": nets[0].get("name")})
    for key, expected in {"FC_TARGET_MCU": "RP2350B", "SERIALRX_UART": "SERIAL_PORT_PIOUART0",
            "SERIALRX_PROVIDER": "SERIALRX_CRSF", "GYRO_1_ALIGN": "CW180_DEG",
            "DEFAULT_MOTOR_PROTOCOL": "MOTOR_PROTOCOL_DSHOT600",
            "DEFAULT_DSHOT_TELEMETRY": "DSHOT_TELEMETRY_ON",
            "DEFAULT_CURRENT_METER_SCALE": "100", "DEFAULT_VOLTAGE_METER_SCALE": "110"}.items():
        assert macros.get(key, "").strip() == expected, key
    assert "ESC_SENSOR_UART" not in macros
    assert "FEATURE_ESC_SENSOR" not in macros.get("DEFAULT_FEATURES", "")
    assert "GYRO_CLKIN_PIN" not in macros
    assert "LED0_INVERTED" in macros, "D1 is active high"
    assert "BEEPER_INVERTED" in macros, "Q1 needs active-high push-pull"
    def net_for(ref, pin):
        matches = [net for net in native.findall("nets/net") if any(
            n.get("ref") == ref and n.get("pin") == pin for n in net.findall("node"))]
        assert len(matches) == 1, (ref, pin)
        return matches[0]
    assert net_for("D1", "1").get("name") == "GND", "LED cathode"
    assert net_for("D1", "2") is net_for("R16", "2"), "LED anode series path"
    assert net_for("R16", "1") is net_for("R15", "2"), "LED resistor chain"
    assert net_for("Q1", "2").get("name") == "GND", "N-MOS source"
    assert native.find("components/comp[@ref='Q1']/value").text == "AP1606"
    assert native.find("components/comp[@ref='U9']/value").text == "BMI270"
    assert native.find("components/comp[@ref='U2']/value").text.startswith("RP2354B")
    assert native.find("components/comp[@ref='R1']/value").text == "100k"
    assert native.find("components/comp[@ref='R2']/value").text == "10k"
    return findings

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    if not __debug__:
        raise RuntimeError("Run without Python -O; this verifier requires its assertions")
    raw = gzip.decompress((BOARD / "validation/schematic.net.xml.gz").read_bytes())
    assert hashlib.sha256(raw).hexdigest() == VERSIONS["native_export_uncompressed_sha256"]
    for name, key in [("OpenFC.kicad_pcb", "native_board_sha256"),
                      ("OpenFC.kicad_sch", "native_schematic_sha256")]:
        assert hashlib.sha256((BOARD / "hardware" / name).read_bytes()).hexdigest() == VERSIONS[key]
    native = ET.fromstring(raw)
    source = (PACKAGE / "configs/OPENFC_LITE_REV2_LW1/config.h").read_text()
    findings = check(source, native)
    controls = {}
    for label, wrong in {
        "wrong_led_polarity": source.replace("#define LED0_INVERTED", "// absent LED inversion"),
        "wrong_beeper_polarity": source.replace("#define BEEPER_INVERTED", "// absent beeper inversion"),
        "historical_motor_rework": source.replace("MOTOR1_PIN           PA31", "MOTOR1_PIN           PA21"),
        "historical_uart_rework": source.replace("UART0_TX_PIN         PA0", "UART0_TX_PIN         PA16"),
        "wrong_receiver_connector": source.replace("SERIAL_PORT_PIOUART0", "SERIAL_PORT_UART1"),
        "invented_serial_esc_telemetry": source + "\n#define ESC_SENSOR_UART SERIAL_PORT_PIOUART1\n",
        "swapped_gyro_bus_direction": source.replace("SPI0_SDO_PIN         PA19", "SPI0_SDO_PIN         PA20"),
    }.items():
        assert wrong != source
        try:
            check(wrong, native)
        except AssertionError as error:
            controls[label] = {"rejected": True, "reason": str(error) or "Forbidden serial ESC telemetry definition"}
        else:
            raise AssertionError(f"Negative control incorrectly passed: {label}")
    receipt = {"status": "pass", "native_board_sha256": VERSIONS["native_board_sha256"],
        "native_netlist_sha256": hashlib.sha256(raw).hexdigest(),
        "config_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "pin_checks": findings, "negative_controls": controls}
    text = json.dumps(receipt, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")

if __name__ == "__main__":
    main()
