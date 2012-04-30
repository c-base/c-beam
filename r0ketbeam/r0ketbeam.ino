#include <SPI.h>
#include <RF24.h>
#include "printf.h"

typedef struct {
  uint8_t length;
  uint8_t protocol;
  uint8_t flags;
  uint8_t strength;
  uint32_t sequence;
  uint32_t id;
  uint8_t button1;
  uint8_t button2;
  uint16_t crc;
} beacon_data_t;

typedef struct {
  uint8_t length;
  uint8_t protocol;
  uint32_t id;
  char name[8];
  uint16_t crc;
} beacon_name_t;

RF24 radio(49, 53);

#if defined(PRINT_NORESPONSE)
int inc;
#endif

void setup()
{
  Serial.begin(115200);
  printf_begin();
  
  Serial.println("# Configuring interface ...");
  radio.begin();

  //Serial.println("> dynamic payloads = true");
  //radio.enableDynamicPayloads();

  //Serial.println("> Speed = 2M");
  radio.setDataRate(RF24_2MBPS);
  
  //Serial.println("> Channel = 81");
  radio.setChannel(81);
  
  //Serial.println("> auto_ack = false");
  radio.setAutoAck(false);
  
  //Serial.println("> payload size = 16 bytes");
  radio.setPayloadSize(16);
  
  //Serial.println("> crc = 8 bit");
  radio.setCRCLength(RF24_CRC_8);
  
  //Serial.println("> rx mac = 0x0102030201LL");
  radio.openReadingPipe(1, 0x0102030201LL);

  //Serial.println("> tx mac = 0x0102030201LL");
  radio.openWritingPipe(0x0102030201LL);
  
  Serial.print("# Carrier: ");
  boolean carrier = radio.testCarrier();
  Serial.println(carrier);
  
  Serial.println("# Start listening ...");
  radio.startListening();
  
  //radio.printDetails();
}

uint32_t flip32(uint32_t number)
{
  return (number & 0x000000FF) << 24 |
         (number & 0x0000FF00) << 8 |
         (number & 0x00FF0000) >> 8 |
         (number & 0xFF000000) >> 24;
}

uint16_t flip16(uint16_t number)
{
  return (number & 0x00FF) << 8 |
         (number & 0xFF00) >> 8;
}

uint16_t crc16(uint8_t* buf, int len)
{
  /* code from r0ket/firmware/basic/crc.c */
  
  uint16_t crc = 0xffff;

  for (int i=0; i < len; i++)
  {
    crc = (unsigned char)(crc >> 8) | (crc << 8);
    crc ^= buf[i];
    crc ^= (unsigned char)(crc & 0xff) >> 4;
    crc ^= (crc << 8) << 4;
    crc ^= ((crc & 0xff) << 4) << 1;
  }
  
  return crc;
}

void sendNick(uint32_t id, char* name)
{
  beacon_name_t pkt;
  pkt.length = 16;
  pkt.protocol = 0x23;
  pkt.id = flip32(id);
  memset(&pkt.name, 0, sizeof(pkt.name));
  strncpy((char*)&pkt.name, name, min(8,strlen(name)));
  pkt.crc = flip16(crc16((uint8_t*)&pkt, sizeof(pkt)-2));
  
  radio.stopListening();
  auf 
  radio.write(&pkt, sizeof(pkt));
  radio.startListening();
}

void sendDummyPacket(uint32_t id, uint32_t sequence)
{
  beacon_data_t pkt;
  pkt.length = 16;
  pkt.protocol = 0x17;
  pkt.id = flip32(id);
  pkt.sequence = flip32(sequence);
  pkt.flags = 0x00; 
  pkt.button1 = 0xFF;
  pkt.button2 = 0xFF;
  
  pkt.crc = flip16(crc16((uint8_t*)&pkt, sizeof(pkt)-2));
  
  radio.stopListening();
  radio.write((uint8_t*)&pkt, sizeof(pkt));
  radio.startListening();
}

int last_sent_packet = 0;
char* nick = "CCCr0ket";

void loop()
{
  int delta = millis() - last_sent_packet;
  if (delta > 1234)
  {
    last_sent_packet = millis();
    //printf("[%i] ", delta);

    uint32_t id = 0x12345678UL;

    char myNick[9];
    sprintf((char*)&myNick, "*[%u]", (unsigned int)millis());
    myNick[sizeof(myNick)-1] = '\0';

    Serial.print("# Sending nick '");
    Serial.print(myNick);
    Serial.print("' as 0x");
    Serial.print(id, HEX);
    Serial.println(" ...");
    sendNick(id, (char*)&myNick);

    //sendDummyPacket(id, last_sent_packet);
  }
  
  if (radio.available())
  {
    //uint8_t buf[16];
    beacon_data_t buf;
    radio.read(&buf, sizeof(buf));

    #if defined(PRINT_NORESPONSE)   
    if (inc > 0) Serial.println();
    inc = 0;
    #endif

    Serial.print("RECV ");
    Serial.print(flip32(buf.id), HEX);
    Serial.print(": ");
    Serial.print(flip32(buf.sequence), HEX);
    Serial.print(" (");
    Serial.print(buf.strength / 255.0 * 100.0);
    Serial.println(")");
    
    uint16_t crc = flip16(crc16((uint8_t*)&buf, sizeof(buf)-2));
    if (crc != buf.crc)
      printf("! CRC mismatch: expected %u, got %u\r\n", crc, buf.crc);
  }
  else 
  {
    #if defined(PRINT_NORESPONSE)
    if (inc++ == 80) { Serial.println(); inc = 0; }
    Serial.print(".");
    delay(100);
    #endif
  }
}


