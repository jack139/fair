
function first()
{
	if (!ableToPrint)
		document.getElementById("qz-status").style.background = "#FFFFFF";
}

function initPrinter()
{
	findPrinter("lion");
}


function doPrint(name)
{
	if (ableToPrint) print_receipt(name);
	else alertify.warning("未找到打印机，不能打印！");
}

function print_receipt(name)
{
	if (notReady()) { return; }

	var date=(new Date()).toLocaleString();

	qz.append("U掌柜 <班组当日统计> urfresh.cn\n\n");
	qz.append("登录用户："+name+"\n");
	qz.append("--------------------------------\n");
	qz.append($("#id_count").html()+"\n");
	qz.append($("#id_total").html()+"\n");
	qz.append($("#id_count2").html()+"\n");
	qz.append($("#id_total2").html()+"\n");
	qz.append("--------------------------------\n");
	qz.append($("#id_total3").html()+"\n");
	qz.append("********************************\n");
	qz.append("打印时间："+date+"\n\n\n\n\n\n");

	qz.print();
	console.log('print done.');
}
