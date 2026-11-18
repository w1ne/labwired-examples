#!/bin/bash
set +e
export PATH=/home/andrii/.nvm/versions/node/v22.23.4/bin:$PATH
cd /data/worktrees/kernelcad-collab-project-assets-20261118/product-web
node --import tsx /data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/oled-native-sweep-controls.mts > /data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/sweep-controls.log 2>&1
printf '%s\n' "$?" > /data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/sweep-controls.exit
node --import tsx /data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/oled-native-linear-controls.mts > /data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/linear-controls.log 2>&1
printf '%s\n' "$?" > /data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/linear-controls.exit
node --import tsx /data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/oled-native-tool-controls.mts > /data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/tool-controls.log 2>&1
printf '%s\n' "$?" > /data/worktrees/labwired-examples-oled-handedness-20261118/examples/displays/esp32c3-oled/cad/verification/handedness/path/tool-controls.exit
