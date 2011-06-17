package samples;

import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import javax.swing.event.*;
import javax.swing.border.*;
import javax.swing.text.*;

import com.linuxnet.jpcsc.*;

public class APDUTool extends JFrame{
    private static int ALL_PROTOS = PCSC.PROTOCOL_T0|PCSC.PROTOCOL_T1;

    private static Apdu.Format format = new Apdu.Format(Apdu.HEX_COLON_HEX_FORMAT, true, false);
    private static String defaultAID = StringValues.APPLET;   
    private static String defaultAPDU = StringValues.APDU_TEXT;

    public static void main(String[] args){
	final APDUTool t = new APDUTool();
	t.addWindowListener(new WindowAdapter() {
            public void windowClosing(WindowEvent e) {
                System.exit(0);
            }
        });
	t.pack();
	t.show();
    }

    private static String[] labelsText = {
	StringValues.READER,
	StringValues.APPLET_AID,
	StringValues.APDU,
    };

    private static String[] buttonsText = {
	StringValues.CONNECT,
	StringValues.SELECT,
	StringValues.SEND,
    };

    private Context ctx;
    private Card card;
    private String[] readerNames;
    private JComboBox readerBox;
    private JButton readerConnector;
    private NumberField appletField;
    private JButton appletConnector;
    private NumberField apduField;
    private JButton apduSender;
    private JTextArea textArea;

    private APDUTool(){
	JPanel rootp = new JPanel();
	rootp.setLayout(new BorderLayout());
	super.getContentPane().add(rootp);
	
	ctx = new Context();
	try{
	    ctx.EstablishContext(PCSC.SCOPE_SYSTEM, null, null);
	    readerNames = ctx.ListReaders();
	}catch(Exception e){
            JOptionPane.showMessageDialog(this, StringValues.CANNOT_CONNECT_TO_PCSC_SERVICE, StringValues.ERROR, JOptionPane.ERROR_MESSAGE);	    
	    System.exit(0);
	}
	
	if (readerNames.length == 0){
	    JOptionPane.showMessageDialog(this, StringValues.NO_READERS_AVAILABLE, StringValues.ERROR, JOptionPane.ERROR_MESSAGE);	    
	    System.exit(0);
	}

	{
	    JPanel inputp = new JPanel();
	    inputp.setLayout(new BoxLayout(inputp, BoxLayout.Y_AXIS));
	    rootp.add(inputp, BorderLayout.NORTH);
	    {
		// the reader panel
		JPanel p = new JPanel();
		p.setLayout(new BoxLayout(p, BoxLayout.X_AXIS));
		p.setBorder(BorderFactory.createTitledBorder(StringValues.READER_SELECTOR));
		inputp.add(p);
		JLabel l = new JLabel(labelsText[0]);
		p.add(l);
		readerBox = new JComboBox(readerNames);
		p.add(readerBox);
		readerConnector = new JButton(buttonsText[0]);
		p.add(readerConnector);
	    }
	    {
		// the aid panel
		JPanel p = new JPanel();
		p.setLayout(new BoxLayout(p, BoxLayout.X_AXIS));
		p.setBorder(BorderFactory.createTitledBorder(StringValues.APPLET_SELECTOR));
		inputp.add(p);
		JLabel l = new JLabel(labelsText[1]);
		p.add(l);
		appletField = new NumberField(defaultAID, 20, 32, 16);
		p.add(appletField);
		appletConnector = new JButton(buttonsText[1]);
		p.add(appletConnector);
	    }
	    {
		// the apdu panel
		JPanel p = new JPanel();
		p.setLayout(new BoxLayout(p, BoxLayout.X_AXIS));
		p.setBorder(BorderFactory.createTitledBorder(StringValues.APDU_SENDER));
		inputp.add(p);
		JLabel l = new JLabel(labelsText[2]);
		p.add(l);
		apduField = new NumberField(defaultAPDU, 20, 256, 16);
		p.add(apduField);
		apduSender = new JButton(buttonsText[2]);
		p.add(apduSender);
	    }
	}

	{
	    // the messages panel
	    JPanel p = new JPanel();
	    p.setLayout(new BoxLayout(p, BoxLayout.X_AXIS));
	    p.setBorder(BorderFactory.createTitledBorder(StringValues.OUTPUT));
	    rootp.add(p, BorderLayout.CENTER);
	    textArea = new JTextArea(20, 80);
	    JScrollPane sp = new JScrollPane(textArea);
	    p.add(sp);
	}

	{
	    // the exit panel
	    JPanel p = new JPanel();
	    p.setLayout(new BoxLayout(p, BoxLayout.X_AXIS));
	    p.setBorder(BorderFactory.createEmptyBorder(5, 0, 5, 0));
	    rootp.add(p, BorderLayout.SOUTH);
	    JButton b = new JButton(StringValues.QUIT);
	    p.add(b);
	    b.addActionListener(new ActionListener() {
		public void actionPerformed(ActionEvent ev) {
		    System.exit(0);
		}
	    });
	}

	// reader connector: connect to reader and wait for card insertion
	readerConnector.addActionListener(new ActionListener() {
	    public void actionPerformed(ActionEvent ev) {
		if (card != null){
		    // try to disconnect any previous card connection
		    try{
			card.Disconnect(PCSC.LEAVE_CARD);	
		    }catch(Exception e){}
		}
		// check reader until card is inserted
		String reader = (String) readerBox.getSelectedItem();
		JOptionPane.showMessageDialog(APDUTool.this, StringValues.TRYING_TO_CONNECT_TO_READER + reader + StringValues.DO_NOT_FORGET_TO_INSERT_A_CARD,StringValues.CONNECTING, JOptionPane.INFORMATION_MESSAGE);
		State[] rsa = new State[1];
		rsa[0] = new State(reader);
		do{
		    try{
			ctx.GetStatusChange(1000, rsa);
		    }catch(Exception e){
                        errorMessage (textArea, StringValues.CONTEXT_GETSTATUSCHANGE_FAILED, e);
			return;
		    }
		}while((rsa[0].dwEventState & PCSC.STATE_PRESENT) != PCSC.STATE_PRESENT);
		textArea.append(StringValues.READERSTATE_OF + reader + ":\n");
		textArea.append(rsa[0].toString());
		try{
		    // connect to card
		    card = ctx.Connect(reader, PCSC.SHARE_EXCLUSIVE, ALL_PROTOS);
		}catch(Exception e){
                    
                    errorMessage (textArea,StringValues.CARD_CONNECT_FAILED, e);		    
		    return;
		}
	    }
	});

	// applet connector: try to select applet with given aid
	appletConnector.addActionListener(new ActionListener() {
	    public void actionPerformed(ActionEvent ev) {
		if (card == null){
	            JOptionPane.showMessageDialog(APDUTool.this, StringValues.NO_ACTIVE_READER_CONNECTION, StringValues.ERROR, JOptionPane.ERROR_MESSAGE);	    
		    return;
		}
		// construct select command
		Apdu apdu = new Apdu(256);
		try{
		    String s = appletField.getText();
		    if (s.length() == 0) throw new RuntimeException(StringValues.NO_AID_GIVEN);
		    if ((s.length() % 2) != 0) throw new RuntimeException(StringValues.ODD_LENGTH_OF + s);
		    apdu.set(0x0, 0xA4, 0x4, 0x0);
		    apdu.addString(s);
		}catch(Exception e){
	            JOptionPane.showMessageDialog(APDUTool.this, StringValues.INVALID_INPUT + e.getMessage(), StringValues.ERROR, JOptionPane.ERROR_MESSAGE);	    
		    return;
		}
		// send the select command
		textArea.append(StringValues.SELECTING_APPLET + apdu + "\n");
		textArea.append(StringValues.SENDING + apdu + "\n");
		try{
		    byte[] response = card.Transmit(apdu);
		    textArea.append(StringValues.RECEIVED + Apdu.ba2s(response, format) + "\n");
		}catch(PCSCException pe){
		    textArea.append(StringValues.CARD_TRANSMIT_FAILED);
		    textArea.append(StringValues.PCSC_ERROR_MESSAGE + pe.getMessage() + "\n");
		    return;
		}catch(Exception e){
                    
                    errorMessage (textArea,StringValues.CARD_TRANSMIT_FAILED, e);
		    return;
		}
	    }
	});

	// take edited apdu and send it to card
	apduSender.addActionListener(new ActionListener() {
	    public void actionPerformed(ActionEvent ev) {
		if (card == null){
	            JOptionPane.showMessageDialog(APDUTool.this, StringValues.NO_ACTIVE_READER_CONNECTION,StringValues.ERROR, JOptionPane.ERROR_MESSAGE);	    
		    return;
		}
		Apdu apdu = new Apdu(256);
		try{
		    String s = apduField.getText();
		    if (s.length() == 0) throw new RuntimeException(StringValues.NO_APDU_GIVEN);
		    if ((s.length() % 2) != 0) throw new RuntimeException(StringValues.ODD_LENGTH_OF + s);
		    apdu.set(s);
		}catch(Exception e){
	            JOptionPane.showMessageDialog(APDUTool.this, StringValues.INVALID_INPUT + e.getMessage(),StringValues.ERROR, JOptionPane.ERROR_MESSAGE);	    
		    return;
		}
		// send the apdu
		textArea.append(StringValues.SENDING + apdu + "\n");
		try{
		    byte[] response = card.Transmit(apdu);
		    textArea.append(StringValues.RECEIVED + Apdu.ba2s(response, format) + "\n");
		}catch(PCSCException pe){
		    textArea.append(StringValues.CARD_TRANSMIT + pe.getMessage() + "\n");
		    return;
		}catch(Exception e){
                    
                    errorMessage (textArea, StringValues.CARD_TRANSMIT_FAILED, e);
		    return;
		}
	    }
	});
    }
    
    private void errorMessage (JTextArea textArea, String message, Exception e)
    {
        textArea.append(message);
        textArea.append(StringValues.ERROR_CLASS + e.getClass() + "\n");
        textArea.append(StringValues.ERROR_MESSAGE + e.getMessage() + "\n");
    }
}


class NumberField extends JTextField{
    public NumberField(){
	super();
    }

    public NumberField(int cols, int maxCnt){
	super(cols);
	((NumberDocument) getDocument()).maxCnt = maxCnt;
    }

    public NumberField(String text, int cols, int maxCnt){
	super(text, cols);
	((NumberDocument) getDocument()).maxCnt = maxCnt;
    }
 
    public NumberField(int cols, int maxCnt, int radix){
	super(cols);
	((NumberDocument) getDocument()).maxCnt = maxCnt;
	((NumberDocument) getDocument()).radix = radix;
    }

    public NumberField(String text, int cols, int maxCnt, int radix){
	super(text, cols);
	((NumberDocument) getDocument()).maxCnt = maxCnt;
	((NumberDocument) getDocument()).radix = radix;
	setText(text);
    }
 
    protected Document createDefaultModel(){
	return new NumberDocument();
    }

    public final int getNumber(){
	String s = super.getText().trim();
	if (s.length() == 0)
	    return 0;
	try{
	    return Integer.parseInt(s, ((NumberDocument) getDocument()).radix);
	}catch(Exception e){
	    throw new RuntimeException(StringValues.INTERNAL_ERROR);
	}
    }

    public final String getText(){
	return super.getText().trim();
    }

    static class NumberDocument extends PlainDocument{
	int maxCnt;
	int radix;

	NumberDocument(){
	    this.maxCnt = -1;
	    this.radix = 10;
	}

	public void insertString(int offs, String str, AttributeSet a)  throws BadLocationException{
	    if (str == null){
		return;
	    }
	    for (int i = 0; i < str.length(); i++){
		if (Character.digit(str.charAt(i), radix) == -1){
		    Toolkit.getDefaultToolkit().beep();
		    return;
		}
	    }
	    if ((maxCnt != -1) && ((getLength() + str.length()) > maxCnt)){
		 Toolkit.getDefaultToolkit().beep();
		return;
	    }
	    super.insertString(offs, str, a);
	}
    }
}


/*
 * StringValues.java
 *
 * Created on 2 luglio 2004, 11.14
 */

/**
 *
 * @author  ue_sergi
 */
class StringValues {
    
    static final String  APDU_TEXT                         = "80CA9F7F00" ;                              
    static final String  APPLET                            = "A0000000030000";                           
    static final String  APDU_SENDER                       = "Apdu Sender "   ;                          
    static final String  APDU                              = "APDU:         ";                           
    static final String  APPLET_AID                        = "Applet AID:";                           
    static final String  APPLET_SELECTOR                   = "Applet Selector ";                         
    static final String  CANNOT_CONNECT_TO_PCSC_SERVICE    = "Cannot connect to PCSC service!";          
    static final String  CARD_CONNECT_FAILED               = "Card.Connect() failed!\n";
    static final String  CARD_TRANSMIT_FAILED              = "Card.Transmit() failed!\n";
    static final String  CARD_TRANSMIT                     = "Card.Transmit(): ";
    static final String  CONNECT                           = "Connect...";
    static final String  CONNECTING                        = "Connecting...";
    static final String  CONTEXT_GETSTATUSCHANGE_FAILED    = "Context.GetStatusChange() failed!\n";
    static final String  DO_NOT_FORGET_TO_INSERT_A_CARD    = "\nDo not forget to insert a card!";
    static final String  ERROR_CLASS                       = "Error class: ";
    static final String  ERROR_MESSAGE                     = "Error message: ";
    static final String  ERROR                             = "Error";
    static final String  INTERNAL_ERROR                    = "Internal error";
    static final String  INVALID_INPUT                     = "Invalid input: ";
    static final String  NO_ACTIVE_READER_CONNECTION       = "No active reader connection!";
    static final String  NO_AID_GIVEN                      = "No AID given";
    static final String  NO_APDU_GIVEN                     = "No APDU given";
    static final String  NO_READERS_AVAILABLE              = "No readers available!";
    static final String  ODD_LENGTH_OF                     = "Odd length of ";
    static final String  OUTPUT                            = "Output ";
    static final String  PCSC_ERROR_MESSAGE                = "PCSC Error Message: ";
    static final String  QUIT                              = "Quit";
    static final String  READER_SELECTOR                   = "Reader Selector ";
    static final String  READER                            = "Reader:      ";
    static final String  READERSTATE_OF                    = "ReaderState of ";
    static final String  RECEIVED                          = "Received ";
    static final String  SELECT                            = "Select... ";
    static final String  SELECTING_APPLET                  = "Selecting applet ";
    static final String  SEND                              = "Send...   ";
    static final String  SENDING                           = "Sending ";
    static final String  TRYING_TO_CONNECT_TO_READER       = "Trying to connect to reader ";
}
