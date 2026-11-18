/* SPDX-License-Identifier: GPL-3.0-or-later
 * Reuse the pinned master's real-iolinki integration fixture. It exchanges
 * encoded bytes between the actual two stacks; its synthetic PHY callbacks
 * deliberately do not prove electrical/timing behaviour or a multi-MCU boot.
 */
#include "station_profile.h"
#define main upstream_protocol_matrix_main
#include "test_master_real_iolinki_device.c"
#undef main

static void test_physical_profile_bytes(void **state) {
    (void)state;
    assert_int_equal(STATION_MASTER_MSEQ_TYPE, IOLINK_MASTER_M_SEQ_TYPE_2_1);
    assert_int_equal(STATION_DEVICE_MSEQ_TYPE, IOLINK_M_SEQ_TYPE_2_1);
    assert_int_equal(STATION_PD_INPUT_BYTES, 1);
    assert_int_equal(STATION_PD_OUTPUT_BYTES, 0);
    assert_int_equal(STATION_BAUDRATE, IOLINK_BAUDRATE_COM2);
    const uint8_t inputs[] = {0x00, 0xff, 0xa5, 0x3c};
    for (size_t i = 0; i < sizeof(inputs); ++i) {
        print_message("TYPE_2_1 / COM2 / input=%02x / output=none\n", inputs[i]);
        assert_master_real_stack_profile(STATION_MASTER_MSEQ_TYPE, STATION_PD_INPUT_BYTES,
                                         STATION_PD_OUTPUT_BYTES, inputs[i],
                                         "physical station profile");
    }
}
int main(void) {
    const struct CMUnitTest tests[] = {
        cmocka_unit_test(test_physical_profile_bytes),
    };
    return cmocka_run_group_tests(tests, NULL, NULL);
}
