var unit_price;
//var inventory_num;

function first()
{
	if (!ableToPrint)
		document.getElementById("qz-status").style.background = "#FFFFFF";
	$("#weight").focus();
}

function check_key()
{
	var weight = parseFloat($('#weight').val());
	if (isNaN(weight)) { weight = 0.00; }
	var weight_price = unit_price*weight;
	$("#price_show").html(weight_price.toFixed(2));
	//$("#inventory_num").html((inventory_num-weight).toFixed(2));
}

function doWeight()
{
	var product_id=$("#id_product_id").val();
	var sku=$("#id_sku").val();
	//var shop=$("#id_shop").val();
	var price=$("#id_price").val();
	var weight=parseFloat($("#weight").val());

	if (isNaN(weight)){
		alertify.warning("请输入数字！");
		$("#weight").focus();
		return false;
	}
	else if (weight<=0){
		alertify.warning("重量必须大于零！");
		$("#weight").focus();
		return false;		
	}

	$.ajax({
		type: "POST",
		url: "/pos/weight_sku",
		async: true,
		timeout: 15000,
		data: {product_id:product_id, sku:sku, price:price, weight:weight},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status==200)
			{
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					/* 成功 */
					alertify.warning("保存成功！称重ID："+retJson["data"]["product_id"]);
					$("#price_show").html("0.00");
					//$("#inventory_num").html(retJson["data"]["invent_num"]);
					//inventory_num=parseFloat(retJson["data"]["invent_num"]);
					$("#weight").val("");
					if (ableToPrint) print_label(retJson["data"]);
					$("#weight").focus();
				}
				else {
					alertify.error("保存称重数据失败："+retJson["msg"]);
					$("#weight").focus();
				}
			}
			else
			{
				alertify.error("网络异常！("+xhr.status+")");
				$("#weight").focus();
			}
			
			return false;
		}
	});
	
	return false;
}

/* 打印标签 */
function print_label(data)
{
	if (notReady()) { return; }
	
	var date=(new Date()).toLocaleString();

	var name = $("#id_name").html();
	var product_id = data["product_id"];
	var price = data["price"];
	var weight = data["weight"];
	var total = data["total"];
	var unit = $("#id_unit").html();

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
	qz.append("TEXT 25,30,\"TSS24.BF2\",0,1,1,\"U掌柜 <优鲜美味，掌上专柜> urfresh.cn\"\n");
	//qz.append("TEXT 25,30,\"TSS24.BF2\",0,1,1,\""+date+"\"\n");
	qz.append("BARCODE 30,70,\"128M\",80,0,0,4,12,\"!104" + 
		product_id[0]+"!099"+product_id.substring(1)+"\"\n");
	//"PRINT LEN000,1"
	qz.append("TEXT 30,160,\"TSS24.BF2\",0,1,1,\"代码: "+product_id+"\"\n");
	qz.append("TEXT 240,160,\"TSS24.BF2\",0,1,1,\"单位: "+unit+"\"\n");
	qz.append("TEXT 30,200,\"TSS24.BF2\",0,1,1,\"名称: "+name+"\"\n");
	qz.append("TEXT 30,240,\"TSS24.BF2\",0,1,1,\"单价: "+price+"\"\n");
	qz.append("TEXT 30,280,\"TSS24.BF2\",0,1,1,\"数量: "+weight+"\"\n");
	qz.append("TEXT 200,230,\"TSS24.BF2\",0,2,2,\""+total+"元\"\n");
	qz.append("PRINT 1,1\n" + "EOP\n");
	qz.print();
	console.log('print done.');

}

function initPrinter()
{
	findPrinter("zebra");
}
