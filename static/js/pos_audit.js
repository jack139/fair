
function new_audit()
{
/*
	r = alertify.prompt("账期开始时间 1)续上一个期末；2)从当前开始，输入数字：", function (e, str1) {
		if (str1==null || str1==""){
			alertify.warning("请输入1或2！");
		}
		else {
			cate = parseFloat(str1);
			if (isNaN(cate))
				alertify.warning("请输入数字 1 或 2！");
			else if (cate==1 || cate==2)
				doNewAudit(cate);
			else
				alertify.warning("请输入数字 1 或 2！");
		}
	});
*/
	doNewAudit(1);
	return false;
}

function doNewAudit(cate)
{
	$.ajax({
		type: "POST",
		url: "/pos/audit",
		async: true,
		timeout: 15000,
		data: {cate:cate},
		dataType: "json",
		complete: function(xhr, textStatus)
		{
			if(xhr.status==200){
				var retJson = JSON.parse(xhr.responseText);
				if (retJson["ret"]==0){
					alertify.warning(retJson["msg"]);
					window.location.href="/pos/audit";
				}
				else {
					alertify.error("添加盘点账期失败："+retJson["msg"]);
				}
			}
			else{
				alertify.error("网络异常！("+xhr.status+")");
			}
		}
	});
}
