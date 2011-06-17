

package com.linuxnet.jpcsc;


/**
 * The Context class wraps the PCSC functions related to 
 * connecting/disconnecting to the PCSC service
 * and card readers. An invocation of Connect() returns
 * a connection to a Card allowing for the transmission
 * of APDUs.
 */
public final class Context{
    /** Dummy empty string array. */
    private static String[] emptyStringArray = new String[0];;

    /** Static initializer. */
    static {
	PCSC.initialize();
    }

    /** The native handle. */
    private long ctx;

    /**
     * Constructor. Try to use established contexts as much as possible.
     * This keeps the number of underlying connections to the PCSC-daemon
     * low.
     */
    public Context(){}
    
    /**
     * Cleanup operation. Destroy context we have.
     */
    final protected void finalize(){



	NativeReleaseContext();
    }

    /**
     * Establish PCSC context. Note that null is also a valid context on Windows, but not on Linux.
     * @param dwScope  PCSC.SCOPE_USER, PCSC.SCOPE_TERMINAL, PCSC.SCOPE_SYSTEMor PCSC.SCOPE_GLOBAL.
     * @param pvReserved1 unused, may be null.
     * @param pvReserved2 unused, may be null.
     * @return established context handle.
     */
    public final void EstablishContext(int dwScope, String pvReserved1, String pvReserved2){
	if ((dwScope != PCSC.SCOPE_USER) && (dwScope != PCSC.SCOPE_TERMINAL) && (dwScope != PCSC.SCOPE_SYSTEM) && (dwScope != PCSC.SCOPE_GLOBAL))
	    throw new RuntimeException("invalid parameter: set dwScope to SCOPE_USER, SCOPE_TERMINAL, SCOPE_SYSTEM or SCOPE_GLOBAL");
	
	int ret = NativeEstablishContext(dwScope, pvReserved1, pvReserved2);



	if (ret != PCSC.SUCCESS)
	    throw new PCSCException("EstablishContext()", ret);
    }

    /**
     * Release context.
     */
    public final void ReleaseContext(){
	int ret = NativeReleaseContext();



	if (ret != PCSC.SUCCESS)
	    throw new PCSCException("ReleaseContext()", ret);
    }

    /**
     * List all readers in all existing groups.
     * @return array of Strings naming all existing readers in the system.
     */
    public final String[] ListReaders(){
	String[] sa = NativeListReaders();



	if (sa == null) return emptyStringArray;




	return sa;
    }

    /**
     * List all readers in the given group. All existing readers are returned if
     * the passed group is null.
     * @param group name of the reader group.
     * @return array of Strings naming the readers of the given group.
     */
    public final String[] ListReaders(String group){
	String[] sa = NativeListReaders(group);



	if (sa == null) return emptyStringArray;




	return sa;
    }

    /**
     * List all readers in the given groups. All existing readers are returned if
     * the passed parameter is null.
     * @param groups arrays of Strings naming the groups.
     * @return array of Strings naming the readers of the given groups.
     * @throws IllegalArgumentException if one of the group names is null.
     */
    public final String[] ListReaders(String[] groups){
	for (int i = 0; i < groups.length; i++){
	    if (groups[i] == null)
		throw new IllegalArgumentException("invalid argument: array of reader names contains null element");
	}
	String[] sa = NativeListReaders(groups);



	if (sa == null) return emptyStringArray;




	return sa;
    }

    /**
     * List all reader groups known to the system.
     * @return array of Strings naming the existing reader groups.
     */
    public final String[] ListReaderGroups(){
	String[] sa = NativeListReaderGroups();



	if (sa == null) return emptyStringArray;




	return sa;
    }


    /**
     * This method blocks until a card is inserted into a reader, or the specified
     * time has been expired. Pass PCSC.INFINITE to block indefinitely. Null is returned
     * if no readers are available, the time has been expired or some other 
     * state change has been detected.
     * @param millis Waiting time, pass PCSC.INFINITE for indefinite waiting time.
     * @return the reader state of the reader the card has been inserted, or null if no
     * reader is currently available, the time has been expired or some other state change has 
     * been detected.
     */
    public State WaitForCard(int millis){
	// first get list of available readers
	String[] sa = ListReaders();
	if (sa.length == 0)
	    return null;
	State[] states = new State[sa.length];
	for (int i = 0; i < sa.length; i++){
	    states[i] = new State(sa[i], PCSC.STATE_UNAWARE);
	}
	// now call GetStatusChange and return immediately to find out the current 
	// state of the readers, reuse their states so that the
	// next call of GetStatusChange blocks.



	GetStatusChange(0, states);




	for (int i = 0; i < states.length; i++){
	    if ((states[i].dwEventState & PCSC.STATE_PRESENT) != 0){
		return states[i];
	    }
	    states[i].dwCurrentState = states[i].dwEventState&~PCSC.STATE_CHANGED;
	}
	
	boolean timedOut = GetStatusChange(millis, states);
	if (timedOut)
	    return null;

	for (int i = 0; i < states.length; i++){
	    if ((states[i].dwEventState & PCSC.STATE_PRESENT) != 0){
		return states[i];
	    }
	}

	return null;
    }


    /**
     * This method blocks until a card is inserted into the specified reader, or the specified
     * time has been expired. Pass PCSC.INFINITE to block indefinitely.
     * @param millis Waiting time, pass PCSC.INFINITE to wait indefinitely.
     * @return the reader state of the reader if a card has been inserted, or null, if the the time has 
     * been expired or some other state change has been detected.
     */
    public State WaitForCard(String rdrName, int millis){
	State state = new State(rdrName);
	State states[] = new State[1];
	states[0] = state;

	GetStatusChange(0, states);

	if ((state.dwEventState & PCSC.STATE_PRESENT) != 0)
	    return state;

	state.dwCurrentState = state.dwEventState&~PCSC.STATE_CHANGED;
	
	boolean timedOut = GetStatusChange(millis, states);
	if (timedOut)
	    return null;

	if ((state.dwEventState & PCSC.STATE_PRESENT) != 0)
	    return state;

	return null;
    }

    
    /**
     * Return status change of a set of readers. For each reader, a State object has to be 
     * allocated and passed. The State object must be properly instantiated, especially with the 
     * name of an existing reader. The method then blocks for the given timeout or foerever 
     * (if PCSC.INFINITE is passed) until the state of one of the readers changes according to the 
     * bits in the dwCurrentState fields in the passed State objects. Refer to the PCSClite documentation 
     * for more information about the possible values for the dwCurrentState field.<br>
     * By default, PCSC.STATE_UNAWARE is set for dwCurrentField in a newly allocated
     * State object. In this case, the method returns immediately with the current state 
     * of the readers stored in the dwEventState fields.<br> 
     * You may want to use WaitForCard() to block until a card is inserted in a reader.<br>
     * If null is passed for the readerStates parameter, the method will block until
     * a reader is present in the system.<br>
     * @param timeout time to wait blocked until status changes as requested.
     * @param readerStates array of State objects naming events and readers to observe.
     * @return true if timeout has occured, false otherwise.
     */
    public final boolean GetStatusChange(int timeout, State[] readerStates){
	int ret = NativeGetStatusChange(timeout, readerStates);
	if (ret == PCSC.E_TIMEOUT)
	    return true;

	if (ret != PCSC.SUCCESS)
	    throw new PCSCException("GetStatusChange()", ret);

	return false;
    }

    /**
     * Connect to a reader. This method blocks until a reader is available in the system and a card
     * is inserted. It then returns a shared connection to this card using either protocol T=0 or
     * T=1.
     * @return handle to card for APDU exchange.
     */
    public final Card Connect(){
	return Connect(PCSC.SHARE_SHARED, PCSC.PROTOCOL_ANY);
    }
    
    /**
     * Connect to a reader. This method blocks until a reader is available in the system and a card
     * is inserted. It then returns a connection to this card with the given sharing mode and for the given protocol.
     * @param dwShareMode  PCSC.SHARE_EXCLUSIVE, PCSC.SHARE_SHARED or PCSC.SHARE_DIRECT.
     * @param dwPreferredProtocols PCSC.PROTOCOL_T0, PCSC.PROTOCOL_T1, PCSC.PROTOCOL_RAW, PCSC.PROTOCOL_ANY.
     * @return handle to card for APDU exchange.
     */
    public final Card Connect(int dwShareMode, int dwPreferredProtocols){
	String reader = null;
	do{
	    GetStatusChange(PCSC.INFINITE, null);
	    
	    State state = WaitForCard(500);
	    if ((state != null) && ((state.dwEventState & PCSC.STATE_PRESENT) == PCSC.STATE_PRESENT)){
		reader = state.szReader;
	    }
	}while(reader == null);
	return Connect(reader, dwShareMode, dwPreferredProtocols);
    }


    /**
     * Connect to a reader. This method first blocks until a reader is available, and then
     * tries to connect to the specified reader. If the given reader does not exist,
     * an exception is thrown. Otherwise JPCSC tries to connect in the mode SHARE_SHARED
     * and for the PROTOCOL_T0 or PROTOCOL_T1. An exception occurs if the connect does not
     * succeed.
     * @param szReader name of the reader, must not be null.
     * @return handle to card for APDU exchange.
     */
    public final Card Connect(String szReader){
	if (szReader == null) throw new NullPointerException("reader name must not be null");
	GetStatusChange(PCSC.INFINITE, null);
	Card c = new Card();
	NativeConnect(c, szReader, PCSC.SHARE_SHARED, PCSC.PROTOCOL_T0|PCSC.PROTOCOL_T1);
	return c;
    }
    

    /**
     * Connect to a reader and return handle to card. Parameters are the reader name
     * to connect to, sharing mode (exclusive, shared, direct), and preferred
     * protocol (PROTOCOL_T0, PROTOCOL_T1, PROTOCOL_RAW, PROTOCOL_ANY). 
     * @param szReader name of the reader, must not be null
     * @param dwShareMode  PCSC.SHARE_EXCLUSIVE, PCSC.SHARE_SHARED or PCSC.SHARE_DIRECT.
     * @param dwPreferredProtocols PCSC.PROTOCOL_T0, PCSC.PROTOCOL_T1, PCSC.PROTOCOL_RAW, PCSC.PROTOCOL_ANY.
     * @return handle to card for APDU exchange.
     */
    public final Card Connect(String szReader, int dwShareMode, int dwPreferredProtocols){
	if (szReader == null) throw new NullPointerException("reader name must not be null");

	if ((dwPreferredProtocols & (PCSC.PROTOCOL_T0|PCSC.PROTOCOL_T1|PCSC.PROTOCOL_RAW|PCSC.PROTOCOL_ANY)) == 0)
	    throw new RuntimeException("invalid parameter: set dwPreferredProtocols to PROTOCOL_ANY, PROTOCOL_RAW, PROTOCOL_T0 or PROTOCOL_T1");

	if ((dwShareMode != PCSC.SHARE_EXCLUSIVE) && (dwShareMode != PCSC.SHARE_SHARED) && (dwShareMode != PCSC.SHARE_DIRECT))
	    throw new RuntimeException("invalid parameter: set dwShareMode to SHARE_DIRECT, SHARE_SHARED or SHARE_EXCLUSIVE");

	Card c = new Card();
	int ret = NativeConnect(c, szReader, dwShareMode, dwPreferredProtocols);
	if (ret != PCSC.SUCCESS)
	    throw new PCSCException("Connect()", ret);
	return c;
    }

    /**
     * Cancel all pending GetStatusChange() calls.
     */
    public final void Cancel(){
	int ret = NativeCancel();
	if (ret != PCSC.SUCCESS)
	    throw new PCSCException("Cancel()", ret);
    }

    /**
     * Return symbolic representation of an error. Uses
     * pcsc_stringify_error() on Linux.
     */
    public native static String StringifyError(int code);

    private native int NativeEstablishContext(int dwScope, String pvReserved1, String pvReserved2);

    private native int NativeCancel();

    private native int NativeReleaseContext();
    
    private native String[] NativeListReaders();

    private native String[] NativeListReaders(String group);

    private native String[] NativeListReaders(String[] groups);

    private native String[] NativeListReaderGroups();

    private native int NativeGetStatusChange(int timeout, State[] readerStates);

    private native int NativeConnect(Card card, String szReader, int dwShareMode, int dwPreferredProtocols);
}
