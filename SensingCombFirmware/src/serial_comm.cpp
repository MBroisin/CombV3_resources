#include <serial_comm.hpp>

static uint8_t serial_active = SERIAL_INACTIVE;


void serial_print(String str){
    if (serial_active){Serial.print(str);}
}

void serial_write(uint8_t* bytes, uint16_t bytes_size){
    if (serial_active){Serial.write(bytes, bytes_size);}
}

void serial_writeln(){
    uint8_t new_line[2] = {ASCII_CR, ASCII_LF};
    serial_write(new_line, 2);
}

void serial_println(String str){
    if (serial_active){Serial.println(str);}
}

void serial_start(){
    /*while(!Serial){
        delay(50);
    }*/

    Serial.begin(230400);
    Serial.println("Welcome.");

    serial_active = SERIAL_ACTIVE;
}