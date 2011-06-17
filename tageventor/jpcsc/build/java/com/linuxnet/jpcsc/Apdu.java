

package com.linuxnet.jpcsc;

import java.io.Serializable;
import java.io.IOException;
import java.rmi.RemoteException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;


/**
 * The Apdu class encapsulates an APDU. It allows to construct APDUs, convert between
 * byte and string representations, and can be passed to Card.Transmit().
 * An Apdu instance uses a byte array to store the APDU header and data. This 
 * internal buffer is reused whenever a new APDU is constructed by calling
 * one of the set(...) methods. You can incrementally add additional data bytes
 * and the expected length by calling one of the add(...) methods. If the 
 * previously allocated APDU buffer is too small for a new APDU to create,
 * reset() can be called to reallocate the internal buffer.
 */
public class Apdu  implements Serializable {

    private static final long serialVersionUID = 4348728415045160222L;

    /**
     * Output format: hex space hex space hex
     */
    public static final int HEX_SPACE_HEX_FORMAT = 0;
    /**
     * Output format: hex:hex:hex
     */
    public static final int HEX_COLON_HEX_FORMAT = 1;
    /**
     * Output format: hexhexhex
     */
    public static final int HEX_VOID_HEX_FORMAT = 2;

    /**
     * The buffer keeping the APDU data.
     */
    private byte[] buf;

    /**
     * The length of the data in the buffer keeping the APDU.
     */
    private int len; 

    /**
     * Construct APDU by taking given buffer. Length of the internal buffer will be the same
     * as the length of the given byte array.
     */
    public Apdu(byte[] ba){
	this.buf = ba;
	this.len = ba.length;
    }

    /**
     * Allocate len bytes for internal APDU buffer.
     */
    public Apdu(int len){
	this.buf = new byte[len];
	this.len = 0;
    }
    
    /**
     * Construct internal buffer from given data.
     * @see #construct
     */
    public Apdu(int cla, int ins, int p1, int p2, int p3, byte[] in, int off, int le){
	this.buf = construct(cla, ins, p1, p2, p3, in, off, le);
	this.len = buf.length;
    }
    
    /** 
     * Construct APDU and return it in a newly created array.
     * @param cla  CLA byte of APDU (byte #0)
     * @param ins  INS byte of APDU (byte #1)
     * @param p1   P1  byte of APDU (byte #2)
     * @param p2   P2  byte of APDU (byte #3)
     * @param p3   P3 or LC  byte of APDU (byte #4). This byte is omitted if parameter has value -1, otherwise it contains number of bytes in buffer in sent to card.
     * @param in   byte array containing command data of APDU. If null, p3 is omitted. 
     * @param off  offset starting at which data sending is to begin
     * @param le   LE byte of APDU (appended to APDU). This byte is omitted if parameter has value -1.
     * @return response APDU as a byte array
     */
    public static byte[] construct(int cla, int ins, int p1, int p2, int p3, byte[] in, int off, int le){
	boolean withPayload = ((in != null) && (p3 >= 0));

        // 5 byte header + payload length + eventually 1 byte LE
        byte[] apdu = new byte[4 + (withPayload ? (1 + p3) : 0) + ((le >= 0) ? 1 : 0)];

	apdu[0] = (byte) cla;
	apdu[1] = (byte) ins;
	apdu[2] = (byte) p1;
	apdu[3] = (byte) p2;

	if (withPayload){
	    apdu[4] = (byte) p3;
	    System.arraycopy(in, off, apdu, 5, p3);
	    off = 5 + p3;
	}else{
	    off = 4;
	}

	if (le >= 0)
	    apdu[off] = (byte)le;

	return apdu;
    }

    /**
     * Reset the buffer.
     */
    public final void reset(){
	this.len = 0;
    }

    /**
     * Reset Apdu, reallocate buffer.
     */
    public final void reset(int len){
	this.buf = new byte[len];
	this.len = 0;
    }


    /**
     * Return internal buffer. Available to Card.Transmit().
     */
    final byte[] getBuffer(){
	return buf;
    }

    /**
     * Return length of APDU in the internal buffer. Available to Card.Transmit().
     */
    final int getLength(){
	return len;
    }

    /**
     * Copy the currently defined APDU to given buffer.
     */
    public final void getBytes(byte[] ba, int off){
	System.arraycopy(this.buf, 0, ba, off, this.len);
    }

    /**
     * Copy the given APDU to the internal buffer.
     */
    public final void set(byte[] ba){
	set(ba, 0, ba.length);
    }

    /**
     * Copy the given APDU (range from a byte array) to the internal buffer.
     */
    public final void set(byte[] ba, int off, int len){
	System.arraycopy(ba, off, buf, 0, len);
	this.len = len;
    }

    /**
     * Create an APDU from the given data.
     */
    public final void set(int cla, int ins, int p1, int p2, int p3, byte[] in, int off, int le){
	// payload length
	int m = ((in == null) ? 0 : p3);
        // 6 = 5 byte header + 1 byte LE
	if (6 + m > buf.length)
	    throw new ArrayIndexOutOfBoundsException("APDU buffer too small: requested size " + (6 + m));
	
	this.len = 6 + m;
	this.buf[0] = (byte) cla;
	this.buf[1] = (byte) ins;
	this.buf[2] = (byte) p1;
	this.buf[3] = (byte) p2;
	if (p3 >= 0){
	    this.buf[4] = (byte) p3;
	    if (in !=null){
		System.arraycopy(in, off, buf, 5, p3);
		off = p3 + 5;
	    }else{
		off = 5;
	    }
	}else{
	    off = 5;
	}
	if (le >= 0)
	    buf[off++] = (byte)le;
    }


    /**
     * Create APDU payload from given data. P3 is initialized to zero.
     * @param cla  CLA byte of APDU (byte #0)
     * @param ins  INS byte of APDU (byte #1)
     * @param p1   P1  byte of APDU (byte #2)
     * @param p2   P2  byte of APDU (byte #3)
     */
    public final void set(int cla, int ins, int p1, int p2){
	this.buf[0] = (byte) cla;
	this.buf[1] = (byte) ins;
	this.buf[2] = (byte) p1;
	this.buf[3] = (byte) p2;
	this.buf[4] = (byte) 0;
	this.len = 5;
    }

    /**
     * Set APDU data from given string. The APDU buffer size must have been
     * allocated accordingly before.
     * @see #s2ba s2ba() for the possible string format
     */
    public final void set(String s){
	int len = s2ba(s, this.buf, 0);
	this.len = len;
    }

    /**
     * Add a data byte to the APDU. The LC byte of the APDU is updated accordingly.
     * The payload has to be already defined.
     */
    public final void addByte(int b){
	addByte((byte) b);
    }

    /**
     * Add a data byte to the APDU. The LC byte of the APDU is updated accordingly.
     * The payload has to be already defined.
     */
    public final void addByte(byte b){
	++this.buf[4];
	this.buf[this.len++] = b;
    }

    /**
     * Add a string representing data to the APDU data area.
     * The payload has to be already defined.
     * @see #s2ba s2ba() for the possible string format
     */
    public final void addString(String s){
	int len = s2ba(s, this.buf, this.len);
	this.buf[4] += len;
	this.len += len;
    }

    /**
     * Add expected length of data. This byte is omitted if parameter has value -1, otherwise it 
     * contains number of bytes expected from card.
     */
    public final void addLe(int le){
	if (le < 0) return;
	this.buf[this.len++] = (byte)le;
    }


    /**
     * ApduWrapper wraps apdu data before sending to the card. It is
     * expected corresponding cardlet will unwrap the apdu. Adding secure
     * messaging to apdu is one type of wrapping.
     */
    public interface Wrapper {
	/**
	 *	Wrap the apdu buffer.
	 *  @param	apduBuffer	buffer contains apdu data. It must be large
	 *                      enough to receive the wrapped apdu.
	 *	@param	len			length of apdu data
	 *  @return length of apdu data after wrapped
	 */
	public int wrap (byte [] apduBuffer, int len) throws java.rmi.RemoteException ;
    }

    /**
     * Wrap the apdu buffer.
     * @param wrapper		
     */
    public void wrapWith (Wrapper wrapper) throws java.rmi.RemoteException {		
	this.len=wrapper.wrap (buf,len);
     }

    /** Serialization support method */
    private void writeObject(java.io.ObjectOutputStream out) throws IOException {
	out.writeInt (len);		
	writeByteArray (out, buf);
    }
 
    /** Serialization support method */
    private void readObject(java.io.ObjectInputStream in) throws IOException, ClassNotFoundException {
	len			= in.readInt();
	buf			= readByteArray (in);
    }
 
    /** Serialization support method */
    private byte [] readByteArray (java.io.ObjectInputStream in) throws IOException {
	byte [] buf=null;
	
	int len = in.readInt ();
	if (len !=0) {
	    buf = new byte [len];
	    in.read (buf, 0, len);
	}
	
	return buf;
    }
 
    /** Serialization support method */
    private void writeByteArray (java.io.ObjectOutputStream out, byte [] buf) throws IOException {
	int len=0;
	
	if (buf != null) len = buf.length;
	out.writeInt (len);
	if (len != 0) out.write ( buf );		
    }
    

 

    /**
     * Return string representation of APDU.
     */
    public String toString(){
	return ba2s(buf, 0, len);
    }

    /**
     * Return string representation of APDU according to given format specification.
     */
    public String toString(Format format){
	return ba2s(buf, 0, len, format);
    }

    /**
     * The Format class described the format to use for converting APDU strings to buffers and vice
     * versa.
     */
    public static class Format{
	/**
	 * Format of data printed.
	 */
	public int dataFormat;
	/**
	 * Prepend string with APDU length.
	 */
	public boolean printLength;
	/**
	 * Append ASCII representation of APDU.
	 */
	public boolean printAscii;
	/**
	 * Constructor.
	 */
	public Format(){
	    dataFormat = HEX_VOID_HEX_FORMAT;
	    printLength = true;
	    printAscii = false;
	}
	/**
	 * Constructor.
	 */
	public Format(int dataFormat, boolean printLength, boolean printAscii){
	    this.dataFormat = dataFormat;
	    this.printLength = printLength;
	    this.printAscii = printAscii;
	}
    }

    /**
     * Default format for convert routines.
     */
    private static Format defaultFormat = new Format();

    /**
     * Helper string.
     */
    private static String digits = "0123456789ABCDEF";

    /**
     * Return string representation for byte array.
     */
    public static String ba2s(byte[] ba){
	return ba2s(ba, 0, ba.length, defaultFormat);
    }

    /**
     * Return string representation for byte array range.
     */
    public static String ba2s(byte[] ba, int off, int len){
	return ba2s(ba, off, len, defaultFormat);
    }

    /**
     * Return string representation for byte array.
     */
    public static String ba2s(byte[] ba, Format f){
	return ba2s(ba, 0, ba.length, f);
    }

    /**
     * Return string representation for byte array range according to given format.
     */
    public static String ba2s(byte[] ba, int off, int len, Format f){
	StringBuffer sb = new StringBuffer();
	if (f.printLength){
	    sb.append(len).append(": ");
	}
	for (int i = off; i < off + len; i++) {
            int b = (int) ba[i];
            char c = digits.charAt((b >> 4) & 0xf);
            sb.append(c);
            c = digits.charAt(b & 0xf);
            sb.append(c);
	    switch(f.dataFormat){
	    case HEX_SPACE_HEX_FORMAT:
		sb.append(' ');
		break;
	    case HEX_COLON_HEX_FORMAT:
		sb.append(':');
		break;
	    case HEX_VOID_HEX_FORMAT:
	    default:
		break;
	    }
	}
	if (f.printAscii){
	    sb.append(' ');
	    for (int i = off; i < off + len; i++) {
		char c = (char) ba[i];
		if (Character.isLetterOrDigit(c)){
		    sb.append(c);
		}else{
		    sb.append('X');
		}
	    }
	}
	return sb.toString();
    }

    /**
     * Convert string to a byte array. Notations supported are
     * 0x00:0xb2 or 0x0:0xb2 or 00:b2 or 00:ba:|symbolic|:... or
     * 00b2 or a0b0|symbolic|a0b0 or
     * 0x00 0xb2 or 0x0 0xb2 or 0x0 0xb2 |symbolic| ...
     */
    public static byte[] s2ba(String s) {
	byte[] ba = new byte[s.length() * 2];
	int len = s2ba(s, ba, 0);
        byte[] ret = new byte[len];
        System.arraycopy(ba, 0, ret, 0, len);
        return ret;
    }

    /**
     * Number of parentheses allowed in string specifications of APDUs.
     */
    private static int MAX_BRACE_CNT = 10;

    /**
     * Convert string to a byte array. Notations supported are
     * 0x00:0xb2 or 0x0:0xb2 or 00:b2 or 00:ba for data bytes.
     * Additionally, | can be used to insert ASCII characters into
     * the byte stream, e.g. 01|abc|01 -> 0161626301
     * Another operator supported is #(...) where at the position of
     * # the length of the byte string between ( and ) is inserted.
     * Examples: #(5566) -> 025566, #(3344)#(55) -> 0233440155,
     * #(11#(22)) -> 03110122, #(11#(|ZZ|)) -> 0411025A5A.
     */
    public static int s2ba(String s, byte[] ba, int off) {
	int[] braceTab = new int[MAX_BRACE_CNT];
	int bracePos = -1;
        boolean asciiMode = false;
        int slen = s.length();
	String n;
	int bpos = off;
        int i = 0;
        byte b;

        while (i < slen) {
            char c = s.charAt(i);
	    if (!asciiMode && (c == ':')){
		i++;
		continue;
	    }
	    if (!asciiMode && (c == ' ')){
		while(s.charAt(++i) == ' ');
		continue;
	    }

	    if (!asciiMode && (c == '#')){
		++i;
		if (s.charAt(i) != '(')
		    throw new RuntimeException("miss ( after # in " + s);
		if (bracePos + 1 >= MAX_BRACE_CNT)
		    throw new RuntimeException("too many ( in APDU spec " + s);
		braceTab[++bracePos] = bpos++;
		++i;
		continue;
	    }
	    if (!asciiMode && (c == ')')){
		if (bracePos < 0)
		    throw new RuntimeException("invalid ) in APDU spec " + s);
		ba[braceTab[bracePos]] = (byte)(bpos - braceTab[bracePos] - 1);
		--bracePos;
		++i;
		continue;
	    }

            if (c == '|'){
		asciiMode = !asciiMode;
                i++;
                continue;
            }

            if (asciiMode){
                if (c >= 256)
                    throw new RuntimeException("invalid character in hex-string " + s);
                b = (byte) ((int) c & 0xff);
                ba[bpos++] = b;
                i++;
                continue;
            }

            try {
                if ((c == '0') && ((s.charAt(i + 1) == 'x') || (s.charAt(i + 1) == 'X'))) {
                    i++;
                    c = s.charAt(i);
                }

                if ((c == 'x') || (c == 'X')) {
                    i++;
                    if ((s.length() == i + 1) || ((s.charAt(i + 1) == ':') || (s.charAt(i + 1) == ' '))){
                        n = s.substring(i, i + 1);
                        i++; // set i on :
                    } else {
                        n = s.substring(i, i + 2);
                        i += 2; // set i on :
                    }
                } else {
                    n = s.substring(i, i + 2);
                    i += 2;
                }

                ba[bpos++] = (byte) (Integer.parseInt(n, 16) & 0xff);
		
            } catch (Exception e) {
                throw new RuntimeException("invalid hexadecimal string " + s);
            }
        }

	if (bracePos >= 0)
	    throw new RuntimeException("mismatched parentheses");
	
        return bpos - off;
    }



    /**
     * Test the convert methods.
     */
    public static void main(String[] args){
	if (args.length == 0){
	    System.out.println("string expected");
	    System.exit(0);
	}
	byte[] ba = s2ba(args[0]);
	System.out.println("RESULT: " + ba2s(ba, 0, ba.length));
    }
}
