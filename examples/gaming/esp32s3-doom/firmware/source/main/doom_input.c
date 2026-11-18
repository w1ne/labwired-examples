//
// Serial keyboard for Doom.
//
// The panel has no buttons wired yet, so the console UART is the input device:
// every byte you type in the monitor becomes a Doom key-down, and a key-up is
// synthesised a short time later. That is enough to walk the menus, start a
// level and play, and it costs no GPIOs.
//
// Terminals send no key-up events at all, which is why the hold time exists:
// too short and you cannot walk, too long and the player slides after you stop
// typing. Terminal auto-repeat refreshes the hold while a key stays down.
//

#include <stdbool.h>
#include <string.h>

#if CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG
#include "driver/usb_serial_jtag.h"
#else
#include "driver/uart.h"
#endif
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "doom_esp32.h"
#include "doomkeys.h"

static const char *TAG = "doom_input";

#define KEY_HOLD_MS 140
#define EVENT_QUEUE_LEN 64
#define PENDING_RELEASES 12
#define UART_RX_BUF 512

typedef struct
{
    int pressed;
    unsigned char key;
} key_event_t;

typedef struct
{
    unsigned char key;
    int64_t due_us;
    bool active;
} pending_release_t;

static key_event_t s_queue[EVENT_QUEUE_LEN];
static volatile int s_head;
static volatile int s_tail;

static pending_release_t s_pending[PENDING_RELEASES];

static portMUX_TYPE s_lock = portMUX_INITIALIZER_UNLOCKED;

static void queue_push(int pressed, unsigned char key)
{
    int next;

    portENTER_CRITICAL(&s_lock);
    next = (s_head + 1) % EVENT_QUEUE_LEN;

    // Drop the newest event rather than overwrite an unread key-up: a lost
    // key-up leaves the player walking into a wall forever.
    if (next != s_tail)
    {
        s_queue[s_head].pressed = pressed;
        s_queue[s_head].key = key;
        s_head = next;
    }
    portEXIT_CRITICAL(&s_lock);
}

static bool queue_pop(key_event_t *out)
{
    bool got = false;

    portENTER_CRITICAL(&s_lock);
    if (s_tail != s_head)
    {
        *out = s_queue[s_tail];
        s_tail = (s_tail + 1) % EVENT_QUEUE_LEN;
        got = true;
    }
    portEXIT_CRITICAL(&s_lock);

    return got;
}

// Re-arm an existing hold instead of stacking a second one, so terminal
// auto-repeat reads as "still held" rather than a burst of down/up pairs.
static void schedule_release(unsigned char key)
{
    int64_t due = esp_timer_get_time() + (int64_t)KEY_HOLD_MS * 1000;
    int free_slot = -1;
    int i;

    portENTER_CRITICAL(&s_lock);
    for (i = 0; i < PENDING_RELEASES; ++i)
    {
        if (s_pending[i].active && s_pending[i].key == key)
        {
            s_pending[i].due_us = due;
            portEXIT_CRITICAL(&s_lock);
            return;
        }

        if (!s_pending[i].active && free_slot < 0)
        {
            free_slot = i;
        }
    }

    if (free_slot >= 0)
    {
        s_pending[free_slot].key = key;
        s_pending[free_slot].due_us = due;
        s_pending[free_slot].active = true;
    }
    portEXIT_CRITICAL(&s_lock);
}

static void expire_releases(void)
{
    int64_t now = esp_timer_get_time();
    unsigned char expired[PENDING_RELEASES];
    int count = 0;
    int i;

    portENTER_CRITICAL(&s_lock);
    for (i = 0; i < PENDING_RELEASES; ++i)
    {
        if (s_pending[i].active && now >= s_pending[i].due_us)
        {
            expired[count++] = s_pending[i].key;
            s_pending[i].active = false;
        }
    }
    portEXIT_CRITICAL(&s_lock);

    for (i = 0; i < count; ++i)
    {
        queue_push(0, expired[i]);
    }
}

static unsigned char map_byte(unsigned char c)
{
    switch (c)
    {
        case 'w': case 'W': return KEY_UPARROW;
        case 's': case 'S': return KEY_DOWNARROW;
        case 'a': case 'A': return KEY_LEFTARROW;
        case 'd': case 'D': return KEY_RIGHTARROW;
        case 'q': case 'Q': return KEY_STRAFE_L;
        case 'e': case 'E': return KEY_STRAFE_R;
        case 'f': case 'F': return KEY_FIRE;
        case ' ':           return KEY_USE;
        case '\r': case '\n': return KEY_ENTER;
        case 0x1b:          return KEY_ESCAPE;
        case '\t':          return KEY_TAB;
        case 0x08: case 0x7f: return KEY_BACKSPACE;
        case 'm': case 'M': return KEY_TAB;   // automap
        case 'p': case 'P': return KEY_PAUSE;
        default:
            // Weapon numbers, y/n prompts and the rest of ASCII go straight
            // through; Doom compares them as lower-case characters.
            if (c >= 'A' && c <= 'Z')
            {
                return (unsigned char)(c - 'A' + 'a');
            }
            if (c >= 0x20 && c < 0x7f)
            {
                return c;
            }
            return 0;
    }
}

// Arrow keys arrive as ESC '[' 'A'..'D'. Without this, every arrow press would
// read as an Escape and slam the menu open.
static unsigned char map_escape_sequence(unsigned char final)
{
    switch (final)
    {
        case 'A': return KEY_UPARROW;
        case 'B': return KEY_DOWNARROW;
        case 'C': return KEY_RIGHTARROW;
        case 'D': return KEY_LEFTARROW;
        default:  return 0;
    }
}

// This package uses the DevKitC-1 v1.0 CP2102 USB-to-UART bridge and UART0
// for both console and keyboard. The optional USB-Serial-JTAG build path
// below remains available for a separately configured native-USB build.
#if CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG

static void console_open(void)
{
    usb_serial_jtag_driver_config_t cfg = USB_SERIAL_JTAG_DRIVER_CONFIG_DEFAULT();

    cfg.rx_buffer_size = UART_RX_BUF;
    ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&cfg));
}

static int console_read(uint8_t *buf, size_t len, TickType_t wait)
{
    return usb_serial_jtag_read_bytes(buf, len, wait);
}

#else

static void console_open(void)
{
    uart_config_t cfg = {
        .baud_rate = 115200,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };

    // RX only: logging keeps using the driverless TX path.
    ESP_ERROR_CHECK(uart_driver_install(UART_NUM_0, UART_RX_BUF, 0, 0, NULL, 0));
    ESP_ERROR_CHECK(uart_param_config(UART_NUM_0, &cfg));
}

static int console_read(uint8_t *buf, size_t len, TickType_t wait)
{
    return uart_read_bytes(UART_NUM_0, buf, len, wait);
}

#endif

static void input_task(void *arg)
{
    uint8_t buf[64];
    enum { ST_PLAIN, ST_ESC, ST_CSI } state = ST_PLAIN;
    int64_t esc_seen_us = 0;

    (void)arg;

    for (;;)
    {
        int n = console_read(buf, sizeof(buf), pdMS_TO_TICKS(20));

        // A lone Escape is only an Escape once we know no '[' is following.
        if (state == ST_ESC && esp_timer_get_time() - esc_seen_us > 30000)
        {
            queue_push(1, KEY_ESCAPE);
            schedule_release(KEY_ESCAPE);
            state = ST_PLAIN;
        }

        for (int i = 0; i < n; ++i)
        {
            unsigned char c = buf[i];
            unsigned char key;

            switch (state)
            {
                case ST_PLAIN:
                    if (c == 0x1b)
                    {
                        state = ST_ESC;
                        esc_seen_us = esp_timer_get_time();
                        continue;
                    }
                    break;

                case ST_ESC:
                    state = (c == '[') ? ST_CSI : ST_PLAIN;
                    if (state == ST_CSI)
                    {
                        continue;
                    }
                    // Not a CSI after all: the Escape was real.
                    queue_push(1, KEY_ESCAPE);
                    schedule_release(KEY_ESCAPE);
                    break;

                case ST_CSI:
                    state = ST_PLAIN;
                    key = map_escape_sequence(c);
                    if (key != 0)
                    {
                        queue_push(1, key);
                        schedule_release(key);
                    }
                    continue;
            }

            key = map_byte(c);

            if (key != 0)
            {
                queue_push(1, key);
                schedule_release(key);
            }
        }
    }
}

void doom_input_init(void)
{
    console_open();

    xTaskCreatePinnedToCore(input_task, "doom_input", 3072, NULL, 6, NULL, 0);

    ESP_LOGI(TAG, "serial keys: WASD move, Q/E strafe, F fire, SPACE use, "
                  "ENTER select, ESC menu, M map, 1-7 weapons");
}

// --- doomgeneric hook -------------------------------------------------------

int DG_GetKey(int *pressed, unsigned char *key)
{
    key_event_t ev;

    expire_releases();

    if (!queue_pop(&ev))
    {
        return 0;
    }

    *pressed = ev.pressed;
    *key = ev.key;

    return 1;
}
