//
// Turn the DevKit's addressable RGB LED off and keep it off.
//
// The WS2812 latches its last colour and holds it with no MCU involvement, so
// whatever the factory demo left in it stays lit forever - our firmware never
// touches the pin, which is exactly why the LED does not go out on its own.
// One all-zero frame at boot clears it.
//
// Bit timing is what makes this work: a WS2812 reads a ~0.4 us high / ~0.85 us
// low pulse as a zero bit, and 24 of them mean black. That is far too fine for
// a bit-banged delay loop, so it goes out through RMT hardware.
//

#include "driver/rmt_encoder.h"
#include "driver/rmt_tx.h"
#include "esp_log.h"

#include "doom_esp32.h"

static const char *TAG = "board_led";

// ESP32-S3-DevKitC-1 v1.0 wires the RGB LED to GPIO48; v1.1 moved it to
// GPIO38. GPIO38 is the panel's RST line here, so only 48 is driven.
#define BOARD_RGB_LED_GPIO 48

#define RMT_RESOLUTION_HZ 10000000  // 0.1 us per tick

void board_led_off(void)
{
    rmt_channel_handle_t channel = NULL;
    rmt_encoder_handle_t encoder = NULL;
    rmt_symbol_word_t bits[24];
    esp_err_t err;

    rmt_tx_channel_config_t tx_config = {
        .gpio_num = BOARD_RGB_LED_GPIO,
        .clk_src = RMT_CLK_SRC_DEFAULT,
        .resolution_hz = RMT_RESOLUTION_HZ,
        .mem_block_symbols = 64,
        .trans_queue_depth = 4,
    };

    rmt_copy_encoder_config_t encoder_config = {};

    rmt_transmit_config_t tx_opts = {
        .loop_count = 0,
    };

    err = rmt_new_tx_channel(&tx_config, &channel);

    if (err != ESP_OK)
    {
        ESP_LOGW(TAG, "rmt_new_tx_channel failed: %s", esp_err_to_name(err));
        return;
    }

    if (rmt_new_copy_encoder(&encoder_config, &encoder) != ESP_OK ||
        rmt_enable(channel) != ESP_OK)
    {
        ESP_LOGW(TAG, "could not bring the RMT channel up");
        return;
    }

    // 24 zero bits = G0 R0 B0.
    for (int i = 0; i < 24; ++i)
    {
        bits[i].level0 = 1;
        bits[i].duration0 = 4;   // 0.4 us high
        bits[i].level1 = 0;
        bits[i].duration1 = 9;   // 0.9 us low
    }

    if (rmt_transmit(channel, encoder, bits, sizeof(bits), &tx_opts) == ESP_OK)
    {
        rmt_tx_wait_all_done(channel, 100);
        ESP_LOGI(TAG, "RGB LED on GPIO%d cleared", BOARD_RGB_LED_GPIO);
    }

    // Release the channel: the LED holds black on its own and Doom should not
    // pay for an RMT channel it will never use again.
    rmt_disable(channel);
    rmt_del_encoder(encoder);
    rmt_del_channel(channel);
}
