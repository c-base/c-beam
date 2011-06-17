package samples;

import com.linuxnet.jpcsc.*;

public class Test{
    static final int PROTO=PCSC.PROTOCOL_T0|PCSC.PROTOCOL_T1;

    static final String[] testModes = {
	"FIRST READER SEND",
	"ALL READER SEND",
	"GETSTATUSCHANGE LOOP",
	"SELECT LOOP",
	"ANY READER SEND",
	"GROUP TEST",
	"APDU TEST",
	"LIST READERS TEST",
	"GET STATUS CHANGE NULL TEST",
	"DEFAULT CONNECT",
	"CARD CONTROL", 
	"RAW PCI", 
	"WAIT FOR CARD", 
	"INTERACTIVE",
    };
    
    static final int FIRSTREADER_TEST = 0;
    static final int ALLREADER_TEST = 1;
    static final int GETSTATUSCHANGE_LOOP = 2;
    static final int SELECT_STRESSTEST = 3;
    static final int ANYREADER_TEST = 4;
    static final int GROUP_TEST = 5;
    static final int APDU_TEST = 6;
    static final int LISTREADERS_TEST = 7;
    static final int GETSTATUSCHANGE_NULL = 8;
    static final int DEFAULT_CONNECT = 9;
    static final int CARD_CONTROL = 10;
    static final int RAW_PCI = 11;
    static final int WAIT_FOR_CARD = 12;
    static final int INTERACTIVE = 13;
    
    public static void usage(){
	System.out.println("samples.Test: java sample.Test [mode]");
	for (int i = 0; i < testModes.length; i++){
	    System.out.println("mode " + i + ": " + testModes[i]);
	}
	System.out.println("default mode: 0");
	System.exit(-1);
    }

    public static void main(String[] args){
	int mode = 0;
	
	if (args.length == 0){
	    mode = INTERACTIVE;
	}else{
	    try{
		mode = Integer.decode(args[0]).intValue();
		System.out.println("Chosen mode: " + testModes[mode]);
	    }catch(Exception e){
		usage();
	    }
	}

	switch(mode){
	case FIRSTREADER_TEST:
	case ALLREADER_TEST:
	    readertest(mode);
	    break;
	case GETSTATUSCHANGE_LOOP:
	    statuschangeloop();
	    break;
	case SELECT_STRESSTEST:
	    selectstress();
	    break;
	case ANYREADER_TEST:
	    anytest();
	    break;
	case GROUP_TEST:
	    grouptest();
	    break;
	case APDU_TEST:
	    apdutest();
	    break;
	case LISTREADERS_TEST:
	    listreaderstest();
	    break;
	case GETSTATUSCHANGE_NULL:
	    getstatuschangenulltest();
	    break;
	case DEFAULT_CONNECT:
	    defaultconnect();
	    break;
	case CARD_CONTROL:
	    cardcontrol();
	    break;
	case RAW_PCI:
	    rawpci();
	    break;
	case WAIT_FOR_CARD:
	    waitforcard();
	    break;
	case INTERACTIVE:
	    interactivetest();
	    break;
	default:
	    throw new RuntimeException("internal error");
	}
	    
	System.exit(0);
    }



    /**
     * Ask user to choose a reader, wait for card in reader, print its atr,
     * connect to card, ask for apdu and send it.
     */
    private static void interactivetest(){
	System.out.println("EstablishContext(): ...");
	Context ctx = new Context();
	ctx.EstablishContext(PCSC.SCOPE_SYSTEM, null, null);

	String[] sa = ctx.ListReaders();
	if (sa.length == 0){
	    System.out.println("No reader detected. Make sure reader is avalaiable and start again.");
	    System.exit(1);
	}

	System.out.println("Wait for card in a certain reader ...");
	System.out.println("Pick reader ...");
	String rn = Util.stdinPickReader(ctx);

	System.out.println("Please, insert card into reader " + rn + " ...");
	
	State state = null;
	do{
	    // block until card is inserted
	    state = ctx.WaitForCard(rn, PCSC.INFINITE);
	}while(state == null);
	
	System.out.println("Card inserted into " + state.szReader);
	System.out.println("Card ATR is " + Apdu.ba2s(state.rgbAtr));

	System.out.println("Connect to card " + state.szReader);
	Card card = ctx.Connect(state.szReader, PCSC.SHARE_EXCLUSIVE, PCSC.PROTOCOL_T0|PCSC.PROTOCOL_T1);

	while(true){
	    String l = Util.readLine("Type APDU to send or q to leave: ");
	    if (l.toUpperCase().equals("Q"))
		break;
	    byte[] ba = null;
	    try{
		ba = Apdu.s2ba(l);
	    }catch(Exception e){
		System.out.println("invalid APDU: " + e.getClass() + ", " + e.getMessage());
		continue;
	    }
	    try{
		byte[] response = card.Transmit(ba, 0, ba.length);		
		System.out.println("Response: " + Apdu.ba2s(response));
	    }catch(Exception e){
		System.out.println("sending APDU failed: " + e.getClass() + ", " + e.getMessage());
		continue;
	    }
	}   

	card.Disconnect();
	ctx.ReleaseContext();
    }


    /**
     * RAW protocol, might fail.
     */
    private static void rawpci(){
	try{
	    System.out.println("EstablishContext(): ...");
	    Context ctx = new Context();
	    ctx.EstablishContext(PCSC.SCOPE_SYSTEM, null, null);
	    
	    String[] sa = ctx.ListReaders();
	    if (sa.length == 0){
		throw new RuntimeException("no reader found");
	    }
	    System.out.println("Connect to reader: " + sa[0]);
	    
	    State[] rsa = new State[1];
	    rsa[0] = new State(sa[0]);
	    do{
		ctx.GetStatusChange(1000, rsa);
	    }while((rsa[0].dwEventState & PCSC.STATE_PRESENT) != PCSC.STATE_PRESENT);
	    
	    System.out.println("Connect to card for raw protocol ...");
	    Card card = ctx.Connect(sa[0], PCSC.SHARE_DIRECT, PCSC.PROTOCOL_RAW);
	    
	    System.out.println("Transmit data ...");
	    byte[] b = { (byte) 0x2, (byte) 0x1, (byte) 0x2, (byte) 0x1, (byte) 0x2, (byte) 0x1, };
	    byte[] ret = card.Transmit(b,0,b.length); 

	    System.out.println("Release contexts ...");
	    card.Disconnect(PCSC.LEAVE_CARD);
	    ctx.ReleaseContext();
	}catch(Exception e){
	    System.out.println("RawPci-Test failed: " + e.getClass().getName() + ", " + e.getMessage());
	    e.printStackTrace(System.out);
	    return;
	}
    }


    /**
     * Connect to first reader with card or first PCSC reader if nowhere a card is inserted.
     */
    private static void defaultconnect(){
	System.out.println("EstablishContext(): ...");
	Context ctx = new Context();
	ctx.EstablishContext(PCSC.SCOPE_SYSTEM, null, null);

	Card c1 = ctx.Connect();
	System.out.println("Context.Connect(): default card connection " + c1);
	Card c2 = ctx.Connect();
	System.out.println("Context.Connect(): default card connection " + c2);
	Card c3 = ctx.Connect();
	System.out.println("Context.Connect(): default card connection " + c3);
	Card c4 = ctx.Connect();
	System.out.println("Context.Connect(): default card connection " + c4);
	c1.Disconnect();
	c2.Disconnect();
	c3.Disconnect();
	c4.Disconnect();
    }


    /**
     * Simple call to card control. Unlikely that given control is understood, thus a pure API test.
     */
    private static void cardcontrol(){
	try{
	    System.out.println("EstablishContext(): ...");
	    Context ctx = new Context();
	    ctx.EstablishContext(PCSC.SCOPE_SYSTEM, null, null);
	
	    String[] sa = ctx.ListReaders();
	    if (sa.length == 0){
		throw new RuntimeException("no reader found");
	    }
	    System.out.println("Connect to reader: " + sa[0]);
		
	    State[] rsa = new State[1];
	    rsa[0] = new State(sa[0]);
	    do{
		ctx.GetStatusChange(1000, rsa);
	    }while((rsa[0].dwEventState & PCSC.STATE_PRESENT) != PCSC.STATE_PRESENT);
	    
	    System.out.println("Connect to card ...");
	    Card card = ctx.Connect(sa[0], PCSC.SHARE_EXCLUSIVE, PCSC.PROTOCOL_T0|PCSC.PROTOCOL_T1);


	    System.out.println("Execute card.control() ...");
	    card.Control(0, new byte[0], 0, 0);

	    System.out.println("Release contexts ...");
	    card.Disconnect(PCSC.LEAVE_CARD);
	    ctx.ReleaseContext();
	}catch(Exception e){
	    System.out.println("CardControl-Test failed: " + e.getClass().getName() + ", " + e.getMessage());
	    e.printStackTrace(System.out);
	    return;
	}
    }




    /**
     * Block infinite on first reader until card is available.
     */
    private static void waitforcard(){
	try{
	    System.out.println("EstablishContext(): ...");
	    Context ctx = new Context();
	    ctx.EstablishContext(PCSC.SCOPE_SYSTEM, null, null);

	    
	    System.out.println("Wait for card to be inserted in any reader ...");
	    State state = null;
	    do{
		// blocks until a reader is available
		ctx.GetStatusChange(PCSC.INFINITE, null);

		// block until card is inserted
		state = ctx.WaitForCard(PCSC.INFINITE);
	    }while(state == null);
	    System.out.println("Card inserted into " + state.szReader);
	    System.out.println("\n");
	    

	    System.out.println("Wait for card in a certain reader ...");
	    System.out.println("Pick reader ...");
	    String rn = Util.stdinPickReader(ctx);
	    System.out.println("Insert card ...");
	    
	    state = null;
	    do{
		// block until card is inserted
		state = ctx.WaitForCard(rn, PCSC.INFINITE);
	    }while(state == null);
	    System.out.println("Card inserted into " + state.szReader);
	    

	    System.out.println("Connect to card " + state.szReader);
	    Card card = ctx.Connect(state.szReader, PCSC.SHARE_EXCLUSIVE, PCSC.PROTOCOL_T0|PCSC.PROTOCOL_T1);
	    
	    System.out.println("Release contexts ...");
	    card.Disconnect(PCSC.LEAVE_CARD);
	    ctx.ReleaseContext();
	}catch(Exception e){
	    System.out.println("CardControl-Test failed: " + e.getClass().getName() + ", " + e.getMessage());
	    e.printStackTrace(System.out);
	    return;
	}
    }



    /**
     * Check that GetStatusChange() returns as soon as a reader is available when
     * NULL is passed in for the State array.
     */
    private static void getstatuschangenulltest(){
	System.out.println("EstablishContext(): ...");
	Context ctx = new Context();
	ctx.EstablishContext(PCSC.SCOPE_SYSTEM, null, null);

	State[] rsa = null;
	ctx.GetStatusChange(1000, null);
	
	System.out.println("GetStatusChange(null) returned, at least one  reader is available.");
    }

    /**
     * Either wait only for the first reader to have a card inserted or successively for 
     * all registered PCSC readers to have a card inserted, open a connection to this card,
     * and try to select the CardDomain.
     */
    private static void readertest(int mode){
	System.out.println("EstablishContext(): ...");
	Context ctx = new Context();
	ctx.EstablishContext(PCSC.SCOPE_SYSTEM, null, null);

	// list readers
	System.out.println("ListReaders(): ...");
	String[] sa = ctx.ListReaders();
	if (sa.length == 0){
	    throw new RuntimeException("no reader found");
	}
	for (int i = 0; i < sa.length; i++){
	    System.out.println("Reader: " + sa[i]);
	}

	int rdrCnt = (mode == ALLREADER_TEST) ? sa.length : 1;
	for (int i = 0; i < rdrCnt; i++){
	    // get status change 
	    System.out.println("GetStatusChange() for reader " + sa[i] + ": ...");
	    State[] rsa = new State[1];
	    rsa[0] = new State(sa[i]);
	    do{
		ctx.GetStatusChange(1000, rsa);
	    }while((rsa[0].dwEventState & PCSC.STATE_PRESENT) != PCSC.STATE_PRESENT);
	    System.out.println("ReaderState of " + sa[i] + ": ");
	    System.out.println(rsa[0]);
	    
	    // connect to card
	    System.out.println("Connect(): ...");
	    Card c = ctx.Connect(sa[i], PCSC.SHARE_EXCLUSIVE, PCSC.PROTOCOL_T0|PCSC.PROTOCOL_T1);
	    
	    // card status
	    System.out.println("CardStatus: ...");
	    State rs = c.Status();
	    System.out.println("CardStatus: ");
	    System.out.println(rs.toString());
	    
	    // select APDU for CardDomain
	    byte[] ba = { 
		(byte)0x00, (byte) 0xA4, (byte) 0x04, (byte) 0x00,  // select
		(byte) 0x07, // length
		(byte) 0xA0, (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x03, (byte) 0x00, (byte) 0x00, (byte) 0x00, // AID 
	    };
	    
	    // select card domain, different Transmit() methods used
	    try{
		System.out.println("First transmit: try to select CardDomain ..."); 
		byte[] ba2 = c.Transmit(ba, 0, ba.length);
		print(ba2);
	    }catch(PCSCException ex){
		System.out.println("REASON CODE: " + ex.getReason());
		System.out.println("TRANSMIT ERROR: " + ex.toString());
	    }

	    {	    
		// manipulate the CardDomain aid, provoke a response different from 0x9000
		ba[5] = (byte) 0xA1;
		byte[] ba2 = new byte[256];
		System.out.println("Second transmit: try again to select CardDomain ..."); 
		int ret = c.Transmit(ba, 0, ba.length, ba2, 0);
		if (ret < 0){
		    System.out.println("Transmit2 failed: pcsc code " + Integer.toHexString(ret));
		}else{
		    print(ba2, 0, ret);
		}
	    }

	    // reconnect
	    System.out.println("Reconnect(): ...");
	    c.Reconnect(PCSC.SHARE_EXCLUSIVE, PCSC.PROTOCOL_T0|PCSC.PROTOCOL_T1, PCSC.LEAVE_CARD);
	    
	    // another time card status
	    System.out.println("CardStatus(): ...");
	    rs = c.Status();
	    System.out.println("CardStatus(): ");
	    System.out.println(rs.toString());
	    
	    // select card domain another time
	    try{
		byte[] ba3 = { (byte) 0xA0, (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x03,
			       (byte) 0x00, (byte) 0x00, };
		System.out.println("Third transmit: try again to select CardDomain ..."); 
		ba = c.Transmit(0x00, 0xA4, 0x04, 0x00, ba3, 20);
		print(ba);
	    }catch(PCSCException ex){
		System.out.println("REASON CODE: " + ex.getReason());
		System.out.println("TRANSMIT ERROR: " + ex.toString());
	    }
	    
	    
	    // disconnect card connection
	    System.out.println("Disconnect from card ...");
	    c.Disconnect(PCSC.LEAVE_CARD);
	}
	
	// release context
	System.out.println("Release context ...");
	ctx.ReleaseContext();
    }




    /**
     * Loop of ListReaders() call.
     */
    private static void listreaderstest(){
	System.out.println("EstablishContext(): ...");
	Context ctx = new Context();
	ctx.EstablishContext(PCSC.SCOPE_SYSTEM, null, null);

	System.out.println("Loop ...");
	for (int i = 0; i < 50; i++){
	    String[] sa = ctx.ListReaders();
	    if (sa.length == 0){
		throw new RuntimeException("no reader found");
	    }
	    for (int j = 0; j < sa.length; j++){
		System.out.println("Reader: " + sa[j]);
	    }
	    State[] rsa = new State[sa.length];
	    for (int j = 0; j < rsa.length; j++){
		rsa[j] = new State(sa[j]);
	    }
	    boolean exitLoop = false;
	    int rdrIdx = 0;
	    while(!exitLoop){
		ctx.GetStatusChange(1000, rsa);
		for (int j = 0; j < rsa.length; j++){
		    if ((rsa[j].dwEventState & PCSC.STATE_PRESENT) != 0){
			rdrIdx = i;
			exitLoop = true;
			break;
		    }
		}
	    }
	}
	
	System.out.println("Release context ...");
	ctx.ReleaseContext();
    }

    /**
     * Wait until any of the registered PCSC readers has a card inserted, then
     * open a connection to this card, and try to select the CardDomain.
     */
    private static void anytest(){
	System.out.println("EstablishContext(): ...");
	Context ctx = new Context();
	ctx.EstablishContext(PCSC.SCOPE_SYSTEM, null, null);

	// list readers
	System.out.println("ListReaders(): ...");
	String[] sa = ctx.ListReaders();
	if (sa.length == 0){
	    throw new RuntimeException("no reader found");
	}
	for (int i = 0; i < sa.length; i++){
	    System.out.println("Reader: " + sa[i]);
	}

	// get status change 
	System.out.println("GetStatusChange() on all readers ...");
	State[] rsa = new State[sa.length];
	for (int i = 0; i < rsa.length; i++){
	    rsa[i] = new State(sa[i]);
	}
	boolean exitLoop = false;
	int rdrIdx = 0;
	while(!exitLoop){
	    ctx.GetStatusChange(1000, rsa);
	    System.out.println("All current reader states: ");
	    for (int i = 0; i < rsa.length; i++){
		System.out.println("Reader " + i + " " + sa[i] + ":");
		System.out.println(rsa[i]);
	    }
	    // break if one of them has a card
	    for (int i = 0; i < rsa.length; i++){
		if ((rsa[i].dwEventState & PCSC.STATE_PRESENT) != 0){
		    rdrIdx = i;
		    exitLoop = true;
		    break;
		}
	    }
	}
	System.out.println("Selected Reader: " + sa[rdrIdx]);

	// connect to card
	System.out.println("Connect(): ...");
	Card c = ctx.Connect(sa[rdrIdx], PCSC.SHARE_EXCLUSIVE, PCSC.PROTOCOL_T0|PCSC.PROTOCOL_T1);
	    
	// card status
	System.out.println("CardStatus: ...");
	State rs = c.Status();
	System.out.println("CardStatus: ");
	System.out.println(rs.toString());
	    
	// select APDU for CardDomain
	byte[] ba = { 
	    (byte)0x00, (byte) 0xA4, (byte) 0x04, (byte) 0x00,  // select
	    (byte) 0x07, // length
	    (byte) 0xA0, (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x03, (byte) 0x00, (byte) 0x00, (byte) 0x00, // AID 
	};
	    
	// select card domain
	try{
	    System.out.println("Transmit(): try to select CardDomain ..."); 
	    byte[] ba2 = c.Transmit(ba, 0, ba.length);
	    print(ba2);
	}catch(PCSCException ex){
	    System.out.println("REASON CODE: " + ex.getReason());
	    System.out.println("TRANSMIT ERROR: " + ex.toString());
	}

	// reconnect
	System.out.println("Reconnect(): ...");
	c.Reconnect(PCSC.SHARE_EXCLUSIVE, PCSC.PROTOCOL_T0|PCSC.PROTOCOL_T1, PCSC.LEAVE_CARD);
	    
	// another time card status
	System.out.println("CardStatus(): ...");
	rs = c.Status();
	System.out.println("CardStatus(): ");
	System.out.println(rs.toString());
	    
	// select card domain another time
	try{
	    byte[] ba3 = { (byte) 0xA0, (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x03,
			   (byte) 0x00, (byte) 0x00, };
	    System.out.println("Transmit(): try again to select CardDomain ..."); 
	    ba = c.Transmit(0x00, 0xA4, 0x04, 0x00, ba3, 20);
	    print(ba);
	}catch(PCSCException ex){
	    System.out.println("REASON CODE: " + ex.getReason());
	    System.out.println("TRANSMIT ERROR: " + ex.toString());
	}
	
	
	// disconnect card connection
	System.out.println("Disconnect from card ...");
	c.Disconnect(PCSC.LEAVE_CARD);
	
	// release context
	System.out.println("Release context ...");
	ctx.ReleaseContext();
    }


    /**
     * Loop for any status change on the first registered PCSC reader. You have to 
     * kill this process explicitly (Ctrl+C).
     */
    private static void statuschangeloop(){
	// establish context
	System.out.println("EstablishContext(): ...");
	Context ctx = new Context();
	ctx.EstablishContext(PCSC.SCOPE_SYSTEM, null, null);
	
	// list readers
	System.out.println("ListReaders(): ...");
	String[] sa = ctx.ListReaders();
	if (sa.length == 0){
	    throw new RuntimeException("no reader found");
	}
	for (int i = 0; i < sa.length; i++){
	    System.out.println("Reader: " + sa[i]);
	}
	
	// get status change test endless loop
	System.out.println("GetStatusChange(): endless loop, break with Ctrl+C...");
	State[] rsa = new State[1];
	rsa[0] = new State(sa[0]);	   
	do{
	    ctx.GetStatusChange(1000, rsa);
	    System.out.println("ReaderState of " + sa[0] + ": ");
	    System.out.println(rsa[0]);
	    try{
		Thread.currentThread().sleep(500);
	    }catch(Exception e){}
	}while(true);

	// unreached
    }

    /**
     * List all groups and all readers in each group.
     */
    private static void grouptest(){
	// establish context
	System.out.println("EstablishContext(): ...");
	Context ctx = new Context();
	ctx.EstablishContext(PCSC.SCOPE_SYSTEM, null, null);

	// list groups
	System.out.println("ListReaderGroups(): ...");
	String[] groups = ctx.ListReaderGroups();
	if (groups.length == 0){
	    System.out.println("no groups found");
	    return;
	}
	for (int i = 0; i < groups.length; i++){
	    System.out.println("Group: " + groups[i]);
	}
	for (int i = 0; i < groups.length; i++){
	    System.out.println("Group: " + groups[i]);
	    // list readers
	    System.out.println("ListReaders(): for each group ...");
	    String[] sa = ctx.ListReaders();
	    if (sa.length == 0){
		System.out.println("no readers in group " + groups[i]);
	    }else{
		for (int j = 0; j < sa.length; j++){
		    System.out.println("Reader: " + sa[j]);
		}
	    }
	}
	// list readers again
	System.out.println("ListReaders(): for all groups ...");
	String[] sa = ctx.ListReaders(groups);
	if (sa.length == 0){
	    System.out.println("no reader in any group");
	}else{
	    for (int j = 0; j < sa.length; j++){
		System.out.println("Reader: " + sa[j]);
	    }
	}
    }


    /**
     * Establish context, list readers, connect to frst one, open card connection,
     * and select CardDomain, but MAX_PASS_CNT times.
     */
    public static int MAX_PASS_CNT = 100;
    private static void selectstress(){
	System.out.println("Select-Stress-Test: ...");
	int pass = 0;
	try{
	    while(pass < MAX_PASS_CNT){
		pass++;
		System.out.println("Pass: " + pass);
		
		Context ctx = new Context();
		ctx.EstablishContext(PCSC.SCOPE_SYSTEM, null, null);
	
		String[] sa = ctx.ListReaders();
		if (sa.length == 0){
		    throw new RuntimeException("no reader found");
		}
		System.out.println("Connect to reader: " + sa[0]);
		
		State[] rsa = new State[1];
		rsa[0] = new State(sa[0]);
		do{
		    ctx.GetStatusChange(1000, rsa);
		}while((rsa[0].dwEventState & PCSC.STATE_PRESENT) != PCSC.STATE_PRESENT);
		
		Card card = ctx.Connect(sa[0], PCSC.SHARE_EXCLUSIVE, PCSC.PROTOCOL_T0|PCSC.PROTOCOL_T1);
		State rs = card.Status();
		
		System.out.println("Selecting CardDomain ...");
		byte[] aid = { (byte) 0xA0, (byte) 0x00, (byte) 0x00, (byte) 0x00, (byte) 0x03,
			       (byte) 0x00, (byte) 0x00, };
		byte[] ret = card.Transmit(0x00, 0xA4, 0x04, 0x00, aid, 20);
		
		card.Disconnect(PCSC.LEAVE_CARD);

		ctx.ReleaseContext();
	    }
	}catch(Exception e){
	    System.out.println("Select-Stress-Test: failed in pass " + pass);
	    System.out.println("Select-Stress-Test: exception-type " + e.getClass().getName());
	    System.out.println("Select-Stress-Test: exception-msg " + e.getMessage());
	    e.printStackTrace(System.out);
	    return;
	}
	System.out.println("Stress-Test: passed successfully !");
    }

    private static String cardDomainAIDString = "A0000000030000";
    private static String selectCardDomainString = "00A4040007A0000000030000";
    private static String getCplcString = "80CA9F7F00";

    private static void apdutest(){
	System.out.println("APDU-Test: ...");

	System.out.println("EstablishContext(): ...");
	Context ctx = new Context();
	ctx.EstablishContext(PCSC.SCOPE_SYSTEM, null, null);

	// list readers
	System.out.println("ListReaders(): ...");
	String[] sa = ctx.ListReaders();
	if (sa.length == 0){
	    System.out.println("no reader found");
	    System.exit(0);
	}
	for (int i = 0; i < sa.length; i++){
	    System.out.println("Reader: " + sa[i]);
	}

	int i = 0;
	// get status change 
	System.out.println("GetStatusChange() for reader " + sa[i] + ": ...");
	State[] rsa = new State[1];
	rsa[0] = new State(sa[i]);
	do{
	    ctx.GetStatusChange(1000, rsa);
	}while((rsa[0].dwEventState & PCSC.STATE_PRESENT) != PCSC.STATE_PRESENT);
	System.out.println("ReaderState of " + sa[i] + ": ");
	System.out.println(rsa[0]);
	    
	// connect to card
	System.out.println("Connect(): ...");
	Card c = ctx.Connect(sa[i], PCSC.SHARE_EXCLUSIVE, PCSC.PROTOCOL_T0|PCSC.PROTOCOL_T1);
	    
	// card status
	System.out.println("CardStatus: ...");
	State rs = c.Status();
	System.out.println("CardStatus: ");
	System.out.println(rs.toString());
	
	Apdu apdu = new Apdu(256);
	// select card domain another time
	try{
	    byte[] ba;

	    apdu.set(selectCardDomainString);
	    System.out.println("apdu1: " + apdu);
	    ba = c.Transmit(apdu);
	    print(ba);

	    apdu.set(0x0, 0xA4, 0x4, 0x0);
	    apdu.addString(cardDomainAIDString);
	    System.out.println("apdu2: " + apdu);
	    ba = c.Transmit(apdu);
	    print(ba);
	    
	}catch(PCSCException ex){
	    System.out.println("REASON CODE: " + ex.getReason());
	    System.out.println("TRANSMIT ERROR: " + ex.toString());
	}
	    
	
	// disconnect card connection
	System.out.println("Disconnect from card ...");
	c.Disconnect(PCSC.LEAVE_CARD);
	
	// release context
	System.out.println("Release context ...");
	ctx.ReleaseContext();
    }



    static void print(byte[] response){
	print(response, 0, response.length);
    }

    static void print(byte[] response, int off, int length){
	System.out.println("response: " + Apdu.ba2s(response, off, length));
    }
}




