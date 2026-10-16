# Step illustrations (original)

Flat pictograms drawn for this project and released under **CC0 1.0** by the team. They are used where no
openly licensed picture was available. Each SVG here is the source of the matching `frontend/public/steps/{step_id}.webp`.

| Step | Picture |
|---|---|
| `unr_s2` | Kneel beside them, tap the shoulders and speak loudly |
| `unr_s3` | Look at the chest for breathing (with the 10-second timer) |
| `ha_s2` | Sitting still, supported against a wall |
| `burns_fire_s1` | Stop, drop and roll |
| `burns_fire_s2` | Burn cooled under running water (also used for `burns_chem_s4`) |
| `burns_fire_s5` | Burn covered loosely with cling film |
| `burns_elec_s1` | Power switched off at the main switch |
| `bite_dog_s2` | Wound washed under running water with soap |

## Animations (`frontend/public/steps/anim/`)

| Step | Movement | Timing |
|---|---|---|
| `unr_a4` | Straight arms, shoulders over the hands, hinging at the hips; chest pushed down and allowed to rise fully | 110 per minute (60/110 s per push), the CPR pacer rate |
| `ch_s4` | Person leaning forward, supported at the chest; heel of the hand strikes between the shoulder blades | 5 blows, one per second, then a 1-second pause |
| `ch_s5` | Helper behind, fist just above the belly button, sharp pull inwards and upwards | 5 thrusts, one per second, then a 1-second pause |

They are made by `src/anim.py` as SVG files with CSS `@keyframes`, and stop moving under `prefers-reduced-motion`.
The movement is illustrative: the depth of a compression is not drawn to scale.

Every picture is marked `verified: false`. The situation owner must check that it matches the step and the source
guideline before the demo, exactly as for the step text (see `docs/VERIFY.md`).

To redraw: `pip install cairosvg pillow`, then run any script in `src/` from that folder (for example `python cool.py`).
Rename the output to the step id and copy the `.webp` to `frontend/public/steps/`.
