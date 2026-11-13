# Photorealistic PCB rendering (reusable for all populated PCB GLBs)

The renderer uses actual PCB geometry and footprint models from KiCad or
LabWired. It applies physically based materials, softbox lights, grounded
shadows and tone mapping. It does not invent missing packages or tracks.

Run from the repository root:

    PYTHONPATH=/home/andrii/scratch/blender-python-deps:/usr/lib/python3.12/lib-dynload blender -b --python scripts/pcb_render/render.py -- --input examples/robotics/quadrotor-bldc/hardware/esc-4in1/fabrication-review/esc-board-populated.glb --profile scripts/pcb_render/quadrotor-profile.json --output /tmp/quad-photoreal.png --engine cycles --samples 48

For other PCB designs, run the same script with the appropriate GLB input.
Supply a different profile if material names are anonymous. Do not reuse
mat_N mappings across different source exports. Semantic material names
(solder_mask, fr4, tin, gold, epoxy, ceramic) work without any profile.
The output comes with a SHA-256 provenance receipt and imported mesh count.

This produces a render, not a photograph or manufacturability certificate.
A missing 3D model remains missing. Verify mechanical model coverage before
promotional release.

## Quality gate

Use --strict for release candidates. This rejects anonymized mesh identity or
materials without identified physical roles. The quadrotor GLB imports 214 meshes
with non-semantic node names. Its result therefore has quality_verdict =
review_required and photoreal_validated = false, even when its material profile
covers all 17 imported materials.

This gate is deliberate. Basic shapes with improved shaders are not physical
package models. Realistic component package geometry, exact reference designators,
correct STEP orientation, soldermask apertures, silkscreen, pad plating and proper
height are required from the upstream export for production quality.

For a catalog-wide pipeline: KiCad import -> complete footprint/3D-model coverage
-> semantic material tagging -> source-grounded GLB -> Blender PBR render ->
provenance and quality gate. The generic renderer is implemented here. Automated
model coverage and production app wiring remain separate integration tasks.

The Blender image export requires NumPy in Blender's Python path. On the work-1
host, the Blender 4.0.2 Python runtime also needs the distro lib-dynload path
to resolve _contextvars. Cycles denoising is disabled on the current host
because its build lacks OpenImageDenoiser; use higher samples for final output.
