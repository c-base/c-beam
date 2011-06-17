package PCSC_PACKAGE_NAME;

/**
 * Instances of the States class are used to keep information about the states
 * of connections with readers or cards.
 */
public class State{
    /** Name of the reader. Has to be set for invocations of Context.GetStatusChange() ,
	and is returned by Card.Status(). */
    public String szReader;

    /** Not used. */
    public Object pvUserData;
    
    /** Defaults to PCSC.STATE_UNAWARE. May be set for Context.GetStatusChange() to initiate
	blocking on certain events. The field is also set by Card.Status() to return
	the state of a card connection. */ 
    public int dwCurrentState;

    /** Set by Context.GetStatusChange() to return the status of a reader. */
    public int dwEventState;

    /** Used by Context.getStatusChange() to store the ATR received by a card. The bytearray is
	allocated by the underlying native code. If PCSC.STATE_ATRMATCH is passed to Context.GetStatusChange()
	in dwCurrentState, this array must contain the ATR of the card to be expected. The return
	value is still a newly created array. */
    public byte[] rgbAtr;

    /**  Returned and set by Card.Status() to signal the protocol used by a card connection. */
    public int proto;

    /**
     * Constructor.
     * @param szReader name of the reader, may not be null
     */
    public State(String szReader){
	if (szReader == null){
	    throw new NullPointerException("reader name must not be null");
	}
	this.szReader = szReader;
	dwCurrentState = PCSC.STATE_UNAWARE;
	dwEventState = PCSC.STATE_UNAWARE;
    }

    /**
     * Constructor.
     * @param szReader name of the reader, may not be null.
     * @param dwCurrentState state to set for dwCurrentState.
     */
    public State(String szReader, int dwCurrentState){
	if (szReader == null){
	    throw new NullPointerException("reader name must not be null");
	}
	this.szReader = szReader;
	this.dwCurrentState = dwCurrentState;
	this.dwEventState = PCSC.STATE_UNAWARE;
    }

    /**
     * Default constructor. Not visible package-externally.
     * Thus, szReader may not be checked in the JNI
     * layer for Context.GetStatusChange(), but State 
     * can still be used for Card.Status().
     */
    State(){
	dwCurrentState = PCSC.STATE_UNAWARE;
	dwEventState = PCSC.STATE_UNAWARE;
    }


    /**
     * Return a string representation for either a card status after a Card.GetStatus()
     * or a reader status after a Context.getStatusChange() operation.
     */
    public String toString(boolean forCardGetStatus){
	StringBuffer sb = new StringBuffer();
	sb.append("szReader: ").append(szReader).append('\n');
	if (!forCardGetStatus){
	    sb.append("reader dwCurrentState: 0x").append(Integer.toHexString(dwCurrentState)).append(" (").append(currentReaderStateToString(dwCurrentState)).append(")\n");
	    sb.append("reader dwEventState: 0x").append(Integer.toHexString(dwEventState)).append(" (").append(eventReaderStateToString(dwEventState)).append(")\n");
	}else{
	    sb.append("card dwState: 0x").append(Integer.toHexString(dwCurrentState)).append(" (").append(cardStateToString(dwCurrentState)).append(")\n");
	    sb.append("card proto: ").append(protoToString(proto)).append('\n');
	}
	sb.append("rgbAtr: ");
	if (rgbAtr == null){
	    sb.append("null\n");
	}else{
	    sb.append(Apdu.ba2s(rgbAtr)).append('\n');
	}
	return sb.toString();
    }

    /**
     * Return a string representation. 
     */
    public String toString(){
	StringBuffer sb = new StringBuffer();
	sb.append("szReader: ").append(szReader).append('\n');
	sb.append("dwCurrentState for reader: 0x").append(Integer.toHexString(dwCurrentState)).append(" (").append(currentReaderStateToString(dwCurrentState)).append(")\n");
	sb.append("dwCurrentState for card: 0x").append(Integer.toHexString(dwCurrentState)).append(" (").append(cardStateToString(dwCurrentState)).append(")\n");
	sb.append("dwEventState: 0x").append(Integer.toHexString(dwEventState)).append(" (").append(eventReaderStateToString(dwEventState)).append(")\n");
	sb.append("rgbAtr: ");
	if (rgbAtr == null){
	    sb.append("null\n");
	}else{
	    sb.append(Apdu.ba2s(rgbAtr)).append('\n');
	}
	sb.append("proto: ").append(protoToString(proto)).append('\n');
	return sb.toString();
    }

    /**
     * Return the symbolic representation of the current reader status of a Context.GetStatusChange() operation. 
     */
    private String currentReaderStateToString (int state) {
	StringBuffer sb=new StringBuffer();

	if (PCSC.STATE_UNAWARE != 0)
	    throw new RuntimeException("invalid pcsc installation: STATE_UNAWARE == 0");
	if (state == PCSC.STATE_UNAWARE)                 sb.append ("unware,");
	if ((state & PCSC.STATE_IGNORE) != 0)		 sb.append ("ignore,");
	if ((state & PCSC.STATE_UNAVAILABLE) != 0)	 sb.append("unavailable,");
	if ((state & PCSC.STATE_EMPTY) != 0)		 sb.append("empty,");
	if ((state & PCSC.STATE_PRESENT) != 0)		 sb.append("present,");
	if ((state & PCSC.STATE_ATRMATCH) != 0)		 sb.append("atr match,");
	if ((state & PCSC.STATE_EXCLUSIVE) != 0)	 sb.append("exclusive,");
	if ((state & PCSC.STATE_INUSE) != 0)		 sb.append("in use,");
	if ((state & PCSC.STATE_MUTE) != 0)			 sb.append("mute,");

	/* remove trailing separator, if any */
	if (sb.length() > 0)	return sb.substring(0,sb.length()-1);
	else					return sb.toString();
    }
 
    /**
     * Return the symbolic representation of the event reader status of a Context.GetStatusChange() operation. 
     */
    private String eventReaderStateToString (int state) {
	StringBuffer sb=new StringBuffer();

	if ((state & PCSC.STATE_IGNORE) != 0)		 sb.append ("ignore,");
	if ((state & PCSC.STATE_CHANGED) != 0)		 sb.append ("changed,");
	if ((state & PCSC.STATE_UNKNOWN) != 0)		 sb.append ("unknown,");
	if ((state & PCSC.STATE_UNAVAILABLE) != 0)	 sb.append("unavailable,");
	if ((state & PCSC.STATE_EMPTY) != 0)		 sb.append("empty,");
	if ((state & PCSC.STATE_PRESENT) != 0)		 sb.append("present,");
	if ((state & PCSC.STATE_ATRMATCH) != 0)		 sb.append("atr match,");
	if ((state & PCSC.STATE_EXCLUSIVE) != 0)	 sb.append("exclusive,");
	if ((state & PCSC.STATE_INUSE) != 0)		 sb.append("in use,");
	if ((state & PCSC.STATE_MUTE) != 0)			 sb.append("mute,");

	/* remove trailing separator, if any */
	if (sb.length() > 0)	return sb.substring(0,sb.length()-1);
	else					return sb.toString();
    }


   /**
     * Return the symbolic representation of the status of a Card.GetStatus() operation. 
     */
    public static String cardStateToString (int state) {
	if ((state & PCSC.UNKNOWN) != 0)
	    return "unknown";
	if ((state & PCSC.ABSENT) != 0)
	    return "absent";
	if ((state & PCSC.PRESENT) != 0)
	    return "present";
	if ((state & PCSC.SWALLOWED) != 0) 
	    return "swallowed";
	if ((state & PCSC.POWERED) != 0) 
	    return "powered";
	if ((state & PCSC.NEGOTIABLE) != 0) 
	    return "negotiable";
	if ((state & PCSC.SPECIFIC) != 0) 
	    return "specific";
	return "invalid";
    }

    private String protoToString (int proto) {
	String p=null;
 
	if (proto == PCSC.PROTOCOL_T0)
	    p="T0";
	else if (proto == PCSC.PROTOCOL_T1)
	    p="T1";
	else if (proto == PCSC.PROTOCOL_RAW)
	    p="raw";
	else
	    p=new String ("0x" + Integer.toHexString(proto));
	
	return p;
    }

}
