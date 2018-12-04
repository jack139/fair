
function addLog(strTips)
{
	var image = $("<div>"+strTips+"</div>");
	image.appendTo(($("#action_log")));
}

/* 开始派送 */
function to_dispatch()
{
	order_id = $("#single_order_id").val();
	$.ajax({
		type: "POST",
		url: "/online/order_dispatch",
		async: true,
		timeout: 15000,
		data: {order_id:order_id},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status == 403)
			{
				addLog("网络异常！(403) "+order_id);
				$("#single_order_id").focus();
			}
			else if(xhr.status==200)
			{
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					//$("#"+retJson["id"]).remove();
					addLog("提交成功："+order_id);
					$("#single_order_id").focus();
				}
				else {
					addLog("提交失败："+retJson["msg"]+" "+order_id);
					$("#single_order_id").focus();
				}
			}
			else
			{
				addLog("网络异常！("+xhr.status+") "+order_id);
				$("#single_order_id").focus();
			}
		}
	});
	
	return false;
}
