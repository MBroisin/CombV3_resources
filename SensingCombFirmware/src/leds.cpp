#include <leds.hpp>
#include <serial_comm.hpp>

#if defined(BOARD1)
static const uint8_t V_LEDS[NB_LEDS] = {LED1, LED2};
static const uint8_t IR_LEDS[NB_IR_LEDS] = {IR1, IR2, IR3, IR4};
#elif defined(BOARD2)
static const uint8_t V_LEDS[NB_LEDS] = {};
static const uint8_t IR_LEDS[NB_IR_LEDS] = {IR1, IR2};
#else
static const uint8_t V_LEDS[NB_LEDS] = {};
static const uint8_t IR_LEDS[NB_IR_LEDS] = {};
#endif

void leds_init(){
    for (int i=0; i<NB_IR_LEDS; i++){
        pinMode(IR_LEDS[i], OUTPUT);
    }
    for (int i=0; i<NB_LEDS; i++){
        pinMode(V_LEDS[i], OUTPUT);
    }
}

void set_vled(uint8_t led_number, uint8_t value){
    if (led_number >= NB_LEDS){
        return;
    }
    if (value !=0 && value != 1){
        if (digitalRead(V_LEDS[led_number])){
            digitalWrite(V_LEDS[led_number], LOW);
        } else {
            digitalWrite(V_LEDS[led_number], HIGH);
        }
    } else {
        digitalWrite(V_LEDS[led_number], value);
    }
}

void set_irled(uint8_t led_number, uint8_t value){
    if (led_number >= NB_IR_LEDS){
        return;
    }
    if (value !=0 && value != 1){
        if (digitalRead(IR_LEDS[led_number])){
            digitalWrite(IR_LEDS[led_number], LOW);
        } else {
            digitalWrite(IR_LEDS[led_number], HIGH);
        }
    } else {
        digitalWrite(IR_LEDS[led_number], value);
    }
}

void send_irleds_status(unsigned long ts){
    uint8_t status_buf[LED_BUFFER_SIZE] = {0};

#ifdef BOARD1
    status_buf[0] = 0b00000000;
#elif defined(BOARD2)
    status_buf[0] = 0b11111111;
#endif

    status_buf[1] = ((ts & 0xff000000) >> 24);
    status_buf[2] = ((ts & 0x00ff0000) >> 16);
    status_buf[3] = ((ts & 0x0000ff00) >> 8);
    status_buf[4] = ((ts & 0x000000ff) >> 0);

    for(int i=0; i<NB_IR_LEDS; i++){
        status_buf[i+LED_OVERHEAD_SIZE] = ((uint8_t)(digitalRead(IR_LEDS[i])==HIGH));
    }
    serial_write(status_buf, LED_BUFFER_SIZE);
    serial_writeln();
}