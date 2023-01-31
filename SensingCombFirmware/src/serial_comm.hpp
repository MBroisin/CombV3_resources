#include <Arduino.h>
#include <board_config.hpp>

#define SERIAL_ACTIVE           1
#define SERIAL_INACTIVE         0


//#define TEST_BUFFERING
#define ASCII_0     48
#define ASCII_1     49
#define ASCII_2     50
#define ASCII_3     51
#define ASCII_4     52
#define ASCII_5     53
#define ASCII_6     54
#define ASCII_7     55
#define ASCII_8     56
#define ASCII_9     57
#define ASCII_CR    13
#define ASCII_LF    10

void serial_print(String str);
void serial_write(uint8_t* bytes, uint16_t bytes_size);
void serial_writeln(void);
void serial_println(String str);
void serial_start(void);