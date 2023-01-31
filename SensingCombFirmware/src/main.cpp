#include <Arduino.h>
//#include <spi_comm.hpp>
#include <accelerometers.hpp>
#include <serial_comm.hpp>
#include <leds.hpp>

// #define DEBUG_SPI
// #define DEBUG_LEDS
// #define DEBUG_IR_LEDS

#define DELAY   5000

void setup() {

  serial_start();
  leds_init();
  accelerometers_init();

#ifdef BOARD2
  accelerometers_set_axis(ACC6, AXIS_Z);
  accelerometers_set_axis(ACC7, AXIS_Z);
  accelerometers_set_axis(ACC8, AXIS_Z);
  accelerometers_set_axis(ACC9, AXIS_Z);
  accelerometers_set_axis(ACC10, AXIS_Z);

  accelerometers_enable(ACC6);
  accelerometers_enable(ACC7);
  accelerometers_enable(ACC8);
  accelerometers_enable(ACC9);
  accelerometers_enable(ACC10);

#else
  accelerometers_set_axis(ACC1, AXIS_Z);
  accelerometers_set_axis(ACC2, AXIS_Z);
  accelerometers_set_axis(ACC3, AXIS_Z);
  accelerometers_set_axis(ACC4, AXIS_Z);
  accelerometers_set_axis(ACC5, AXIS_Z);

  accelerometers_enable(ACC1);
  accelerometers_enable(ACC2);
  accelerometers_enable(ACC3);
  accelerometers_enable(ACC4);
  accelerometers_enable(ACC5);

#endif
}

void loop() {
#ifdef DEBUG_SPI
  Serial.print("(");
  Serial.print(digitalRead(9));
  Serial.print(", ");
  Serial.print(digitalRead(10));
  Serial.println(")");
  delay(10); 
#elif defined(DEBUG_LEDS)
  set_vled(0, 0);
  set_vled(1, 1);
  for(int i=0; i<NB_IR_LEDS; ++i){
    set_irled(i, 0);
  }
  delay(DELAY);
  set_vled(0, 1);
  set_vled(1, 0);
  for(int i=0; i<NB_IR_LEDS; ++i){
    set_irled(i, 1);
  }
  delay(DELAY);

#elif defined(DEBUG_IR_LEDS)
  for(int i=0; i<NB_IR_LEDS; ++i){
    set_irled(i, 0);
  }
  delay(DELAY);
  for(int i=0; i<NB_IR_LEDS; ++i){
    set_irled(i, 1);
  }
  delay(DELAY);
#else 

  set_irled(0, 1);
  set_irled(1, 0);
  send_irleds_status(micros());
  delay(DELAY);

  set_irled(0, 1);
  set_irled(1, 1);
  send_irleds_status(micros());
  delay(DELAY);

  set_irled(0, 0);
  set_irled(1, 1);
  send_irleds_status(micros());
  delay(DELAY);

  set_irled(0, 1);
  set_irled(1, 1);
  send_irleds_status(micros());
  delay(DELAY);

  set_irled(0, 0);
  set_irled(1, 0);
  send_irleds_status(micros());
  delay(DELAY);
  /*for(int capt=0; capt<NB_ACCELS; capt++){
    delay(DELAY);
    serial_println("start");
    accelerometers_enable(capt);
    delay(DELAY);
    serial_println("stop");
    accelerometers_disable(capt);
  }*/
  
#endif
}