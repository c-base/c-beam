package PCSC_PACKAGE_NAME;


/**
 * Warning, Error, Parameter Codes.
 */
public final class PCSC{
    /**
     * Name of the native library we depend on.
     */
    public static final String pcscNativeLibName = "jpcsc";

    /**
     * Note that PCSC Lite versions up to 0.8.2 return 1 instead of 0 on success
     * and thus do not match JPCSC.
     */
    public final static int SUCCESS;

    /** Scope in user space */
    public static final int SCOPE_USER;
    /** Scope in terminal   */
    public static final int SCOPE_TERMINAL;
    /** Scope in system     */
    public static final int SCOPE_SYSTEM;
    /** Scope is global, mapped on SCOPE_SYSTEM on Windows */
    public static final int SCOPE_GLOBAL;

    /** T=0 active protocol. */
    public static final int PROTOCOL_T0;
    /** T=1 active protocol. */
    public static final int PROTOCOL_T1;
    /** Raw active protocol. */
    public static final int PROTOCOL_RAW;
    /** IFD determines protocol. */
    public static final int PROTOCOL_ANY;
    /** IFD determines protocol. */
    public static final int PROTOCOL_DEFAULT;


    /** Exclusive mode only  */
    public static final int SHARE_EXCLUSIVE;
    /** Shared mode only     */
    public static final int SHARE_SHARED;
    /** Raw mode only */
    public static final int SHARE_DIRECT;


    /** Do nothing on close  */
    public static final int LEAVE_CARD;
    /** Reset on close       */
    public static final int RESET_CARD;
    /** Power down on close  */
    public static final int UNPOWER_CARD;
    /** Eject on close       */  
    public static final int EJECT_CARD;

    /** Unknown state        */   
    public static final int UNKNOWN;
    /** Card is absent       */
    public static final int ABSENT;
    /** Card is present      */
    public static final int PRESENT;
    /** Card not powered     */
    public static final int SWALLOWED;
    /** Card is powered      */
    public static final int POWERED;
    /** Ready for PTS        */
    public static final int NEGOTIABLE;
    /** PTS has been set     */
    public static final int SPECIFIC;

    /** App wants status     */
    public static final int STATE_UNAWARE;
    /** Ignore this reader   */
    public static final int STATE_IGNORE;
    /** State has changed    */
    public static final int STATE_CHANGED;
    /** Reader unknown       */
    public static final int STATE_UNKNOWN;
    /** Status unavailable   */
    public static final int STATE_UNAVAILABLE;
    /** Card removed         */
    public static final int STATE_EMPTY;
    /** Card inserted        */
    public static final int STATE_PRESENT;
    /** ATR matches card 	*/
    public static final int STATE_ATRMATCH;
    /** Exclusive Mode       */
    public static final int STATE_EXCLUSIVE;
    /** Shared Mode          */
    public static final int STATE_INUSE;
    /** Unresponsive card    */
    public static final int STATE_MUTE;

    /** Error code */
    public static final int  E_CANCELLED;
    /** Error code */
    public static final int  E_CANT_DISPOSE;
    /** Error code */
    public static final int  E_INSUFFICIENT_BUFFER;
    /** Error code */
    public static final int  E_INVALID_ATR;
    /** Error code */
    public static final int  E_INVALID_HANDLE;
    /** Error code */
    public static final int  E_INVALID_PARAMETER;
    /** Error code */
    public static final int  E_INVALID_TARGET;
    /** Error code */
    public static final int  E_INVALID_VALUE;
    /** Error code */
    public static final int  E_NO_MEMORY;
    /** Error code */
    public static final int  F_COMM_ERROR;
    /** Error code */
    public static final int  F_INTERNAL_ERROR;
    /** Error code */
    public static final int  F_UNKNOWN_ERROR;
    /** Error code */
    public static final int  F_WAITED_TOO_LONG;
    /** Error code */
    public static final int  E_UNKNOWN_READER;
    /** Error code */
    public static final int  E_TIMEOUT;
    /** Error code */
    public static final int  E_SHARING_VIOLATION;
    /** Error code */
    public static final int  E_NO_SMARTCARD;
    /** Error code */
    public static final int  E_UNKNOWN_CARD;
    /** Error code */
    public static final int  E_PROTO_MISMATCH;
    /** Error code */
    public static final int  E_NOT_READY;
    /** Error code */
    public static final int  E_SYSTEM_CANCELLED;
    /** Error code */
    public static final int  E_NOT_TRANSACTED;
    /** Error code */
    public static final int  E_READER_UNAVAILABLE;
    
    /** Warning code */
    public static final int  W_UNSUPPORTED_CARD;
    /** Warning code */
    public static final int  W_UNRESPONSIVE_CARD;
    /** Warning code */
    public static final int  W_UNPOWERED_CARD;
    /** Warning code */
    public static final int  W_RESET_CARD;
    /** Warning code */
    public static final int  W_REMOVED_CARD;

    /** Error code */
    public static final int  E_PCI_TOO_SMALL;
    /** Error code */
    public static final int  E_READER_UNSUPPORTED;
    /** Error code */
    public static final int  E_DUPLICATE_READER;
    /** Error code */
    public static final int  E_CARD_UNSUPPORTED;
    /** Error code */
    public static final int  E_NO_SERVICE;
    /** Error code */
    public static final int  E_SERVICE_STOPPED;

    /** Infinite timeout. */
    public static final int  INFINITE;

        /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_VENDOR_NAME;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_VENDOR_IFD_TYPE;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_VENDOR_IFD_VERSION;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_VENDOR_IFD_SERIAL_NO;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_CHANNEL_ID;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_ASYNC_PROTOCOL_TYPES;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_DEFAULT_CLK;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_MAX_CLK;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_DEFAULT_DATA_RATE;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_MAX_DATA_RATE;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_MAX_IFSD;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_SYNC_PROTOCOL_TYPES;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_POWER_MGMT_SUPPORT;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_USER_TO_CARD_AUTH_DEVICE;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_USER_AUTH_INPUT_DEVICE;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_CHARACTERISTICS;

    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_CURRENT_PROTOCOL_TYPE;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_CURRENT_CLK;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_CURRENT_F;
   /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_CURRENT_D;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_CURRENT_N;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_CURRENT_W;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_CURRENT_IFSC;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_CURRENT_IFSD;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_CURRENT_BWT;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_CURRENT_CWT;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_CURRENT_EBC_ENCODING;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_EXTENDED_BWT;

    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_ICC_PRESENCE;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_ICC_INTERFACE_STATUS;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_CURRENT_IO_STATE;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_ATR_STRING;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_ICC_TYPE_PER_ATR;

    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_ESC_RESET;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_ESC_CANCEL;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_ESC_AUTHREQUEST;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_MAXINPUT;

    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_DEVICE_UNIT;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_DEVICE_IN_USE;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_DEVICE_FRIENDLY_NAME_A;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_DEVICE_SYSTEM_NAME_A;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_DEVICE_FRIENDLY_NAME_W;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_DEVICE_SYSTEM_NAME_W;
    /** Tag for requesting card and reader attributes */
    public static final int  SCARD_ATTR_SUPRESS_T1_IFS_REQUEST;


    static{
	Runtime.getRuntime().loadLibrary(PCSC.pcscNativeLibName);

	int[] codes = null;
	codes = NativeInitialize(Context.class, Card.class, State.class);

	SUCCESS = codes[0];

	SCOPE_USER = codes[1];
	SCOPE_TERMINAL = codes[2];
	SCOPE_SYSTEM = codes[3];
	SCOPE_GLOBAL = codes[4];

	PROTOCOL_T0 = codes[5];
	PROTOCOL_T1 = codes[6];
	PROTOCOL_RAW = codes[7];
	PROTOCOL_ANY = codes[8];
	PROTOCOL_DEFAULT = PROTOCOL_ANY;
	
	SHARE_EXCLUSIVE = codes[9];
	SHARE_SHARED = codes[10];
	SHARE_DIRECT = codes[11];

	LEAVE_CARD = codes[12];
	RESET_CARD = codes[13];
	UNPOWER_CARD = codes[14];
	EJECT_CARD = codes[15];

	UNKNOWN = codes[16];
	ABSENT = codes[17];
	PRESENT = codes[18];
	SWALLOWED = codes[19];
	POWERED = codes[20];
	NEGOTIABLE = codes[21];
	SPECIFIC = codes[22];

	STATE_UNAWARE = codes[23];
	STATE_IGNORE = codes[24];
	STATE_CHANGED = codes[25];
	STATE_UNKNOWN = codes[26];
	STATE_UNAVAILABLE = codes[27];
	STATE_EMPTY = codes[28];
	STATE_PRESENT = codes[29];
	STATE_ATRMATCH = codes[30];
	STATE_EXCLUSIVE = codes[31];
	STATE_INUSE = codes[32];
	STATE_MUTE = codes[33];

	E_CANCELLED = codes[34];
	E_CANT_DISPOSE = codes[35];
	E_INSUFFICIENT_BUFFER = codes[36];
	E_INVALID_ATR = codes[37];
	E_INVALID_HANDLE = codes[38];
	E_INVALID_PARAMETER = codes[39];
	E_INVALID_TARGET = codes[40];
	E_INVALID_VALUE = codes[41];
	E_NO_MEMORY = codes[42];
	F_COMM_ERROR = codes[43];
	F_INTERNAL_ERROR = codes[44];
	F_UNKNOWN_ERROR = codes[45];
	F_WAITED_TOO_LONG = codes[46];
	E_UNKNOWN_READER = codes[47];
	E_TIMEOUT = codes[48];
	E_SHARING_VIOLATION = codes[49];
	E_NO_SMARTCARD = codes[50];
	E_UNKNOWN_CARD = codes[51];
	E_PROTO_MISMATCH = codes[52];
	E_NOT_READY = codes[53];
	E_SYSTEM_CANCELLED = codes[54];
	E_NOT_TRANSACTED = codes[55];
	E_READER_UNAVAILABLE = codes[56];
    
	W_UNSUPPORTED_CARD = codes[57];
	W_UNRESPONSIVE_CARD = codes[58];
	W_UNPOWERED_CARD = codes[59];
	W_RESET_CARD = codes[60];
	W_REMOVED_CARD = codes[61];

	E_PCI_TOO_SMALL = codes[62];
	E_READER_UNSUPPORTED = codes[63];
	E_DUPLICATE_READER = codes[64];
	E_CARD_UNSUPPORTED = codes[65];
	E_NO_SERVICE = codes[66];
	E_SERVICE_STOPPED = codes[67];

	INFINITE = codes[68];

	SCARD_ATTR_VENDOR_NAME = codes[69];
	SCARD_ATTR_VENDOR_IFD_TYPE = codes[70];
	SCARD_ATTR_VENDOR_IFD_VERSION = codes[71];
	SCARD_ATTR_VENDOR_IFD_SERIAL_NO = codes[72];
	SCARD_ATTR_CHANNEL_ID = codes[73];
	SCARD_ATTR_ASYNC_PROTOCOL_TYPES = codes[74];
	SCARD_ATTR_DEFAULT_CLK = codes[75];
	SCARD_ATTR_MAX_CLK = codes[76];
	SCARD_ATTR_DEFAULT_DATA_RATE = codes[77];
	SCARD_ATTR_MAX_DATA_RATE = codes[78];
	SCARD_ATTR_MAX_IFSD = codes[79];
	SCARD_ATTR_SYNC_PROTOCOL_TYPES = codes[80];
	SCARD_ATTR_POWER_MGMT_SUPPORT = codes[81];
	SCARD_ATTR_USER_TO_CARD_AUTH_DEVICE = codes[82];
	SCARD_ATTR_USER_AUTH_INPUT_DEVICE = codes[83];
	SCARD_ATTR_CHARACTERISTICS = codes[84];

	SCARD_ATTR_CURRENT_PROTOCOL_TYPE = codes[85];
	SCARD_ATTR_CURRENT_CLK = codes[86];
	SCARD_ATTR_CURRENT_F = codes[87];
	SCARD_ATTR_CURRENT_D = codes[88];
	SCARD_ATTR_CURRENT_N = codes[89];
	SCARD_ATTR_CURRENT_W = codes[90];
	SCARD_ATTR_CURRENT_IFSC = codes[91];
	SCARD_ATTR_CURRENT_IFSD = codes[92];
	SCARD_ATTR_CURRENT_BWT = codes[93];
	SCARD_ATTR_CURRENT_CWT = codes[94];
	SCARD_ATTR_CURRENT_EBC_ENCODING = codes[95];
	SCARD_ATTR_EXTENDED_BWT = codes[96];

	SCARD_ATTR_ICC_PRESENCE = codes[97];
	SCARD_ATTR_ICC_INTERFACE_STATUS = codes[98];
	SCARD_ATTR_CURRENT_IO_STATE = codes[99];
	SCARD_ATTR_ATR_STRING = codes[100];
	SCARD_ATTR_ICC_TYPE_PER_ATR = codes[101];

	SCARD_ATTR_ESC_RESET = codes[102];
	SCARD_ATTR_ESC_CANCEL = codes[103];
	SCARD_ATTR_ESC_AUTHREQUEST = codes[104];
	SCARD_ATTR_MAXINPUT = codes[105];

	SCARD_ATTR_DEVICE_UNIT = codes[106];
	SCARD_ATTR_DEVICE_IN_USE = codes[107];
	SCARD_ATTR_DEVICE_FRIENDLY_NAME_A = codes[108];
	SCARD_ATTR_DEVICE_SYSTEM_NAME_A = codes[109];
	SCARD_ATTR_DEVICE_FRIENDLY_NAME_W = codes[110];
	SCARD_ATTR_DEVICE_SYSTEM_NAME_W = codes[111];
	SCARD_ATTR_SUPRESS_T1_IFS_REQUEST = codes[112];
    }
    
    
    static void initialize(){
	// all initialization takes place in the static initializer so far ...
	return;
    }
    
    static native int[] NativeInitialize(Class ctxClass, Class cardClass, Class stateClass);
    
#ifdef DEBUG
    /**
     * Print values of codes dependent on underlying platform.
     */
    public static void log(){
	System.out.println("Constants:");
	System.out.println("SUCCESS: " + Integer.toHexString(PCSC.SUCCESS));
	System.out.println("SCOPE_USER: " + Integer.toHexString(PCSC.SCOPE_USER));
	System.out.println("SCOPE_TERMINAL: " + Integer.toHexString(PCSC.SCOPE_TERMINAL));
	System.out.println("SCOPE_SYSTEM: " + Integer.toHexString(PCSC.SCOPE_SYSTEM));
	System.out.println("SCOPE_GLOBAL: " + Integer.toHexString(PCSC.SCOPE_GLOBAL));
	System.out.println("PROTOCOL_T0: " + Integer.toHexString(PCSC.PROTOCOL_T0));
	System.out.println("PROTOCOL_T1: " + Integer.toHexString(PCSC.PROTOCOL_T1));
	System.out.println("PROTOCOL_RAW: " + Integer.toHexString(PCSC.PROTOCOL_RAW));
	System.out.println("PROTOCOL_ANY: " + Integer.toHexString(PCSC.PROTOCOL_ANY));
	System.out.println("SHARE_EXCLUSIVE: " + Integer.toHexString(PCSC.SHARE_EXCLUSIVE));
	System.out.println("SHARE_SHARED: " + Integer.toHexString(PCSC.SHARE_SHARED));
	System.out.println("SHARE_DIRECT: " + Integer.toHexString(PCSC.SHARE_DIRECT));
	System.out.println("LEAVE_CARD: " + Integer.toHexString(PCSC.LEAVE_CARD));
	System.out.println("RESET_CARD: " + Integer.toHexString(PCSC.RESET_CARD));
	System.out.println("UNPOWER_CARD: " + Integer.toHexString(PCSC.UNPOWER_CARD));
	System.out.println("EJECT_CARD: " + Integer.toHexString(PCSC.EJECT_CARD));
	System.out.println("UNKNOWN: " + Integer.toHexString(PCSC.UNKNOWN));
	System.out.println("ABSENT: " + Integer.toHexString(PCSC.ABSENT));
	System.out.println("PRESENT: " + Integer.toHexString(PCSC.PRESENT));
	System.out.println("SWALLOWED: " + Integer.toHexString(PCSC.SWALLOWED));
	System.out.println("POWERED: " + Integer.toHexString(PCSC.POWERED));
	System.out.println("NEGOTIABLE: " + Integer.toHexString(PCSC.NEGOTIABLE));
	System.out.println("SPECIFIC: " + Integer.toHexString(PCSC.SPECIFIC));
	System.out.println("STATE_UNAWARE: " + Integer.toHexString(PCSC.STATE_UNAWARE));
	System.out.println("STATE_IGNORE: " + Integer.toHexString(PCSC.STATE_IGNORE));
	System.out.println("STATE_CHANGED: " + Integer.toHexString(PCSC.STATE_CHANGED));
	System.out.println("STATE_UNKNOWN: " + Integer.toHexString(PCSC.STATE_UNKNOWN));
	System.out.println("STATE_UNAVAILABLE: " + Integer.toHexString(PCSC.STATE_UNAVAILABLE));
	System.out.println("STATE_EMPTY: " + Integer.toHexString(PCSC.STATE_EMPTY));
	System.out.println("STATE_PRESENT: " + Integer.toHexString(PCSC.STATE_PRESENT));
	System.out.println("STATE_ATRMATCH: " + Integer.toHexString(PCSC.STATE_ATRMATCH));
	System.out.println("STATE_EXCLUSIVE: " + Integer.toHexString(PCSC.STATE_EXCLUSIVE));
	System.out.println("STATE_INUSE: " + Integer.toHexString(PCSC.STATE_INUSE));
	System.out.println("STATE_MUTE: " + Integer.toHexString(PCSC.STATE_MUTE));
	System.out.println("E_CANCELLED: " + Integer.toHexString(PCSC.E_CANCELLED));
	System.out.println("E_CANT_DISPOSE: " + Integer.toHexString(PCSC.E_CANT_DISPOSE));
	System.out.println("E_INSUFFICIENT_BUFFER: " + Integer.toHexString(PCSC.E_INSUFFICIENT_BUFFER));
	System.out.println("E_INVALID_ATR: " + Integer.toHexString(PCSC.E_INVALID_ATR));
	System.out.println("E_INVALID_HANDLE: " + Integer.toHexString(PCSC.E_INVALID_HANDLE));
	System.out.println("E_INVALID_PARAMETER: " + Integer.toHexString(PCSC.E_INVALID_PARAMETER));
	System.out.println("E_INVALID_TARGET: " + Integer.toHexString(PCSC.E_INVALID_TARGET));
	System.out.println("E_INVALID_VALUE: " + Integer.toHexString(PCSC.E_INVALID_VALUE));
	System.out.println("E_NO_MEMORY: " + Integer.toHexString(PCSC.E_NO_MEMORY));
	System.out.println("F_COMM_ERROR: " + Integer.toHexString(PCSC.F_COMM_ERROR));
	System.out.println("F_INTERNAL_ERROR: " + Integer.toHexString(PCSC.F_INTERNAL_ERROR));
	System.out.println("F_UNKNOWN_ERROR: " + Integer.toHexString(PCSC.F_UNKNOWN_ERROR));
	System.out.println("F_WAITED_TOO_LONG: " + Integer.toHexString(PCSC.F_WAITED_TOO_LONG));
	System.out.println("E_UNKNOWN_READER: " + Integer.toHexString(PCSC.E_UNKNOWN_READER));
	System.out.println("E_TIMEOUT: " + Integer.toHexString(PCSC.E_TIMEOUT));
	System.out.println("E_SHARING_VIOLATION: " + Integer.toHexString(PCSC.E_SHARING_VIOLATION));
	System.out.println("E_NO_SMARTCARD: " + Integer.toHexString(PCSC.E_NO_SMARTCARD));
	System.out.println("E_UNKNOWN_CARD: " + Integer.toHexString(PCSC.E_UNKNOWN_CARD));
	System.out.println("E_PROTO_MISMATCH: " + Integer.toHexString(PCSC.E_PROTO_MISMATCH));
	System.out.println("E_NOT_READY: " + Integer.toHexString(PCSC.E_NOT_READY));
	System.out.println("E_SYSTEM_CANCELLED: " + Integer.toHexString(PCSC.E_SYSTEM_CANCELLED));
	System.out.println("E_NOT_TRANSACTED: " + Integer.toHexString(PCSC.E_NOT_TRANSACTED));
	System.out.println("E_READER_UNAVAILABLE: " + Integer.toHexString(PCSC.E_READER_UNAVAILABLE));
	System.out.println("W_UNSUPPORTED_CARD: " + Integer.toHexString(PCSC.W_UNSUPPORTED_CARD));
	System.out.println("W_UNRESPONSIVE_CARD: " + Integer.toHexString(PCSC.W_UNRESPONSIVE_CARD));
	System.out.println("W_UNPOWERED_CARD: " + Integer.toHexString(PCSC.W_UNPOWERED_CARD));
	System.out.println("W_RESET_CARD: " + Integer.toHexString(PCSC.W_RESET_CARD));
	System.out.println("W_REMOVED_CARD: " + Integer.toHexString(PCSC.W_REMOVED_CARD));
	System.out.println("E_PCI_TOO_SMALL: " + Integer.toHexString(PCSC.E_PCI_TOO_SMALL));
	System.out.println("E_READER_UNSUPPORTED: " + Integer.toHexString(PCSC.E_READER_UNSUPPORTED));
	System.out.println("E_DUPLICATE_READER: " + Integer.toHexString(PCSC.E_DUPLICATE_READER));
	System.out.println("E_CARD_UNSUPPORTED: " + Integer.toHexString(PCSC.E_CARD_UNSUPPORTED));
	System.out.println("E_NO_SERVICE: " + Integer.toHexString(PCSC.E_NO_SERVICE));
	System.out.println("E_SERVICE_STOPPED: " + Integer.toHexString(PCSC.E_SERVICE_STOPPED));
	System.out.println("INFINITE: " + Integer.toHexString(PCSC.INFINITE));
    }
#endif /* DEBUG */    

}
