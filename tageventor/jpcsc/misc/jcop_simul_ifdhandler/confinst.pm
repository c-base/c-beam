#!/usr/bin/perl

die unless (@ARGV == 4);

$friendlyName = shift @ARGV;
$devName = shift @ARGV;
$libPath = shift @ARGV;
$chId = shift @ARGV;

print "install $friendlyName $devName $libPath $chId";


while (<STDIN>) {
    if (/^(\s)*FRIENDLYNAME(\s)+\"$friendlyName\"/){
	$mode = "replace";
    }
    
    if (defined $mode){
	s/^(\s)*DEVICENAME(\s)+(\w+)/DEVICENAME $devName/;
	s/^(\s)*LIBPATH(\s)+(\w+)/LIBPATH $libPath/;
	s/^(\s)*CHANNELID(\s)+(\w+)/CHANNELID $chId/;
    }
    print $_;
}

if (!defined $mode){
    print "\n";
    print "FRIENDLYNAME $friendlyName";
    print "DEVICENAME $devName";
    print "LIBPATH $libPath";
    print "CHANNELID $chId";
}
