#include <spi_comm.hpp>

static const int CSpin1     = 9;   // Chip select 1
static const int CSpin2     = 10;  // Chip select 2
static const int ReadyPin1  = 3;   // Interrupt 1
static const int ReadyPin2  = 2;   // Interrupt 2

uint8_t bus_acquirable = BUS_FREE;

uint8_t buf_to_send11[USB_BUFFER_SIZE];
uint8_t buf_to_send12[USB_BUFFER_SIZE];
float time_stamp1;

uint8_t buf_to_send21[USB_BUFFER_SIZE];
uint8_t buf_to_send22[USB_BUFFER_SIZE];
float time_stamp2;

int bts_count1 = 0;
int bts_count2 = 0;

uint8_t bts1 = 0;
uint8_t bts2 = 0;

void convert_acc_buf_from_raw_UINT16(uint8_t raw[], uint16_t datX[], uint16_t datY[], uint16_t datZ[]){
    for (int i=0; i<BUF_SIZE; i++){
        int ind = i*DATA_PACK;

        int16_t temp = raw[ind+0]; 
        temp = (temp << 8) | raw[ind+1];
        datX[i] = temp;

        temp = raw[ind+2]; 
        temp = ((temp << 8) | raw[ind+3]);
        datY[i] = temp;

        temp = raw[ind+4]; 
        temp = ((temp << 8) | raw[ind+5]);
        temp = ~temp;
        temp += 1;
        temp ^= (1 << 15);
        datZ[i] = (uint16_t)temp;
    }
}

void extract_axis_bytes(uint8_t raw[], uint8_t dat[], uint8_t axis){
    for (int i=0; i<2*BUF_SIZE; i+=2){
        int ind = (i/2)*DATA_PACK;

        dat[i] = raw[ind+axis*2+0];
        dat[i+1] = raw[ind+axis*2+1];
    }
}


void writeRegister(byte reg, byte val, int CSpin) {
  
    // take the chip select low to select the device:
    digitalWrite(CSpin, LOW);

    SPI.transfer(reg); //Send register location
    SPI.transfer(val);  //Send value to record into register

    digitalWrite(CSpin, HIGH);
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
    for(int i=0; i<numBytes; i++){
        data[i] = SPI.transfer(0x00);
    }
    digitalWrite(CSpin, HIGH);
    bus_acquirable = BUS_FREE;
}

void getBytesFromAcc(uint8_t CSpin, uint8_t* data_axis){
    static uint8_t acc_dat[BUF_SIZE*DATA_PACK];
    readMultipleRegister(BUF_OUT, BUF_SIZE*DATA_PACK, acc_dat, CSpin);
    extract_axis_bytes(acc_dat, data_axis, AXIS_Z);
}

void configINT(int CSpin){
    writeRegister(CNTL1addr, 0x00, CSpin);
    writeRegister(ODCNTLaddr, ODCNTL_SPEED, CSpin);
    writeRegister(IC1addr, IC1_INT, CSpin);
    writeRegister(IC4addr, IC4_INT, CSpin);
    writeRegister(CNTL1addr, CNTL1_INT, CSpin);
}

void configBUF(int CSpin){
    writeRegister(CNTL1addr, 0x00, CSpin);
    writeRegister(ODCNTLaddr, ODCNTL_SPEED, CSpin);
    writeRegister(IC1addr, IC1_BUF, CSpin);
    writeRegister(IC4addr, IC4_BUF, CSpin);
    writeRegister(BUFCNTL1addr, BUF_CNTL1, CSpin);
    writeRegister(BUFCNTL2addr, BUF_CNTL2, CSpin);
    // writeRegister(CNTL1addr, CNTL1_BUF, CSpin);
}

void startAccelBUF(int CSpin){
    writeRegister(CNTL1addr, CNTL1_BUF, CSpin);
}

void callback_Acc1BUF(){
    Serial.println("coucou1");
    static uint8_t acc1_dat[BUF_SIZE*DATA_PACK];
    static uint8_t data_axis[2*BUF_SIZE];

    while(!bus_acquirable){;}
    readMultipleRegister(BUF_OUT, BUF_SIZE*DATA_PACK, acc1_dat, CSpin1);
    extract_axis_bytes(acc1_dat, data_axis, AXIS_OF_INTEREST);

    if (bts1 == 0){
        for (int i=0; i<BUF_SIZE_8; i++){
            // if (bts_count1 == 0){
            //     buf_to_send11[i+BUF_SIZE_8*bts_count1] = ASCII_1;
            // } else {
            //     buf_to_send11[i+BUF_SIZE_8*bts_count1] = ASCII_2;
            // }
            buf_to_send11[i+BUF_SIZE_8*bts_count1] = data_axis[i];
        }
    } else {
        for (int i=0; i<BUF_SIZE_8; i++){
            // if (bts_count1 == 0){
            //     buf_to_send12[i+BUF_SIZE_8*bts_count1] = ASCII_3;
            // } else {
            //     buf_to_send12[i+BUF_SIZE_8*bts_count1] = ASCII_4;
            // }
            buf_to_send12[i+BUF_SIZE_8*bts_count1] = data_axis[i];
        }
    }
    bts_count1++;
    if (bts_count1 > COUNT_MAX - 1){
        bts_count1 = 0;

        if (bts1 == 0){
            Serial.write(buf_to_send11, sizeof(buf_to_send11));
            Serial.println("");
        } else {
            Serial.write(buf_to_send12, sizeof(buf_to_send12));
            Serial.println("");
        }
        bts1 = (bts1 + 1)%2;
    }
}

void callback_Acc2BUF(){
    Serial.println("coucou2");
    static uint8_t acc2_dat[BUF_SIZE*DATA_PACK];
    static uint8_t data_axis[2*BUF_SIZE];

    while(!bus_acquirable){;}
    readMultipleRegister(BUF_OUT, BUF_SIZE*DATA_PACK, acc2_dat, CSpin2);
    extract_axis_bytes(acc2_dat, data_axis, AXIS_OF_INTEREST);
    // Serial.write(acc2_dat, sizeof(acc2_dat));
    // Serial.println("");
    if (bts2 == 0){
        for (int i=0; i<BUF_SIZE_8; i++){
            // if (bts_count2 == 0){
            //     buf_to_send21[i+BUF_SIZE_8*bts_count2] = ASCII_5;
            // } else {
            //     buf_to_send21[i+BUF_SIZE_8*bts_count2] = ASCII_6;
            // }
            buf_to_send21[i+BUF_SIZE_8*bts_count2] = data_axis[i];
        }
    } else {
        for (int i=0; i<BUF_SIZE_8; i++){
            // if (bts_count2 == 0){
            //     buf_to_send22[i+BUF_SIZE_8*bts_count2] = ASCII_7;
            // } else {
            //     buf_to_send22[i+BUF_SIZE_8*bts_count2] = ASCII_8;
            // }
            buf_to_send22[i+BUF_SIZE_8*bts_count2] = data_axis[i];
        }
    }
    bts_count2++;
    if (bts_count2 > COUNT_MAX - 1){
        bts_count2 = 0;

        if (bts2 == 0){
            Serial.write(buf_to_send21, sizeof(buf_to_send21));
            Serial.println("");
        } else {
            Serial.write(buf_to_send22, sizeof(buf_to_send22));
            Serial.println("");
        }
        bts2 = (bts2 + 1)%2;
    }
}

void accels_init(){

    while(!Serial){
        delay(50);
    }

    Serial.begin(230400);
    Serial.println("Welcome.");

    SPI.begin();

    digitalWrite(CSpin1, HIGH);
    digitalWrite(CSpin2, HIGH);

    pinMode(CSpin1, OUTPUT);
    pinMode(CSpin2, OUTPUT);
    pinMode(ReadyPin1, INPUT);
    pinMode(ReadyPin2, INPUT);

    delay(100);
    configBUF(CSpin2);
    delay(100);
    configBUF(CSpin1);
    delay(100);

    Serial.print("WHO_AM_I 1 : ");
    Serial.println(readRegister(WHO_AM_I, 1, CSpin1));
    Serial.print("WHO_AM_I 2 : ");
    Serial.println(readRegister(WHO_AM_I, 1, CSpin2));

    startAccelBUF(CSpin1);
    startAccelBUF(CSpin2);

    attachInterrupt(digitalPinToInterrupt(ReadyPin1), callback_Acc1BUF, RISING);
    attachInterrupt(digitalPinToInterrupt(ReadyPin2), callback_Acc2BUF, RISING);

    // startAccelBUF(CSpin1);
    // startAccelBUF(CSpin2);

    // delay(1000);
    
    // static uint8_t data_axis[2*BUF_SIZE];
    // getBytesFromAcc(CSpin1, data_axis);
    // Serial.print("ACC1");
    // Serial.write(data_axis, sizeof(data_axis));
    // Serial.println("");

    // getBytesFromAcc(CSpin2, data_axis);
    // Serial.print("ACC2");
    // Serial.write(data_axis, sizeof(data_axis));
    // Serial.println("");
    
}