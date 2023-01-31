#include <accelerometers.hpp>
#include <leds.hpp>
#include <SAMDTimerInterrupt.h>
#include <SAMD_ISR_Timer.h> 

#if defined(BOARD1)
static const uint8_t CHIP_SELECTS[NB_ACCELS] = {CSPIN1, CSPIN2, CSPIN3, CSPIN4, CSPIN5};
static const uint8_t INTERRUPTS[NB_ACCELS] = {INTPIN1, INTPIN2, INTPIN3, INTPIN4, INTPIN5};
static uint8_t axis_to_read[NB_ACCELS] = {AXIS_Z, AXIS_Z, AXIS_Z, AXIS_Z, AXIS_Z};
static uint8_t acc_enables[NB_ACCELS] = {ACC_DISABLED};
static uint8_t ACC_IDS[NB_ACCELS] = {ACC1_ID, ACC2_ID, ACC3_ID, ACC4_ID, ACC5_ID};

#elif defined(BOARD2)
static const uint8_t CHIP_SELECTS[NB_ACCELS] = {CSPIN1, CSPIN2, CSPIN3, CSPIN4, CSPIN5};
static const uint8_t INTERRUPTS[NB_ACCELS] = {INTPIN1, INTPIN2, INTPIN3, INTPIN4, INTPIN5};
static uint8_t axis_to_read[NB_ACCELS] = {AXIS_Z, AXIS_Z, AXIS_Z, AXIS_Z, AXIS_Z};
static uint8_t acc_enables[NB_ACCELS] = {ACC_DISABLED};
static uint8_t ACC_IDS[NB_ACCELS] = {ACC6_ID, ACC7_ID, ACC8_ID, ACC9_ID, ACC10_ID};

#else
static const uint8_t CHIP_SELECTS[NB_ACCELS] = {CSPIN1, CSPIN2};
static const uint8_t INTERRUPTS[NB_ACCELS] = {INTPIN1, INTPIN2};
static uint8_t axis_to_read[NB_ACCELS] = {AXIS_Z, AXIS_Z};
static uint8_t acc_enables[NB_ACCELS] = {ACC_DISABLED};
static uint8_t ACC_IDS[NB_ACCELS] = {ACC1_ID, ACC2_ID};
#endif

static const uint8_t NUMBERS[10] = {ASCII_0, ASCII_1, ASCII_2, ASCII_3, ASCII_4, ASCII_5, ASCII_6, ASCII_7, ASCII_8, ASCII_9};
static uint8_t bus_acquirable = BUS_FREE;

#ifdef BUFFERING
static uint8_t buf_to_send1[USB_BUFFER_SIZE] = {0};
static uint8_t buf_to_send2[USB_BUFFER_SIZE] = {0};
static uint8_t bts = BUFFER1;
static uint8_t bts_count = 0;
#endif

SAMDTimer ITimer(TIMER_TC3); 
// SAMD_ISR_Timer ISR_Timer;

void extract_axis_bytes(uint8_t raw[], uint8_t* dat, uint8_t axis, uint8_t AccID, unsigned long ts){
    dat[0] = (ACC_IDS[AccID] << 4) + (axis);
    dat[1] = ODCNTL_SPEED;
    dat[2] = BUF_SIZE;
    dat[3] = ((ts & 0xff000000) >> 24);
    dat[4] = ((ts & 0x00ff0000) >> 16);
    dat[5] = ((ts & 0x0000ff00) >> 8);
    dat[6] = ((ts & 0x000000ff) >> 0);
    for (int i=OVERHEAD_SIZE; i<TRANSMIT_BUF_SIZE-1; i+=2){
        int ind = ((i-OVERHEAD_SIZE)/2)*DATA_PACK;

        dat[i] = raw[ind+axis*2+0];
        dat[i+1] = raw[ind+axis*2+1];
    }
}

#ifdef FAKE_DATA
void fake_axis_bytes(uint8_t raw[], uint8_t* dat, uint8_t axis, uint8_t AccID, unsigned long ts){
    // dat[0] = NUMBERS[AccID];
    // dat[1] = NUMBERS[axis];

    dat[0] = (AccID << 5) + (axis << 3) + ((USB_BUFFER_SIZE & 0x03ff) >> 8);
    dat[1] = (USB_BUFFER_SIZE & 0xff);

    // dat[2] = NUMBERS[((USB_BUFFER_SIZE & 0x0e00) >> 9)];
    // dat[3] = NUMBERS[((USB_BUFFER_SIZE & 0x01c0) >> 6)];
    // dat[4] = NUMBERS[((USB_BUFFER_SIZE & 0x0038) >> 3)];
    // dat[5] = NUMBERS[(USB_BUFFER_SIZE & 0x0007)];

    dat[2] = ((ts & 0xff000000) >> 24);
    dat[3] = ((ts & 0x00ff0000) >> 16);
    dat[4] = ((ts & 0x0000ff00) >> 8);
    dat[5] = ((ts & 0x000000ff) >> 0);

    dat[6] = ASCII_0;
    dat[7] = ASCII_0;
    dat[8] = ASCII_0;
    dat[9] = ASCII_0;
    dat[10] = ASCII_0;

    // for (int i=11; i<11+NB_ACCELS; i++){
    //     if (digitalRead(CHIP_SELECTS[i])){dat[i] = ASCII_1;} 
    //     else {dat[i] = ASCII_0;}
    // }
    for (int i=11+NB_ACCELS; i<TRANSMIT_BUF_SIZE; i++){dat[i] = NUMBERS[AccID];}
}
#endif

void writeRegister(byte reg, byte val, int CSpin) {
    bus_acquirable = BUS_BUSY;
    // take the chip select low to select the device:
    digitalWrite(CSpin, LOW);
    SPI.transfer(reg); //Send register location
    SPI.transfer(val);  //Send value to record into register
    digitalWrite(CSpin, HIGH);
    bus_acquirable = BUS_FREE;
}

unsigned int readRegister(byte reg, int bytesToRead, int CSpin) {
    unsigned int inByte = 0;   // incoming byte from the SPI
    unsigned int result = 0;   // result to return
    byte dataToSend = SPI_READ | reg;


    // take the chip select low to select the device:
    digitalWrite(CSpin, LOW);
    // send the device the register you want to read:
    SPI.transfer(dataToSend);
    // send a value of 0 to read the first byte returned:
    result = SPI.transfer(0x00);
    if (bytesToRead > 1) {
    inByte = SPI.transfer(0x00);
    result = result | (inByte << 8);
    }
    digitalWrite(CSpin, HIGH);
    return (result);
}

void readMultipleRegister(byte reg, int numBytes, uint8_t data[], int CSpin) {  
    byte dataToSend = SPI_READ | reg;
    // take the chip select low to select the device:
    bus_acquirable = BUS_BUSY;
    digitalWrite(CSpin, LOW);
    // send the device the register you want to read:
    SPI.transfer(dataToSend);
    data[0] = SPI.transfer(0x00);
    for(int i=1; i<numBytes; i++){
        data[i] = SPI.transfer(0x00);
    }
    // for (int i=0; i<numBytes; i+=2){
    //     uint16_t temp = data[i+1];
    //     temp = (temp << 8) | data[i]; 
    //     // serial_print(String(((float)temp)*4*9.81/65535));

    //     if (i%6 == 0){serial_print(" --- ");}
    //     serial_print(String(temp));
    //     serial_print(", ");
    // }
    digitalWrite(CSpin, HIGH);
    bus_acquirable = BUS_FREE;
}

void AccConfigBUF(int CSpin){
    writeRegister(CNTL1addr, 0x00, CSpin);
    writeRegister(ODCNTLaddr, ODCNTL_SPEED, CSpin);
    writeRegister(IC1addr, IC1_BUF, CSpin);
    writeRegister(IC4addr, IC4_BUF, CSpin);
    writeRegister(BUFCNTL1addr, BUF_CNTL1, CSpin);
    writeRegister(BUFCNTL2addr, BUF_CNTL2, CSpin);
    // writeRegister(CNTL1addr, CNTL1_BUF, CSpin);
}

void startAccelBUF(int CSpin){
    while(!bus_acquirable){;}
    noInterrupts();
    writeRegister(CNTL1addr, CNTL1_BUF, CSpin);
    interrupts();
}

void stopAccelBUF(int CSpin){
    while(!bus_acquirable){;}
    noInterrupts();
    writeRegister(CNTL1addr, 0x00, CSpin);
    interrupts();
}

void callback_gatherAccs(){
    unsigned long time_stamp = micros();
    // serial_println(String(time_stamp));
    static uint8_t acc_dat[BUF_SIZE*DATA_PACK];
    static uint8_t data_axis[TRANSMIT_BUF_SIZE];

    for (int chip=0; chip<NB_ACCELS; chip++){
        if (acc_enables[chip]){
            // serial_print("coucou ");
            uint8_t CSpin = CHIP_SELECTS[chip];
            // serial_println(String(chip));
            readMultipleRegister(BUF_OUT, BUF_SIZE*DATA_PACK, acc_dat, CSpin);
            
#ifdef ALL_AXIS
            extract_axis_bytes(acc_dat, data_axis, AXIS_X, chip, time_stamp);
            serial_write(data_axis, TRANSMIT_BUF_SIZE);
            serial_writeln();

            extract_axis_bytes(acc_dat, data_axis, AXIS_Y, chip, time_stamp);
            serial_write(data_axis, TRANSMIT_BUF_SIZE);
            serial_writeln();

            extract_axis_bytes(acc_dat, data_axis, AXIS_Z, chip, time_stamp);
            serial_write(data_axis, TRANSMIT_BUF_SIZE);
            serial_writeln();

#else
            extract_axis_bytes(acc_dat, data_axis, axis_to_read[chip], chip, time_stamp);
            serial_write(data_axis, TRANSMIT_BUF_SIZE);
            serial_writeln();
#endif

#ifdef BUFFERING
            if (bts == BUFFER1){
                for (int i=0; i<TRANSMIT_BUF_SIZE; i++){
                    buf_to_send1[bts_count*TRANSMIT_BUF_SIZE + i] = data_axis[i];
                }
            } else {
                for (int i=0; i<TRANSMIT_BUF_SIZE; i++){
                    buf_to_send2[bts_count*TRANSMIT_BUF_SIZE + i] = data_axis[i];
                }
            }
            bts_count++;
            if (bts_count>COUNT_MAX-1){
                bts_count = 0;
                if (bts == BUFFER1){
                    bts = BUFFER2;
                    serial_write(buf_to_send1, USB_BUFFER_SIZE);
                } else {
                    
                    bts = BUFFER1;
                    serial_write(buf_to_send2, USB_BUFFER_SIZE);
                }
                serial_writeln();
            }   
#endif
        }
    }
}

void accelerometers_init(){

    /* SPI init */
    SPI.begin();

    /* Chips configuration */
    for(int chip=0; chip<NB_ACCELS; chip++){
        pinMode(CHIP_SELECTS[chip], OUTPUT);
        digitalWrite(CHIP_SELECTS[chip], HIGH);
        pinMode(INTERRUPTS[chip], INPUT);
        delay(DELAY_INIT);
        AccConfigBUF(CHIP_SELECTS[chip]);
    }
    delay(DELAY_INIT);

    /* Chips testing : WHO_I_AM should be 0x3d or 61 or '=' (hey, dec, ascii) */
    uint8_t init_counter = 0;
    for(int chip=0; chip<NB_ACCELS; chip++){
        unsigned int who_am_i = readRegister(WHO_AM_I, 1, CHIP_SELECTS[chip]); 
        serial_println(String(who_am_i));
        if (who_am_i == WHO_AM_I_val){
            init_counter++;
        }
        delay(DELAY_INIT);
    }
#ifdef RESET_UNTIL_ACTIVE
    if (init_counter != NB_ACCELS){
        NVIC_SystemReset();
    }
#endif
    serial_println(String(init_counter));
    if (init_counter == NB_ACCELS){
        set_irled(0, 1);
        set_irled(1, 1);
    }

    if (ITimer.attachInterruptInterval_MS(TIMER0_INTERVAL_MS+5, callback_gatherAccs)) {serial_println(F("Starting ITimer OK"));}
    else {serial_println(F("Can't set ITimer. Select another freq. or interval"));}
}

void accelerometers_set_axis(uint8_t AccID, uint8_t axis){
    if (AccID > NB_ACCELS){
        return;
    }
    if (axis > 2){
        return;
    }
    axis_to_read[AccID] = axis;
}

void accelerometers_enable(uint8_t AccID){
    if (AccID > NB_ACCELS){
        return;
    }
    startAccelBUF(CHIP_SELECTS[AccID]);
    acc_enables[AccID] = ACC_ENABLED;
}

void accelerometers_disable(uint8_t AccID){
    if (AccID > NB_ACCELS){
        return;
    }
    stopAccelBUF(CHIP_SELECTS[AccID]);
    acc_enables[AccID] = ACC_DISABLED;
}
