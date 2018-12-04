var ableToPrint = false;
var printerName = "zebra";

function deployQZApplet() {
    console.log('Starting deploy of qz applet');

    var versions = deployJava.getJREs();
    if(versions == null || versions.length == 0) {
    	ableToPrint = false;
    	console.log('No JRE!');
    	//alert('检测到您的计算机没有安装JRE软件，不能使用打印功能！')
    	alertify.warning("您的计算机没有安装JRE软件，不能使用打印功能。");
    	return false;
    }

    var attributes = {id: "qz", code:'qz.PrintApplet.class',
	archive:'/static/qz-print/qz-print.jar', width:1, height:1};
    var parameters = {jnlp_href: '/static/qz-print/qz-print_jnlp.jnlp',
	cache_option:'plugin', disable_logging:'false',
	initial_focus:'false', separate_jvm:'true'};
    if (deployJava.versionCheck("1.7+") == true) {}
    else if (deployJava.versionCheck("1.6.0_45+") == true) {}
    else if (deployJava.versionCheck("1.6+") == true) {
	delete parameters['jnlp_href'];
    }
    deployJava.runApplet(attributes, parameters, '1.6');

    return true;
}

/**
 * Automatically gets called when applet has loaded.
 */
function qzReady() {
    // If the qz object hasn't been created, fallback on the <applet> tags
    if (!qz) {
	window["qz"] = document.getElementById('qz');
    }
    //var title = document.getElementById("title");
    if (qz) {
	try {
	    //title.innerHTML = title.innerHTML + " " + qz.getVersion();
	    document.getElementById("qz-status").style.background = "#FFFFFF";
	    //if (typeof("initPrinter")=="function"){
	    	console.log('call initPrinter()');
	    	initPrinter();
	    //}
	} catch(err) { // LiveConnect error, display a detailed message
	    document.getElementById("qz-status").style.background = "#F5A9A9";
	    alert("ERROR:  \nThe applet did not load correctly.  Communication to the " +
		    "applet has failed, likely caused by Java Security Settings.  \n\n" +
		    "CAUSE:  \nJava 7 update 25 and higher block LiveConnect calls " +
		    "once Oracle has marked that version as outdated, which " +
		    "is likely the cause.  \n\nSOLUTION:  \n  1. Update Java to the latest " +
		    "Java version \n          (or)\n  2. Lower the security " +
		    "settings from the Java Control Panel.");
	}
    }
}

/**
 * Returns whether or not the applet is not ready to print.
 * Displays an alert if not ready.
 */
function notReady() {
    // If applet is not loaded, display an error
    if (!isLoaded()) {
	return true;
    }
    // If a printer hasn't been selected, display a message.
    else if (!qz.getPrinter()) {
	alert('Please select a printer first by using the "Detect Printer" button.');
	return true;
    }
    return false;
}

/**
 * Returns is the applet is not loaded properly
 */
function isLoaded() {
    if (!qz) {
	alert('Error:\n\n\tPrint plugin is NOT loaded!');
	return false;
    } else {
	try {
	    if (!qz.isActive()) {
		alert('Error:\n\n\tPrint plugin is loaded but NOT active!');
		return false;
	    }
	} catch (err) {
	    alert('Error:\n\n\tPrint plugin is NOT loaded properly!');
	    return false;
	}
    }
    return true;
}

/**
 * Automatically gets called when "qz.print()" is finished.
 */
function qzDonePrinting() {
    // Alert error, if any
    if (qz.getException()) {
	alert('打印出错:\n\n\t' + qz.getException().getLocalizedMessage());
	qz.clearException();
	return;
    }

    // Alert success message
    alertify.warning('成功打印到 ' + qz.getPrinter() + ' 打印机队列.');
}



/***************************************************************************
 * Prototype function for finding the closest match to a printer name.
 * Usage:
 *    qz.findPrinter('zebra');
 *    window['qzDoneFinding'] = function() { alert(qz.getPrinter()); };
 ***************************************************************************/
function findPrinter(name) {
    if (name) {
	   printerName = name;
    }

    if (isLoaded()) {
	// Searches for locally installed printer with specified name
	qz.findPrinter(printerName);

	// Automatically gets called when "qz.findPrinter()" is finished.
	window['qzDoneFinding'] = function() {
	    var printer = qz.getPrinter();

	    // Alert the printer name to user
	    alertify.warning(printer !== null ? '打印机 '+printer+' OK!':'!!!未找到打印机 '+printerName);

	    // Remove reference to this function
	    window['qzDoneFinding'] = null;
	};
    }
}


/***************************************************************************
 * Prototype function for printing a text or binary file containing raw
 * print commands.
 * Usage:
 *    qz.appendFile('/path/to/file.txt');
 *    window['qzDoneAppending'] = function() { qz.print(); };
 ***************************************************************************/
function printFile(file) {
    if (notReady()) { return; }

    // Append raw or binary text file containing raw print commands
    qz.appendFile(getPath() + "qz-print/" + file);

    // Automatically gets called when "qz.appendFile()" is finished.
    window['qzDoneAppending'] = function() {
	// Tell the applet to print.
	qz.print();

	// Remove reference to this function
	window['qzDoneAppending'] = null;
    };
}


function printCommand() {
    if (notReady()) { return; }

    // Append raw or binary text file containing raw print commands
    //qz.appendFile(getPath() + "assets/" + file);

    qz.appendHex("x1bx20x2");
    //qz.append("this is a test\n");
    console.log('append text');

    // Tell the applet to print.
    qz.print();
    console.log('print done.');
}


/***************************************************************************
 ****************************************************************************
 * *                          HELPER FUNCTIONS                             **
 ****************************************************************************
 ***************************************************************************/


/***************************************************************************
 * Gets the current url's path, such as http://site.com/example/dist/
 ***************************************************************************/
function getPath() {
    var path = window.location.href;
    return path.substring(0, path.lastIndexOf("/")) + "/";
}

/**
 * Equivalent of VisualBasic CHR() function
 */
function chr(i) {
    return String.fromCharCode(i);
}
