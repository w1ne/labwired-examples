# Routing input

`routing-base.kicad_pcb` is the fixed native output from the KiCad 10 / Freerouting 2.5.0 routing exchange. It is an intermediate input, not the accepted board. The final source applies explicit copper, topology, polarity and package corrections, then passes independent KiCad DRC.

The exact accepted starting board and original project rules are preserved under the verification evidence as `accepted-baseline/`. The original three missing nets were END_X, END_Y and Z_DIR. The routing input has all three closed; the deterministic patch sequence finishes the remaining escapes and applies the authorized electrical corrections.
