package PCSC_PACKAGE_NAME;


/**
 * Exception class used for PCSC related errors.
 */
public class PCSCException extends RuntimeException{
    /**
     * PCSC status code for failed action.
     */
    private int reason;

    /**
     * Default constructor.
     */
    public PCSCException(){}

    /**
     * Constructor.
     */
    public PCSCException(String msg){
	super(msg);
    }

    /**
     * Constructor.
     */
    public PCSCException(String msg, int reason){
	super(msg);
	this.reason = reason;
    }

    /**
     * Return code.
     */
    public final int getReason(){
	return reason;
    }

    /**
     * Return error message.
     */
    public final String getMessage(){
	String s = super.getMessage();
	return (reason == 0) ? s : s + ": 0x" + Integer.toHexString(reason) + ", " + Context.StringifyError(reason);
    }

    /**
     * Return symbolic representation of this exception. Its message, reason code
     * plus symbolic representation of reason code.
     */
    public final String toString(){
	String s = super.getMessage();
	return (reason == 0) ? s : s + ": 0x" + Integer.toHexString(reason) + ", " + Context.StringifyError(reason);
    }
}
