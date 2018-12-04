var item_list=[];

function first()
{
	if (!ableToPrint)
		document.getElementById("qz-status").style.background = "#FFFFFF";
	initAll();
	$("#weight").focus();
}


function keyPress(id)
{
	if ($(id).val()=="") checkOut(); 
	else setTimeout(addItem, 200);
}

function initAll()
{
	$.each(item_list, function(i, item){
		$(item+"_tr").remove();		
	});
	item_list=[];
	$("#item_list").show();

	$("#product_id").prop('disabled', false);
	$("#product_id").val("");
	$("#product_id").focus();
}


function delItem(item)
{
	$(item+"_tr").remove();
	item_list.splice(item_list.indexOf(item),1);
	if (item_list.length==0)
		$("#item_list").show();
}

function showData(item)
{
	var rand_id = item["product_id"] + "_" + Math.floor(Math.random()*1000000);
	var shop_row = $("<tr id='"+rand_id+"_tr'>" + 
		"<td><div id='"+rand_id+"_id'>"+item["product_id"]+"</div></td>" +
		"<td id='"+item["product_id"]+"'>"+item["name"]+"</td>" +
		"<td>"+((item["product_id"][2]==1)?"整进整出":((item["product_id"][2]==2)?"散进散出":"散进整出"))+"</td>" +
		"<td><div id='"+rand_id+"_price'>"+item["price"]+"</td>" +
		"<td><div id='"+rand_id+"_unit'>"+item["unit_name"]+"</td>" +
		"<td><div id='"+rand_id+"_num'>"+item["weight"]+"</div></td>" +
		"<td><div id='"+rand_id+"_total'>"+item["weight_price"]+"</div></td>" +
		"<td><a class=\"abtn\" href='#' id='"+rand_id+"' " +
		"onclick=\"delItem('#"+rand_id+"');\">删除</a></td></tr>");
	$("#item_list").hide();
	$("#item_list").after(shop_row);
	
	item_list.push("#"+rand_id);

	$("#product_id").val("");
	$("#"+rand_id+"_num").focus();
}

function addItem()
{
	var product_id=$("#product_id").val();

	if ($("#"+product_id).length>0){
		alertify.warning("该商品已添加，不能重复添加！");
		$("#product_id").select();
		return false;
	}

	$.ajax({
		type: "POST",
		url: "/pos/pos_json",
		async: true,
		timeout: 15000,
		data: {product_id:product_id, weight:0},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status==200)
			{
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					showData(retJson["data"]);
				}
				else {
					alertify.error("查找商品失败："+retJson["msg"]);
					$("#product_id").focus();
				}
			}
			else
			{
				alertify.error("网络异常！("+xhr.status+")");
				$("#product_id").focus();
			}
			
			return false;
		}
	});
	
	return false;
}


function doPrint()
{
	if (!ableToPrint){
		alertify.warning("未找到打印机，不能打印！");
		return false;
	}

	var btn_list=$("a.abtn");

	if (btn_list.size()==0){
		alertify.warning("请添加商品！");
		return false;
	}

	var fail=false;
	$.each(btn_list, function(i, item){
		var rand_id = item.id;
		var product_id = $("#"+rand_id+"_id").html();
		var name = $("#"+product_id).html();
		var unit = $("#"+rand_id+"_unit").html();
		var price = $("#"+rand_id+"_price").html();
		var num = $("#"+rand_id+"_num").html();
		var total = $("#"+rand_id+"_total").html();

		print_label(product_id, name, unit, price, num, total);
	});

	return false;
}


/* 打印标签 */
function print_label(product_id, name, unit, price, num, total)
{
	if (notReady()) { return; }

	var date=(new Date()).toLocaleString();

	qz.append("SIZE 50 mm,40 mm\n" +
		"GAP 3 mm,0 mm\n" +
		"REFERENCE 0,0\n" +
		"SPEED 4.0\n" +
		"DENSITY 8\n" +
		"SET PEEL OFF\n" +
		"SET CUTTER OFF\n" +
		"SET PARTIAL_CUTTER OFF\n" +
		"SET TEAR ON\n" +
		"DIRECTION 0\n" +
		"SHIFT 0\n" +
		"OFFSET 0 mm\n" +
		"CLS\n");
	qz.append("TEXT 25,30,\"TSS24.BF2\",0,1,1,\"U掌柜 <舌尖甜到心间> urfresh.cn\"\n");
	//qz.append("TEXT 25,30,\"TSS24.BF2\",0,1,1,\""+date+"\"\n");
	//qz.append("BARCODE 30,70,\"128M\",80,0,0,4,12,\"!104" + 
	//	product_id[0]+"!099"+product_id.substring(1)+"\"\n");
	qz.append("BARCODE 10,70,\"128\",80,0,0,3,7,\""+product_id+"\"\n");
	//"PRINT LEN000,1"
	qz.append("TEXT 30,160,\"TSS24.BF2\",0,1,1,\"代码: "+product_id+"\"\n");
	qz.append("TEXT 240,160,\"TSS24.BF2\",0,1,1,\"单位: "+unit+"\"\n");
	qz.append("TEXT 30,200,\"TSS24.BF2\",0,1,1,\"名称: "+name+"\"\n");
	qz.append("TEXT 30,240,\"TSS24.BF2\",0,1,1,\"单价: "+price+"\"\n");
	qz.append("TEXT 30,280,\"TSS24.BF2\",0,1,1,\"数量: "+num+"\"\n");
	qz.append("TEXT 200,230,\"TSS24.BF2\",0,2,2,\""+total+"元\"\n");
	qz.append("PRINT 1,1\n" + "EOP\n");
	qz.print();
	console.log('print done.');
}

function initPrinter()
{
	findPrinter("zebra");
}
