#include <stdio.h>
#include <stdarg.h>
#include <errno.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>

#include <pcscdefines.h>
#include <ifdhandler.h>

#define JCOP_PORT            8050
#define JCOP_HOST      "localhost"
#define JCOP_BUFSZ  1024

int JCOP_socket = -1;
char JCOP_buffer[JCOP_BUFSZ];
char JCOP_atr[33]; // MAX_ATR_SIZE
int JCOP_atrl;


#ifdef DEBUG
char DBG_buf[8192];
void dbg_ba2s(char *cp, int cnt);
static void dbg_log(const char *fmt, ...);
#else
#define dbg_ba2s(...)
#define dbg_log(...);

#endif

static int jcop_read(int tag);
static int jcop_power_up();
static int jcop_close();



     
RESPONSECODE IFDHCreateChannel ( DWORD Lun, DWORD Channel ) {

  /* Lun - Logical Unit Number, use this for multiple card slots 
     or multiple readers. 0xXXXXYYYY -  XXXX multiple readers,
     YYYY multiple slots. The resource manager will set these 
     automatically.  By default the resource manager loads a new
     instance of the driver so if your reader does not have more than
     one smartcard slot then ignore the Lun in all the functions.
     Future versions of PC/SC might support loading multiple readers
     through one instance of the driver in which XXXX would be important
     to implement if you want this.
  */
  
  /* Channel - Channel ID.  This is denoted by the following:
     0x000001 - /dev/pcsc/1
     0x000002 - /dev/pcsc/2
     0x000003 - /dev/pcsc/3
     
     USB readers may choose to ignore this parameter and query 
     the bus for the particular reader.
  */

  /* This function is required to open a communications channel to the 
     port listed by Channel.  For example, the first serial reader on COM1 would
     link to /dev/pcsc/1 which would be a sym link to /dev/ttyS0 on some machines
     This is used to help with intermachine independance.
     
     Once the channel is opened the reader must be in a state in which it is possible
     to query IFDHICCPresence() for card status.
 
     returns:

     IFD_SUCCESS
     IFD_COMMUNICATION_ERROR
  */
    
    /**
     * Connection to JCOP is setup later.
    */
    dbg_log("JCOP.CreateChanenel(): Lun 0x%x, Channel 0x%x\n", Lun, Channel);

    jcop_power_up();

    return IFD_SUCCESS;
}

RESPONSECODE IFDHCloseChannel ( DWORD Lun ) {
  
  /* This function should close the reader communication channel
     for the particular reader.  Prior to closing the communication channel
     the reader should make sure the card is powered down and the terminal
     is also powered down.

     returns:

     IFD_SUCCESS
     IFD_COMMUNICATION_ERROR     
  */

    dbg_log("JCOP.CreateChanenel(): Lun 0x%x\n", Lun);

    return IFD_SUCCESS;
  

}

RESPONSECODE IFDHGetCapabilities ( DWORD Lun, DWORD Tag, 
				   PDWORD Length, PUCHAR Value ) {
  
  /* This function should get the slot/card capabilities for a particular
     slot/card specified by Lun.  Again, if you have only 1 card slot and don't mind
     loading a new driver for each reader then ignore Lun.

     Tag - the tag for the information requested
         example: TAG_IFD_ATR - return the Atr and it's size (required).
         these tags are defined in ifdhandler.h

     Length - the length of the returned data
     Value  - the value of the data

     returns:
     
     IFD_SUCCESS
     IFD_ERROR_TAG
  */
    dbg_log("JCOP.GetCapabilities(): Lun 0x%x, Tag %d 0x%x, Length 0x%x, Value 0x%x\n", Lun, Tag, Tag, *Length, Value);
    switch(Tag){
    case TAG_IFD_SLOTS_NUMBER:
	*Value = 1;
	break;
    default:
	dbg_log("unimplemented tag %d\n", Tag);
    }
    return IFD_SUCCESS;

}

RESPONSECODE IFDHSetCapabilities ( DWORD Lun, DWORD Tag, 
			       DWORD Length, PUCHAR Value ) {

  /* This function should set the slot/card capabilities for a particular
     slot/card specified by Lun.  Again, if you have only 1 card slot and don't mind
     loading a new driver for each reader then ignore Lun.

     Tag - the tag for the information needing set

     Length - the length of the returned data
     Value  - the value of the data

     returns:
     
     IFD_SUCCESS
     IFD_ERROR_TAG
     IFD_ERROR_SET_FAILURE
     IFD_ERROR_VALUE_READ_ONLY
  */
#ifdef PCSC_DEBUG
    fprintf(stderr, "JCOP.SetCapabilities(): Lun 0x%x, Tag 0x%x, Length 0x%x, Value 0x%x\n", Lun, Tag, Length, Value);
    fflush(stderr);
#endif

    return IFD_SUCCESS;
  
}

RESPONSECODE IFDHSetProtocolParameters ( DWORD Lun, DWORD Protocol, 
				   UCHAR Flags, UCHAR PTS1,
				   UCHAR PTS2, UCHAR PTS3) {

  /* This function should set the PTS of a particular card/slot using
     the three PTS parameters sent

     Protocol  - 0 .... 14  T=0 .... T=14
     Flags     - Logical OR of possible values:
     IFD_NEGOTIATE_PTS1 IFD_NEGOTIATE_PTS2 IFD_NEGOTIATE_PTS3
     to determine which PTS values to negotiate.
     PTS1,PTS2,PTS3 - PTS Values.

     returns:

     IFD_SUCCESS
     IFD_ERROR_PTS_FAILURE
     IFD_COMMUNICATION_ERROR
     IFD_PROTOCOL_NOT_SUPPORTED
  */

    dbg_log("JCOP.SetProtoParams(): Lun 0x%x, Proto 0x%x, Flags 0x%x, PTS1 0x%x, PTS2 0x%x, PTS3 0x%x\n", Lun, Protocol, Flags, PTS1&0xff, PTS2&0xff, PTS3&0xff);

    return IFD_SUCCESS;

}



RESPONSECODE IFDHPowerICC ( DWORD Lun, DWORD Action, 
			    PUCHAR Atr, PDWORD AtrLength ) {

  /* This function controls the power and reset signals of the smartcard reader
     at the particular reader/slot specified by Lun.

     Action - Action to be taken on the card.

     IFD_POWER_UP - Power and reset the card if not done so 
     (store the ATR and return it and it's length).
 
     IFD_POWER_DOWN - Power down the card if not done already 
     (Atr/AtrLength should
     be zero'd)
 
    IFD_RESET - Perform a quick reset on the card.  If the card is not powered
     power up the card.  (Store and return the Atr/Length)

     Atr - Answer to Reset of the card.  The driver is responsible for caching
     this value in case IFDHGetCapabilities is called requesting the ATR and it's
     length.  This should not exceed MAX_ATR_SIZE.

     AtrLength - Length of the Atr.  This should not exceed MAX_ATR_SIZE.

     Notes:

     Memory cards without an ATR should return IFD_SUCCESS on reset
     but the Atr should be zero'd and the length should be zero

     Reset errors should return zero for the AtrLength and return 
     IFD_ERROR_POWER_ACTION.

     returns:

     IFD_SUCCESS
     IFD_ERROR_POWER_ACTION
     IFD_COMMUNICATION_ERROR
     IFD_NOT_SUPPORTED
  */
    dbg_log("JCOP.PowerICC(): Lun 0x%x, Action %d, Atr 0x%x, Len %d\n", Lun, Action, Atr, *AtrLength);
    
    if (Action == IFD_POWER_UP){
	int ret = jcop_power_up();
	if (ret == IFD_SUCCESS){
	    memcpy(Atr, JCOP_atr, JCOP_atrl);
	    *AtrLength = JCOP_atrl;
	    dbg_log("JCOP.PowerICC(): return atr\n");
	    return IFD_SUCCESS;
	}
	dbg_log("JCOP.PowerICC(): return error\n");
	*AtrLength = 0;
	return IFD_COMMUNICATION_ERROR;
    }

    return IFD_SUCCESS;
}



RESPONSECODE IFDHTransmitToICC ( DWORD Lun, SCARD_IO_HEADER SendPci, 
				 PUCHAR TxBuffer, DWORD TxLength, 
				 PUCHAR RxBuffer, PDWORD RxLength, 
				 PSCARD_IO_HEADER RecvPci ) {
  
  /* This function performs an APDU exchange with the card/slot specified by
     Lun.  The driver is responsible for performing any protocol specific exchanges
     such as T=0/1 ... differences.  Calling this function will abstract all protocol
     differences.

     SendPci
     Protocol - 0, 1, .... 14
     Length   - Not used.

     TxBuffer - Transmit APDU example (0x00 0xA4 0x00 0x00 0x02 0x3F 0x00)
     TxLength - Length of this buffer.
     RxBuffer - Receive APDU example (0x61 0x14)
     RxLength - Length of the received APDU.  This function will be passed
     the size of the buffer of RxBuffer and this function is responsible for
     setting this to the length of the received APDU.  This should be ZERO
     on all errors.  The resource manager will take responsibility of zeroing
     out any temporary APDU buffers for security reasons.
  
     RecvPci
     Protocol - 0, 1, .... 14
     Length   - Not used.

     Notes:
     The driver is responsible for knowing what type of card it has.  If the current
     slot/card contains a memory card then this command should ignore the Protocol
     and use the MCT style commands for support for these style cards and transmit 
     them appropriately.  If your reader does not support memory cards or you don't
     want to then ignore this.

     RxLength should be set to zero on error.

     returns:
     
     IFD_SUCCESS
     IFD_COMMUNICATION_ERROR
     IFD_RESPONSE_TIMEOUT
     IFD_ICC_NOT_PRESENT
     IFD_PROTOCOL_NOT_SUPPORTED
  */
    int ret;

    dbg_log("JCOP.Transmit(): Lun 0x%x\n", Lun);
    dbg_log("JCOP.Transmit(): io_hdr proto %d, length %d\n", SendPci.Protocol, SendPci.Length);
    dbg_log("JCOP.Transmit(): txb 0x%x, txbl %d, rxb 0x%x, rxbl %d\n", TxBuffer, TxLength, RxBuffer, *RxLength);
    
    if (JCOP_socket < 0){
	dbg_log("JCOP.Transmit(): invalid jcop socket\n");
	return IFD_COMMUNICATION_ERROR;
    }

    if (TxLength >= 256){
	dbg_log("JCOP.Transmit(): invalid transmit buffer size %d\n", TxLength);
	jcop_close();
	return IFD_COMMUNICATION_ERROR;
    }

    // copy data from send_buffer to JCOP_buffer and send
    JCOP_buffer[0] = 0x1;
    JCOP_buffer[1] = 0x0;
    JCOP_buffer[2] = TxLength/256;
    JCOP_buffer[3] = TxLength%256;
    memcpy(JCOP_buffer+4, TxBuffer, TxLength);
    
    dbg_ba2s(JCOP_buffer, TxLength+4);
    dbg_log("jcop send: %s\n", DBG_buf);

    // send apdu
    ret = write(JCOP_socket, JCOP_buffer, TxLength + 4);
    if (ret < 0){
	dbg_log("Failed to transmit to jcop\n");
	jcop_close();
	return IFD_COMMUNICATION_ERROR;
    }

    // read apdu
    ret = jcop_read(0x1);
    if (ret < 0){
	dbg_log("Failed to receive apdu response\n");
	return IFD_COMMUNICATION_ERROR;
    }
    *RxLength = ret - 4;
    memcpy(RxBuffer, JCOP_buffer+4, *RxLength);
    dbg_ba2s(RxBuffer, *RxLength);
    dbg_log("jcop response apdu: %s\n", DBG_buf);

    return IFD_SUCCESS;
}

RESPONSECODE IFDHControl ( DWORD Lun, PUCHAR TxBuffer, 
			 DWORD TxLength, PUCHAR RxBuffer, 
			 PDWORD RxLength ) {

  /* This function performs a data exchange with the reader (not the card)
     specified by Lun.  Here XXXX will only be used.
     It is responsible for abstracting functionality such as PIN pads,
     biometrics, LCD panels, etc.  You should follow the MCT, CTBCS 
     specifications for a list of accepted commands to implement.

     TxBuffer - Transmit data
     TxLength - Length of this buffer.
     RxBuffer - Receive data
     RxLength - Length of the received data.  This function will be passed
     the length of the buffer RxBuffer and it must set this to the length
     of the received data.

     Notes:
     RxLength should be zero on error.
  */

    dbg_log("JCOP.Control(): Lun 0x%x\n", Lun);

    return IFD_SUCCESS;

}

RESPONSECODE IFDHICCPresence( DWORD Lun ) {

  /* This function returns the status of the card inserted in the 
     reader/slot specified by Lun.  It will return either:

     returns:
     IFD_ICC_PRESENT
     IFD_ICC_NOT_PRESENT
     IFD_COMMUNICATION_ERROR
  */
    fd_set set;
    struct timeval timeout;
    int ret;

    if (JCOP_socket < 0){
	// try to power up jcop
	dbg_log("Presence(): try to power up jcop ...\n");
	(void) jcop_power_up();
    }
     
    if (JCOP_socket > 0){
	/* Initialize the file descriptor set. */
	FD_ZERO (&set);
	FD_SET (JCOP_socket, &set);
	
	/* Initialize the timeout data structure. */
	timeout.tv_sec = 0;
	timeout.tv_usec = 0;
	
	/* `select' returns 0 if timeout, 1 if input available, -1 if error. */
	ret = select (FD_SETSIZE, &set, NULL, NULL, &timeout);
	if (ret < 0){
	    dbg_log("select failed\n");
	    jcop_close();
	    return IFD_ICC_NOT_PRESENT;
	}
	if (ret == 1){
	    dbg_log("select: data available ...\n");
	    ret = read(JCOP_socket, JCOP_buffer, JCOP_BUFSZ);
	    if (ret <= 0){
		dbg_log("select: socket has been closed down\n");
		jcop_close();
		return IFD_ICC_NOT_PRESENT;
	    }else{
		// this should not happen: simulator data is always picked up at transmit time
		;
	    }
	}
	//dbg_log("jcop seems alive ...\n");
    }

    return (JCOP_socket < 0) ? IFD_ICC_NOT_PRESENT : IFD_ICC_PRESENT;
}




static int jcop_read(int tag){
    int ret, len;

    dbg_log("read jcop data ...\n");

    ret = read(JCOP_socket, JCOP_buffer, JCOP_BUFSZ);
    dbg_ba2s(JCOP_buffer, ret);
    dbg_log("jcop response1: %s\n", DBG_buf);
    if (ret < 4){
	dbg_log("invalid jcop response length\n");
	jcop_close();
	return -1;
    }
    if ((JCOP_buffer[0] != tag) || (JCOP_buffer[1] != 0)){
	dbg_log("invalid jcop response type %d\n", JCOP_buffer[0]&0xff);
	jcop_close();
	return -1;
    }
    len = (JCOP_buffer[2]&0xff << 8) + (JCOP_buffer[3]&0xff);
    if (ret == len + 4){
	dbg_log("jcop data fully read\n");
	return ret;
    }
    dbg_log("read jcop outstanding data ...\n");
    if (ret != 4){
	dbg_log("invalid short jcop data length\n");
	jcop_close();
	return -1;
    }
    ret = read(JCOP_socket, JCOP_buffer+4, JCOP_BUFSZ-4);
    dbg_ba2s(JCOP_buffer+4, ret);
    dbg_log("jcop response2: %s\n", DBG_buf);
    if (ret < 0){
	dbg_log("jcop read failed\n");
	jcop_close();
	return -1;
    }
    if (ret != len){
	dbg_log("invalid jcop response data length %d\n", ret);
	jcop_close();
	return -1;
    }
    return 4+ret;
}


static int jcop_power_up(){
    struct sockaddr_in servername;
    struct hostent *hostinfo;
    int ret;

    if (JCOP_socket >= 0)
	jcop_close();
    
    dbg_log("jcop powering up ...\n");
    
    // socket creation
    JCOP_socket = socket(PF_INET, SOCK_STREAM, 0);
    if (JCOP_socket < 0) {
	dbg_log("jcop socket creation failed\n");
	return IFD_COMMUNICATION_ERROR;
    }
    
    // lookup jcop host
    servername.sin_family = AF_INET;
    servername.sin_port = htons(JCOP_PORT);
    hostinfo = gethostbyname(JCOP_HOST);
    if (hostinfo == NULL){
	jcop_close();
	fprintf(stderr, "invalid jcop host %s\n", JCOP_HOST);
	fflush(stderr);
	exit(-1);
    }
    servername.sin_addr = *(struct in_addr *) hostinfo->h_addr;
    
    // connect to jcop
    if (connect (JCOP_socket, (struct sockaddr *) &servername, sizeof (servername)) < 0){
	jcop_close();
	dbg_log("jcop socket connect failed\n");
	return IFD_COMMUNICATION_ERROR;
    }
    
    // request jcop atr
    JCOP_buffer[0] = 0x0;
    JCOP_buffer[1] = 0x21;
    JCOP_buffer[2] = 0;
    JCOP_buffer[3] = 4;
    JCOP_buffer[4] = 0;
    JCOP_buffer[5] = 0;
    JCOP_buffer[6] = 0;
    JCOP_buffer[7] = 0;
    ret = write(JCOP_socket, JCOP_buffer, 8);
    if (ret < 0){
	dbg_log("Failed to write jcop setup\n");
	jcop_close();
	return IFD_COMMUNICATION_ERROR;
    }
	
    // read atr
    ret = jcop_read(0x0);
    if (ret < 4){
	dbg_log("read jcop atr failed\n");
	return -1;
    }
    JCOP_atrl = ret - 4;
    memcpy(JCOP_atr, JCOP_buffer+4, JCOP_atrl);
    dbg_ba2s(JCOP_atr, JCOP_atrl);
    dbg_log("jcop atr: %s\n", DBG_buf);
    
    return IFD_SUCCESS;
}

static int jcop_close(){
    dbg_log("jcop_close(): closing\n");
    close(JCOP_socket);
    JCOP_socket = -1;
}



#ifdef DEBUG
static void dbg_ba2s(char *cp, int cnt){
    int i, n;
    sprintf(DBG_buf, "%d:", cnt);
    for(i = 0, n = 0; i < cnt; i++){
	n += sprintf(DBG_buf + n, "0x%x:", cp[i]&0xff);
    }
}
		 


static void dbg_log(const char *fmt, ...){
    va_list marker;
    char buf[4096];
    va_start(marker, fmt);
    vsprintf(buf, fmt, marker);
    fprintf(stderr, buf);
    fflush(stderr);
}
#endif /* DEBUG */
