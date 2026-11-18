# Upstream doomgeneric (ozkl), minus every platform backend. The ESP32-S3
# backend (DG_Init / DG_DrawFrame / DG_GetKey / ...) lives in main/.
#
# w_file_stdc.c is deliberately NOT built: w_file_flash.c replaces it and
# hands doomgeneric a memory-mapped WAD, so W_CacheLumpNum returns pointers
# straight into flash instead of copying lumps into RAM.

set(DOOM_SRCS
    dummy.c am_map.c doomdef.c doomstat.c dstrings.c d_event.c d_items.c
    d_iwad.c d_loop.c d_main.c d_mode.c d_net.c f_finale.c f_wipe.c g_game.c
    hu_lib.c hu_stuff.c info.c i_cdmus.c i_endoom.c i_joystick.c i_scale.c
    i_sound.c i_system.c i_timer.c memio.c m_argv.c m_bbox.c m_cheat.c
    m_config.c m_controls.c m_fixed.c m_menu.c m_misc.c m_random.c p_ceilng.c
    p_doors.c p_enemy.c p_floor.c p_inter.c p_lights.c p_map.c p_maputl.c
    p_mobj.c p_plats.c p_pspr.c p_saveg.c p_setup.c p_sight.c p_spec.c
    p_switch.c p_telept.c p_tick.c p_user.c r_bsp.c r_data.c r_draw.c
    r_main.c r_plane.c r_segs.c r_sky.c r_things.c sha1.c sounds.c statdump.c
    st_lib.c st_stuff.c s_sound.c tables.c v_video.c wi_stuff.c w_checksum.c
    w_file.c w_main.c w_wad.c z_zone.c i_input.c i_video.c doomgeneric.c
    w_file_flash.c
)

idf_component_register(
    SRCS ${DOOM_SRCS}
    INCLUDE_DIRS "."
    REQUIRES esp_timer
    LDFRAGMENTS "linker.lf"
)

target_compile_definitions(${COMPONENT_LIB} PUBLIC
    NORMALUNIX
    LINUX
    DOOMGENERIC_RESX=320
    DOOMGENERIC_RESY=200
)

# 1993 C. It compiles clean enough to run, not clean enough to read the log.
target_compile_options(${COMPONENT_LIB} PRIVATE
    -Wno-all
    -w
    -fno-strict-aliasing
)
