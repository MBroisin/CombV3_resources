#include <SPI.h>
#include <board_config.hpp>
#include <serial_comm.hpp>

/* BOARD RELATED DEFINES */
#if defined(BOARD1)
#define NB_ACCELS       5
#define CSPIN1          4
#define CSPIN2          5
#define CSPIN3          6
#define CSPIN4          7
#define CSPIN5          8
#define INTPIN1         2
#define INTPIN2         3
#define INTPIN3         9
#define INTPIN4         10
#define INTPIN5         15

#define ACC1            0
#define ACC2            1
#define ACC3            2
#define ACC4            3
#define ACC5            4

#define ACC1_ID         1
#define ACC2_ID         2
#define ACC3_ID         3
#define ACC4_ID         4
#define ACC5_ID         5
#elif defined(BOARD2)
#define NB_ACCELS       5
#define CSPIN1          4
#define CSPIN2          5
#define CSPIN3          6
#define CSPIN4          7
#define CSPIN5          8
#define INTPIN1         2
#define INTPIN2         3
#define INTPIN3         9
#define INTPIN4         10
#define INTPIN5         15

#define ACC6            0
#define ACC7            1
#define ACC8            2
#define ACC9            3
#define ACC10           4

#define ACC6_ID         6
#define ACC7_ID         7
#define ACC8_ID         8
#define ACC9_ID         9
#define ACC10_ID        10

#else
#define NB_ACCELS       2
#define CSPIN1          9
#define CSPIN2          10
#define INTPIN1         3
#define INTPIN2         2

#define ACC1            0
#define ACC2            1

#define ACC1_ID         1
#define ACC2_ID         2
#endif

/* ACCELS CONFIGURATION */
#define G         9.81

#define SPI_READ 0x80
#define SPI_WRITE 0x00 

// #define FAKE_DATA
// #define BUFFERING
#define STREAM_MODE
#define RESET_UNTIL_ACTIVE
#define ALL_AXIS

#ifdef STREAM_MODE
#define BUF_SIZE    48        // KX132 buffer size (must be <=86)
#else
#define BUF_SIZE    85
#endif

#define BUF_SIZE_8          (2*BUF_SIZE)
#define DATA_PACK           6         // x_lsb, x_msb, y_lsb ...
#define OVERHEAD_SIZE       7
#define TRANSMIT_BUF_SIZE   (BUF_SIZE_8+OVERHEAD_SIZE)

#define CNTL1addr       0x1b
#define BUFCNTL1addr    0x5E
#define BUFCNTL2addr    0x5F
#define ODCNTLaddr      0x21
#define IC1addr         0x22
#define IC4addr         0x25
#define BUFFILLaddr     0x60
#define INS2addr        0x17
#define WHO_AM_I        0x13
#define COTRaddr        0x12
#define WHO_AM_I_val    0x3D

#define ODCNTL_12       0x4         /* SPEEDS */
#define ODCNTL_25       0x5
#define ODCNTL_50       0x6
#define ODCNTL_100      0x7
#define ODCNTL_200      0x8
#define ODCNTL_400      0x9
#define ODCNTL_800      0xa
#define ODCNTL_1600     0xb
#define ODCNTL_3200     0xc
// Effective speed
#define ODCNTL_SPEED    ODCNTL_1600

#define DELAY_50SAMPLES_12      3840 // 3840 initially (50 samples)
#define DELAY_50SAMPLES_25      1920
#define DELAY_50SAMPLES_50      960
#define DELAY_50SAMPLES_100     480
#define DELAY_50SAMPLES_200     240
#define DELAY_50SAMPLES_400     120
#define DELAY_50SAMPLES_800     60
#define DELAY_50SAMPLES_1600    30
#define DELAY_50SAMPLES_3200    15
#define DELAY_40SAMPLES_12      3100
#define DELAY_70SAMPLES_12      5600

#define TIMER0_INTERVAL_MS      (DELAY_50SAMPLES_12/(0b1<<(ODCNTL_SPEED-ODCNTL_12)))

#define CNTL1_INT       0b11100000      // INTERRPUT MODE
#define IC4_INT         0b00010000
#define IC1_INT         0b00111000

#define CNTL1_BUF2G     0b11000000
#define CNTL1_BUF4G     0b11001000
#define CNTL1_BUF       CNTL1_BUF2G     // BUFFER MODE
#define BUF_CNTL1       BUF_SIZE        // Define the amount of data stored before interrupting
#define BUF_CNTL2_FIFO  0b11100000
#define BUF_CNTL2_TRIG  0b11100010

#ifdef STREAM_MODE
#define BUF_CNTL2       0b11100001      // buffer enable + buffer resolution + buffer interrupt enable
#define BUF_CNTL2_FIFO  0b11100000      // buffer enable + buffer resolution + buffer interrupt enable
#define IC4_BUF         0b00100000      // Watermark interrupt (int when buffer filled more than a threshold given by BUF_CNTL1)
#else
#define BUF_CNTL2       0b11100000
#define IC4_BUF         0b00100000      // Watermark interrupt (int when buffer filled more than a threshold given by BUF_CNTL1)
#endif

#define IC1_BUF         0b00111000      // Physical interrupt enable

#define CNTL1_DEF       0b11000000      // DEFAULT MODE
#define IC4_DEF         0b00000000
#define IC1_DEF         0b00010000

#define XOUT_L    0x08
#define XOUT_H    0x09
#define YOUT_L    0x0a
#define YOUT_H    0x0b
#define ZOUT_L    0x0c
#define ZOUT_H    0x0d
#define BUF_OUT   0x63

#define AXIS_X              0
#define AXIS_Y              1
#define AXIS_Z              2
#define AXIS_OF_INTEREST    AXIS_Z

#define COUNT_MAX       5
#define USB_BUFFER_SIZE (COUNT_MAX*TRANSMIT_BUF_SIZE)
#define BEGIN_SEQ       "ch> "
#define BUFFER1         0
#define BUFFER2         1

#define ACC_ENABLED     1
#define ACC_DISABLED    0

#define DELAY_INIT  100
#define BUS_BUSY    0
#define BUS_FREE    1

void accelerometers_init(void);
void accelerometers_enable(uint8_t AccID);
void accelerometers_disable(uint8_t AccID);
void accelerometers_set_axis(uint8_t AccID, uint8_t axis);
