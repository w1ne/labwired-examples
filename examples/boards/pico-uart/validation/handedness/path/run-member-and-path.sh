#!/bin/bash
set +e
export PATH=/home/andrii/.nvm/versions/node/v22.23.4/bin:$PATH
cd /data/worktrees/kernelcad-collab-project-assets-20261118/product-web
node --import tsx /data/worktrees/labwired-examples-pico-handedness-20261118/examples/boards/pico-uart/validation/handedness/path/pico-native-member-controls.mts > /data/worktrees/labwired-examples-pico-handedness-20261118/examples/boards/pico-uart/validation/handedness/path/member-controls.log 2>&1
control_status=$?
printf '%s\n' "$control_status" > /data/worktrees/labwired-examples-pico-handedness-20261118/examples/boards/pico-uart/validation/handedness/path/member-controls.exit
if [ "$control_status" -ne 0 ]; then exit "$control_status"; fi
bash /data/worktrees/labwired-examples-pico-handedness-20261118/examples/boards/pico-uart/validation/handedness/path/run-ordered-path.sh > /data/worktrees/labwired-examples-pico-handedness-20261118/examples/boards/pico-uart/validation/handedness/path/ordered-path.log 2>&1
