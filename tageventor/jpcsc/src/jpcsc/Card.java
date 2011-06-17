package PCSC_PACKAGE_NAME;


/**
 * The Card class offers PCSC functions related to connecting,
 * disconnecting and transferring data to cards.
 */
public final class Card{
    /** Native handle. */
    private long card;

    /** Protocol used. It is cached and set in Connect() and Reconnect(). */
    private int proto;

    /** Flag controlling the transparent handling of T0 GetResponse. */
    private boolean t0getResponse;

    /** Flag controlling the transparent handling of incorrect Le */
    private boolean resendOnWrongLe;

     
    /**
     * Constructor.
     */
    Card(){
	t0getResponse = true;
	resendOnWrongLe = true;
    }

    /**
     * Return string representation.
     */
    public final String toString(){
	return "card " + card + ", proto " + proto + ", toflag " + t0getResponse;
    }

    /**
     * Return protocol used.
     */
    public final int getProto(){
	return proto;
    }

    /**
     * Return flag indicating the transparent handling of T0 GetResponse.
     */
    public final boolean getT0GetResponse(){
	return t0getResponse;
    }

    /**
     * Switch on/off transparent handling of T0 GetResponse.
     */
    public final void setT0GetResponse(boolean b){
	this.t0getResponse = b;
    }

    /**
     * Return flag indicating the transparent handling of resend on wrong Le
     */
    public final boolean getResendOnWrongLe(){
	return resendOnWrongLe;
    }
    
    /**
     * Switch on/off transparent handling of resend on wrong Le
     */
    public final void setResendOnWrongLe(boolean b){
	this.resendOnWrongLe = b;
    }

    /**
     * Finalizer. Invokes Disconnect() with parameter LEAVE_CARD.
     */
    final protected void finalize(){
#ifdef DEBUG
	System.err.println("Card.finalize(): disconnect ...");
#endif
	try{
	    NativeDisconnect(PCSC.LEAVE_CARD);
	}catch(Exception e){}
    }

    /**
     * Default disconnect from card (LEAVE_CARD).
     */
    public final void Disconnect(){
#ifdef DEBUG
	System.err.println("Card.Disconnect(): default disconnect ...");
#endif
	Disconnect(PCSC.LEAVE_CARD);
    }

    /**
     * Disconnect from card. Valid parameters
     * are LEAVE_CARD, RESET_CARD, UNPOWER_CARD, EJECT_CARD.
     * @param param PCSC.LEAVE_CARD, PCSC.RESET_CARD, PCSC.UNPOWER_CARD, PCSC.EJECT_CARD.
     */
    public final void Disconnect(int param){
	if ((param != PCSC.LEAVE_CARD) && (param != PCSC.RESET_CARD) && (param != PCSC.UNPOWER_CARD) && (param != PCSC.EJECT_CARD))
	    throw new RuntimeException("invalid parameter: set param to LEAVE_CARD, RESET_CARD, UNPOWER_CARD or EJECT_CARD");
	
	int ret = NativeDisconnect(param);
#ifdef DEBUG
	System.err.println("Card.Disconnect(): ret " + ret);
#endif
	if (ret != PCSC.SUCCESS) throw new PCSCException("Disconnect()", ret);
    }

    /**
     * Reconnect to card. Valid parameters are SHARE_EXCLUSIVE, SHARE_SHARED, SHARE_DIRECT for the
     * sharing mode, PROTOCOL_T0, PROTOCOL_T1, PROTOCOL_RAW, PROTOCOL_ANY for the protocol,
     * and LEAVE_CARD, EJECT_CARD, RESET_CARD and UNPOWER_CARD for the initialization parameter.
     * @param dwSharedMode  PCSC.SHARE_EXCLUSIVE, PCSC.SHARE_SHARED or PCSC.SHARE_DIRECT.
     * @param  dwPreferredProtos PCSC.PROTOCOL_T0, PCSC.PROTOCOL_T1, PCSC.PROTOCOL_RAW, PCSC.PROTOCOL_ANY.
     * @param dwInitialization PCSC.LEAVE_CARD, PCSC.EJECT_CARD, PCSC.RESET_CARD and PCSC.UNPOWER_CARD.
     */
    public final void Reconnect(int dwSharedMode, int dwPreferredProtos, int dwInitialization){
	if ((dwPreferredProtos & (PCSC.PROTOCOL_T0|PCSC.PROTOCOL_T1|PCSC.PROTOCOL_RAW|PCSC.PROTOCOL_ANY)) == 0)
	    throw new RuntimeException("invalid parameter: set dwPreferredProtos to PROTOCOL_ANY, PROTOCOL_RAW, PROTOCOL_T0 or PROTOCOL_T1");

	if ((dwSharedMode != PCSC.SHARE_EXCLUSIVE) && (dwSharedMode != PCSC.SHARE_SHARED) && (dwSharedMode != PCSC.SHARE_DIRECT))
	    throw new RuntimeException("invalid parameter: set dwSharedMode to SHARE_DIRECT, SHARE_SHARED or SHARE_EXCLUSIVE");

	if ((dwInitialization != PCSC.LEAVE_CARD) && (dwInitialization != PCSC.RESET_CARD) && (dwInitialization != PCSC.UNPOWER_CARD) && (dwInitialization != PCSC.EJECT_CARD))
	    throw new RuntimeException("invalid parameter: set dwInitialization to LEAVE_CARD, RESET_CARD, UNPOWER_CARD or EJECT_CARD");
	
	int ret = NativeReconnect(dwSharedMode, dwPreferredProtos, dwInitialization); 
#ifdef DEBUG
	System.err.println("Card.Reconnect(): shared " + dwSharedMode + ", protos " + dwPreferredProtos + ", init " + dwInitialization + ", ret " + ret);
#endif
	if (ret != PCSC.SUCCESS) throw new PCSCException("Reconnect()", ret);
    }

    /**
     * Transmit given APDU. Result is returned in a newly instantiated bytearray.
     * In case of error, the native code raises a PCSCException.
     * @return response from the card.
     */
    public final byte[] Transmit(Apdu apdu){
	if (apdu == null) throw new NullPointerException();
	return Transmit(apdu.getBuffer(), 0, apdu.getLength());
    }

    /**
     * Transmit data. Result is returned in a newly instantiated bytearray.
     * The specified range of the parameter array must contain a properly constructed 
     * APDU. In case of error, the native code raises a PCSCException.
     * @param in  buffer holding the APDU.
     * @param off  offset into buffer where the APDU starts.
     * @param len  length of APDU.
     * @return response from the card.
     */
    public final byte[] Transmit(byte[] in, int off, int len){
	if (in == null) throw new NullPointerException();
	if ((off < 0) || (len < 0) || (off + len > in.length))
	    throw new ArrayIndexOutOfBoundsException();
	
#ifdef DEBUG
	System.err.println("Card.Transmit(): apdu " + Apdu.ba2s(in, off, len));
#endif

	byte[] out = NativeTransmit(in, off, len);

#ifdef DEBUG
	System.err.println("Card.Transmit(): response " + Apdu.ba2s(out));
#endif
	return out;
    }

    /** 
     * Transmit data to the card. Result is returned in a newly created array.
     * The given APDU header information and data are stored in a newly created
     * temporary array and passed to the native Transmit routines.
     * @param cla  CLA byte of APDU (byte #0)
     * @param ins  INS byte of APDU (byte #1)
     * @param p1   P1  byte of APDU (byte #2)
     * @param p2   P2  byte of APDU (byte #3)
     * @param p3   P3 or LC  byte of APDU (byte #4). This byte is omitted if parameter has value -1, otherwise it contains number of bytes in buffer in sent to card.
     * @param in   byte array containing command data of APDU. 
     * @param off  offset starting at which data sending is to begin
     * @param le   LE byte of APDU (appended to APDU). This byte is omitted if parameter has value -1.
     * @return response APDU as a byte array
     * @exception  PCSCException if communication failed or if some parameters are wrong */
    public final byte[] Transmit(int cla, int ins, int p1, int p2, int p3, byte[] in, int off, int le){
	// payload length
	int m = ((in == null) ? 0 : p3);
        // 6 = 5 byte header + 1 byte LE
        byte[] apdu = new byte[6 + m];

#ifdef DEBUG
	System.err.println("Card.Transmit(): cla " + cla + ", ins " + ins + ", p1 " + p1 + 
			   ", p2 " + p2 + ", lc " + p3 + ", le " + le);
#endif

	apdu[0] = (byte) cla;
	apdu[1] = (byte) ins;
	apdu[2] = (byte) p1;
	apdu[3] = (byte) p2;
	if (p3 >= 0){
	    apdu[4] = (byte) p3;
	    if (in !=null){
		System.arraycopy(in, off, apdu, 5, p3);
		off = p3 + 5;
	    }else{
		off = 5;
	    }
	}else{
	    off = 5;
	}
	if (le >= 0)
	    apdu[off++] = (byte)le;

	return Transmit(apdu, 0, off);
    }

    /** 
     * Transmit data to the card. Result is returned in a newly created array.
     * The given APDU header information and data are stored in a newly created
     * temporary array and passed to the native Transmit routines. The given
     * range of the given in buffer is sent to the card.
     * @param cla  CLA byte of APDU (byte #0)
     * @param ins  INS byte of APDU (byte #1)
     * @param p1   P1  byte of APDU (byte #2)
     * @param p2   P2  byte of APDU (byte #3)
     * @param in   byte array containing command data of APDU. 
     * @param off  offset starting at which data sending is to begin
     * @param len  number of bytes to be transmitted
     * @param le   LE byte of APDU (appended to APDU). This byte is omitted if parameter has value -1.
     * @return response APDU as a byte array
     * @exception  PCSCException if communication failed or if some parameters are wrong */
    public final byte[] Transmit(int cla, int ins, int p1, int p2, byte[] in, int off, int len, int le){
	return Transmit(cla, ins, p1, p2, len, in, off, le);
    }

    /** 
     * Transmit data to the card. Result is returned in a newly created array.
     * The given APDU header information and data are stored in a newly created
     * temporary array and passed to the native Transmit routines. The given in
     * buffer is fully sent to the card. 
     * @param cla  CLA byte of APDU (byte #0)
     * @param ins  INS byte of APDU (byte #1)
     * @param p1   P1  byte of APDU (byte #2)
     * @param p2   P2  byte of APDU (byte #3)
     * @param in   byte array containing command data of APDU. 
     * @param le   LE byte of APDU (appended to APDU). This byte is omitted if parameter has value -1.
     * @return response APDU as a byte array
     * @exception  PCSCException if communication failed or if some parameters are wrong */
    public final byte[] Transmit(int cla, int ins, int p1, int p2, byte[] in, int le){
	return Transmit(cla, ins, p1, p2, in.length, in, 0, le);
    }

    /** 
     * Transmit data to the card. Result is returned in a newly created array.
     * The given APDU header information and data are stored in a newly created
     * temporary array and passed to the native Transmit routines. The given range
     * of the in buffer is sent and the expected length field is left out.
     * @param cla  CLA byte of APDU (byte #0)
     * @param ins  INS byte of APDU (byte #1)
     * @param p1   P1  byte of APDU (byte #2)
     * @param p2   P2  byte of APDU (byte #3)
     * @param in   byte array containing command data of APDU. 
     * @param off  offset starting at which data sending is to begin
     * @param len  number of bytes to be transmitted
     * @return response APDU as a byte array
     * @exception  PCSCException if communication failed or if some parameters are wrong */
    public final byte[] Transmit(int cla, int ins, int p1, int p2, byte[] in, int off, int len){
	return Transmit(cla, ins, p1, p2, len, in, off, -1);
    }

    /** 
     * Transmit data to the card. Result is returned in a newly created array.
     * The given APDU header information and data are stored in a newly created
     * temporary array and passed to the native Transmit routines. The in buffer
     * is sent completely, the expected length field is left out.
     * @param cla  CLA byte of APDU (byte #0)
     * @param ins  INS byte of APDU (byte #1)
     * @param p1   P1  byte of APDU (byte #2)
     * @param p2   P2  byte of APDU (byte #3)
     * @param in   byte array containing command data of APDU. 
     * @return response APDU as a byte array
     * @exception  PCSCException if communication failed or if some parameters are wrong */
    public final byte[] Transmit(int cla, int ins, int p1, int p2, byte[] in){
	return Transmit(cla, ins, p1, p2, in.length, in, 0, -1);
    }

    /**
     * Transmit data. Result is returned in the passed array at given offset. The
     * range within the given buffer in must hold a properly constructed APDU.
     * On success, the returned value will hold the number of bytes stored in the 
     * result buffer. 
     * In case of an error, a PCSCException is raised. The exception instance
     * then contains the PCSC error code. If sending the APDU was successful,
     * the number of bytes received are returned.
     * @param in  buffer holding the APDU.
     * @param inoff  offset into buffer where the APDU starts.
     * @param len  length of APDU.
     * @param out  buffer where to store the card result.
     * @param outoff  offset into buffer where to store reponse.
     * @return number of bytes returned by the card.
     */
    public final int Transmit(byte[] in, int inoff, int len, byte[] out, int outoff){
	if ((in == null) || (out == null)) 
	    throw new NullPointerException();
	if ((inoff < 0) || (len < 0) || (inoff + len > in.length))
	    throw new ArrayIndexOutOfBoundsException("Transmit(): in params");
	if ((outoff < 0) || (outoff > out.length))
	    throw new ArrayIndexOutOfBoundsException("Transmit(): out params");
	
	int cnt = NativeTransmit(in, inoff, len, out, outoff);


#ifdef DEBUG
	System.err.println("Card.Transmit(): inoff " + inoff + ", inlen " + len + 
			   ", outoff " + outoff + ", retcnt " + cnt);
#endif
	return cnt;
    }

    /**
     * Return status of connection. The State object contains the state
     * of the connection in the dwCurrentState field (which might be 
     * PCSC.ABSENT, PCSC.PRESENT, PCSC.SWALLOWED, PCSC.POWERED, PCSC.NEGOTIABLE
     * or PCSC.SPECIFIC). The protocol of the connection is stored in
     * the State.proto field.
     * @return state of the connection.
     */
    public final State Status(){
	State state = new State();
#ifdef DEBUG
	System.err.println("Card.Status(): entering ...");
#endif
	int ret = NativeStatus(state);
#ifdef DEBUG
	System.err.println("Card.Status(): status " + state);
#endif
	if (ret != PCSC.SUCCESS)
	    throw new PCSCException("Status()", ret);

	return state;
    }


    /**
     * Return status of connection in the specified state object.
     * The State object contains the state
     * of the connection in the dwCurrentState field (which might be 
     * PCSC.ABSENT, PCSC.PRESENT, PCSC.SWALLOWED, PCSC.POWERED, PCSC.NEGOTIABLE
     * or PCSC.SPECIFIC). The protocol of the connection is stored in
     * the State.proto field.
     * @param state of the connection.
     */
    public final void Status(State state){
#ifdef DEBUG
	System.err.println("Card.Status(): entering ...");
#endif
	int ret = NativeStatus(state);
#ifdef DEBUG
	System.err.println("Card.Status(): status " + state);
#endif
	if (ret != PCSC.SUCCESS)
	    throw new PCSCException("Status()", ret);
    }

    /**
     * Signal the start of a transaction.
     */
    public final void BeginTransaction(){
	int ret = NativeBeginTransaction();
#ifdef DEBUG
	System.err.println("Card.BeginTransaction(): ret " + ret);
#endif
	if (ret != PCSC.SUCCESS)
	    throw new PCSCException("BeginTransaction()", ret);
    }

    /**
     * Signal end of a transaction. The parameter dispositon may either be
     * LEAVE_CARD, RESET_CARD, UNPOWER_CARD or EJECT_CARD.
     * @param disposition LEAVE_CARD, RESET_CARD, UNPOWER_CARD, EJECT_CARD.
     */
    public final void EndTransaction(int disposition){
	int ret = NativeEndTransaction(disposition);
#ifdef DEBUG
	System.err.println("Card.EndTransaction(): ret " + ret);
#endif
	if (ret != PCSC.SUCCESS)
	    throw new PCSCException("EndTransaction()", ret);
    }

    /** 
     * Wrapper for SCardControl(). Note that Muscle PCSC (< 1.2.9) does not
     * support the dwControlCode parameter. 
     */
    public final byte[] Control(int dwControlCode, byte[] in){
	if (in == null) throw new NullPointerException();
#ifdef DEBUG
	System.err.println("Card.Control(): dwControlCode " + dwControlCode);
#endif
	return NativeControl(dwControlCode, in, 0, in.length);
    }

    /** 
     * Wrapper for SCardControl(). Note that Muscle PCSC (< 1.2.9) does not
     * support the dwControlCode parameter. 
     */
    public final byte[] Control(int dwControlCode, byte[] in, int off, int len){
	if (in == null) throw new NullPointerException();
	if ((off < 0) || (len < 0) || (off + len > in.length))
	    throw new ArrayIndexOutOfBoundsException();
#ifdef DEBUG
	System.err.println("Card.Control(): dwControlCode " + dwControlCode);
#endif
	return NativeControl(dwControlCode, in, off, len);
    }



    /**
     * Set an attribute of the IFD Handler.
     */
    public final void SetAttrib(int dwAttribId, byte[] attr){
	if (attr == null) throw new NullPointerException();
	int ret = NativeSetAttrib(dwAttribId, attr, attr.length);
#ifdef DEBUG
	System.err.println("Card.SetAttrib(): dwAttribId " + dwAttribId + " ret " + ret);
#endif
	if (ret != PCSC.SUCCESS)
	    throw new PCSCException("SetAttrib()", ret);
    }

    /**
     * Get an attribute from the IFD Handler.
     */
    public final byte[] GetAttrib(int dwAttribId){
#ifdef DEBUG
	System.err.println("Card.GetAttrib(): dwAttribId " + dwAttribId);
#endif
	return NativeGetAttrib(dwAttribId);
    }

    private native int NativeDisconnect(int param); 
    
    private native byte[] NativeTransmit(byte[] in, int off, int len);

    private native int NativeTransmit(byte[] in, int inoff, int len, byte[] out, int outoff);

    private native int NativeStatus(State rs);

    private native int NativeBeginTransaction();

    private native int NativeEndTransaction(int dispo);

    private native int NativeReconnect(int dwSharedMode, int dwPreferredProtos, int dwInitialization);

    private native byte[] NativeControl(int cc, byte[] in, int off, int len);

    private native int NativeSetAttrib(int dwAttribId, byte[] attr, int attrLen);
    
    private native byte[] NativeGetAttrib(int dwAttribId);
}
