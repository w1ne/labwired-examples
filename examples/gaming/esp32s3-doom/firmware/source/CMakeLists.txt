cmake_minimum_required(VERSION 3.16)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(doom-s3)

# The shareware IWAD is flashed into its own raw partition and memory-mapped at
# runtime, so lumps are read straight out of flash with no PSRAM copy.
esptool_py_flash_target_image(flash "wad" "0x410000" "${CMAKE_CURRENT_LIST_DIR}/wad/doom1.wad")
