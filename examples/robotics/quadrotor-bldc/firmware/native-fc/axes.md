# BMI270 and airframe axes

The configured `CW180_DEG` transform follows the populated U9 orientation
and the declared camera-forward assembly. It is based on the native pads,
the Bosch package drawing and the pinned driver. It still needs physical
six-direction motion qualification on the assembled device.

## Coordinate authority

The native KiCad board places U9 at editor coordinates (160.17,83.33) mm,
rotation 180° on F.Cu. Pad1 is at (159.00,82.58), pad4 at
(159.00,84.08), and pads12/13/14 at (160.67/160.17/159.67,82.41).
Those independent pad locations identify the package orientation; the
silkscreen text is not used as the axis authority.

The mechanical model retains the native STEP world: +X is native editor+X,
+Y is native editor−Y and +Z points above the populated face. It uses a
translation for registration, with no board rotation or reflection. The
camera supports are at CAD Y=−58 mm. The assembly defines forward=−CADY,
left=+CADX and up=+CADZ. The frame is right-handed.

[Bosch BST-BMI270-DS000-08, rev 1.6, March 2026](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf),
printed pages 143–144, identifies the package pins and sensing axes. The exact
PDF has SHA256
`0dab40659d3a8598af76a0b2da1fd8a216aeb87254541632c89145f974694af7`.
The two reviewed page images are retained in `validation/`.

| Sensor axis | Direction in native CAD | After CW180 in the body frame |
| --- | --- | --- |
| +X | +CADY | negative forward |
| +Y | −CADX | negative left |
| +Z | +CADZ | up |

Equivalently, for a physical vector expressed in CAD axes, the raw sensor
components are `(CADY, −CADX, CADZ)`. The pinned BMI270 driver preserves raw
X/Y/Z order. `boardalignment.c` applies CW180 as `(-X, -Y, +Z)`, producing
`(-CADY, +CADX, +CADZ)`: forward, left, up. This agrees with the
[Betaflight orientation convention](https://betaflight.com/docs/wiki/guides/current/Flight-Controller-Orientation).
An independent source-and-pad review reached the same registration.

## Motor order

The native connector order stays M1..M4 = GPIO31,30,29,28. For the declared
forward direction, the standard quad-X positions are M1 rear-right
(CAD−X,+Y), M2 front-right (CAD−X,−Y), M3 rear-left (CAD+X,+Y), and M4
front-left (CAD+X,−Y). The package changes neither the copper nets nor the
firmware motor numbering to hide an assembly-label error. The ESC and
mechanical package own the matching wire and rotor labels.

## Bench acceptance

A known positive translation or rotation about each declared body axis must
produce the corresponding reported axis and sign. Check both positive and
negative directions, then return the board to its level rest pose. Confirm
motor identity and spin direction separately with propellers removed.
Sensor drawing registration establishes the nominal mapping. It does not
measure assembly errors, live offsets, vibration or control stability.
