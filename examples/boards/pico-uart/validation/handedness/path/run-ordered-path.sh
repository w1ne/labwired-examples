#!/bin/bash
set +e
export PATH=/home/andrii/.nvm/versions/node/v22.23.4/bin:$PATH
cd /data/worktrees/kernelcad-collab-project-assets-20261118/product-web
node --import tsx /data/worktrees/labwired-examples-pico-handedness-20261118/examples/boards/pico-uart/validation/handedness/path/pico-ordered-complete-native-path.mts
printf '%s\n' "$?" > /data/worktrees/labwired-examples-pico-handedness-20261118/examples/boards/pico-uart/validation/handedness/path/ordered-path.exit
