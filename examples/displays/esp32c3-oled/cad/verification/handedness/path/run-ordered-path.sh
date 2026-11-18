#!/bin/bash
set +e
export PATH=/home/andrii/.nvm/versions/node/v22.23.4/bin:$PATH
cd /data/worktrees/kernelcad-collab-project-assets-20261118/product-web
node --import tsx /data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/oled-ordered-complete-native-path.mts
code=$?
printf '%s\n' "$code" > /data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/ordered-path.exit
exit "$code"
