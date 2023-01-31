#include <SPI.h>


#define G         9.81

#define SPI_READ 0x80
#define SPI_WRITE 0x00 

#define STREAM_MODE

#ifdef STREAM_MODE
#define BUF_SIZE    50        // KX132 buffer size (must be <=86)
#else
#define BUF_SIZE    85
#endif

#define BUF_SIZE_8  (2*BUF_SIZE)
#define DATA_PACK   6         // x_lsb, x_msb, y_lsb ...

#define CNTL1addr     0x1b
#define BUFCNTL1addr  0x5E
#define BUFCNTL2addr  0x5F
#define ODCNTLaddr    0x21
#define IC1addr       0x22
#define IC4addr       0x25
#define BUFFILLaddr   0x60
#define INS2addr      0x17
#define WHO_AM_I      0x13

#define ODCNTL_12     0x4         /* SPEEDS */
#define ODCNTL_25     0x5
#define ODCNTL_50     0x6
#define ODCNTL_100    0x7
#define ODCNTL_200    0x8
#define ODCNTL_400    0x9
#define ODCNTL_800    0xa
#define ODCNTL_1600   0xb
#define ODCNTL_3200   0xc

// Effective speed
#define ODCNTL_SPEED  ODCNTL_800
 
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
#define AXIS_OF_INTEREST    AXIS_X

#define COUNT_MAX       5
#define USB_BUFFER_SIZE (COUNT_MAX*BUF_SIZE_8)
#define BEGIN_SEQ       "ch> "

//#define TEST_BUFFERING
#define ASCII_1     49
#define ASCII_2     50
#define ASCII_3     51
#define ASCII_4     52
#define ASCII_5     53
#define ASCII_6     54
#define ASCII_7     55
#define ASCII_8     56

#define BUS_BUSY    0
#define BUS_FREE    1

float getAcc(int axis, int CSpin);
void accels_init(void);
