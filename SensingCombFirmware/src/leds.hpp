#include <board_config.hpp>
#include <Arduino.h>

#if defined(BOARD1)
#define NB_IR_LEDS      4
#define NB_LEDS         2
#define IR1             16
#define IR2             17
#define IR3             18
#define IR4             19
#define LED1            20
#define LED2            21
#elif defined(BOARD2)
#define NB_IR_LEDS      2
#define NB_LEDS         0
#define IR1             16
#define IR2             17
#else
#define NB_IR_LEDS      0
#define NB_LEDS         0
#endif

#define LED_OVERHEAD_SIZE       5
#define LED_DATA_SIZE           4
#define LED_BUFFER_SIZE         (LED_OVERHEAD_SIZE+LED_DATA_SIZE)

void leds_init(void);
void set_vled(uint8_t led_number, uint8_t value);
void set_irled(uint8_t led_number, uint8_t value);
void send_irleds_status(unsigned long ts);