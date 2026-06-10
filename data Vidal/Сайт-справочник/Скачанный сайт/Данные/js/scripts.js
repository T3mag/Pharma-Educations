function change(code) {
   eval("img_p = i_" + code + ".src");
   ll = img_p.length;
   img_p = img_p.slice(ll-6,ll);
   if (img_p == "cl.gif") {
      disp = "block";
      img_new = "../images/op.gif";
   }
   else {
      disp = "none";
      img_new = "../images/cl.gif";
   }
   eval("i_" + code + ".src=\"" + img_new + "\"");
   eval("l_" + code + ".style.display = '" + disp +"'");
return;
}
var newWindow;
function photo(fname)
{
	if (!newWindow || newWindow.closed) {
		newWindow = window.open("","sub","status,height=598,width=400");
		var newContent = "<html><head><title>VIDAL®. Справочник Видаль. Лекарственные препараты в России</title></head><body bgcolor=#d5e8f9 style=padding:0;margin:0><table height=598 border=0 cellpadding=0 cellspacing=0><tr valign=middle><td><img src='";
		newContent += fname;
		newContent += "'></td></tr></table></body></html>";
		newWindow.document.write(newContent);
		newWindow.document.close( ); // close layout stream
	} else if (newWindow.focus) {
		newWindow.focus( );
		var newContent = "<table height=598 border=0 cellpadding=0 cellspacing=0><tr valign=middle><td><img src='"+fname+"'></td></tr></table>";
		newWindow.document.body.innerHTML = newContent;
	}
}

function showtip(did)
{
	if (document.getElementById(did).style.display=='none') {
		document.getElementById(did).style.display='block';
	} else { document.getElementById(did).style.display='none'; }
}
var printWindow;
function iprint(info)
{
	var re = new RegExp("<A href=\"javascript:iprint(.*?)</a>","gi");
	info = info.replace(re, "");
	var re = new RegExp("</a>","gi");
	info = info.replace(re, "");
	var re = new RegExp("<A href(.*?)>","gi");
	info = info.replace(re, "");
	var re = new RegExp(' style="display: none"',"gi");
	info = info.replace(re, "");;
	var re = /<img(.*?)photo\('(._2A@)'\)(.*?)>/i;
	imgsrc = info.match(re);
//	if (imgsrc) photo(imgsrc[2]);
	var re = /<img(.*?)photo\('(._2A@)'\)(.*?)>/gi;
	info = info.replace(re, "");
	var re = new RegExp("<tr id=buttons>(.*?)\n(.*?)\n(.*?)</tr>","gi");
	info = info.replace(re, "");
	
	if (!printWindow || printWindow.closed) {
		printWindow = window.open("","info","status,resizable,scrollbars,titlebar=no,height=598,width=500,left=0");
		var newContent = "<html><head><title>VIDAL®. Справочник Видаль. Лекарственные препараты в России</title><link href=style.css rel=stylesheet type=text/css></head><body>";
		newContent += "<center><b><a href=javascript:print()>ОТПРАВИТЬ НА ПЕЧАТЬ</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href=javascript:close()>ЗАКРЫТЬ ОПИСАНИЕ</a><br><br>";
		newContent += info;
		newContent += "<center><b><a href=javascript:print()>ОТПРАВИТЬ НА ПЕЧАТЬ</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href=javascript:close()>ЗАКРЫТЬ ОПИСАНИЕ</a></body></html>";
		printWindow.document.write(newContent);
		printWindow.document.close( ); 
	} else if (printWindow.focus) {
		printWindow.focus( );
		var newContent = info;
		printWindow.document.body.innerHTML = newContent;
	}
}
