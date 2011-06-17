package samples;

import java.io.LineNumberReader;
import java.io.InputStreamReader;

import com.linuxnet.jpcsc.*;

/**
 * Miscellaneous functions. 
 */
public class Util{
    /** 
     * Read a line from standard in and trim it. 
     * @return the line read from standard in.
     */
    public static String readLine(String prompt){
	System.out.print(prompt);
	LineNumberReader lnr = new LineNumberReader(new InputStreamReader(System.in));
	String l = null;
	try{
	    l = lnr.readLine();
	}catch(Exception e){
	    throw new RuntimeException("reading from standard in failed");
	}
	l =l.trim();
	return l;
    }


    /** 
     * Ask user on the command line to pick one of the available readers.
     * @return the name of the selected reader, or null if no reader
     * is available.
     */
    public static String stdinPickReader(Context ctx){
	String rn = null;
	while(rn == null){
	    String[] sa = ctx.ListReaders();
	    if (sa.length == 0)
		return null;
	    for (int i = 0; i < sa.length; i++){
		System.out.println("reader " + i + ": " + sa[i]);
	    }
	    String l = readLine("Select reader (1-n): ");
	    int n = 0;
	    try{
		n = Integer.decode(l).intValue();
	    }catch(Exception e){
		System.out.println("Invalid reader index " + l);
		continue;
	    }
	    if ((n < 0) || (n >= sa.length)){
		System.out.println("Invalid reader index " + n);
	    }else{
		rn = sa[n];
	    }
	}
	return rn;
    }


    /** 
     * Wait for a card to be inserted in any of the installed reader. The method will block the 
     * specified time until a card is inserted. Returns the state of the first reader
     * a card has been detected in.
     * @param milis Waiting time, pass PCSC.INFINITE for indefinite waiting time.
     * @return state object with name of reader name a card has inserted to.
     */
    public static State waitForCard(Context ctx, int millis){
	// first get list of available readers
	String[] sa = ctx.ListReaders();
	State[] states = new State[sa.length];
	for (int i = 0; i < sa.length; i++){
	    states[i] = new State(sa[i], PCSC.STATE_UNAWARE);
	}
	while(true){
	    ctx.GetStatusChange(millis, states);
	    for (int i = 0; i < states.length; i++){
		if ((states[i].dwEventState & PCSC.STATE_PRESENT) != 0){
		    return states[i];
		}
		// save the returned state for the next current state to be passed,
		// next call will then be blocking.
		states[i].dwCurrentState = states[i].dwEventState&~PCSC.STATE_CHANGED;
	    }
	}
    }


       
}
