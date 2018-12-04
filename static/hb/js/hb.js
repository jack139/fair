
function share_receive_red_envelope(){
	var num = $("#phone_number").val();
	var patt1 = /[^0-9]/g;
	if(num != ''){
		if(num.match(patt1) == null){
			var first_num = num.substr(0, 1);
			if(first_num == '1'){
				if(num.length == 11){
				
					$.ajax({
						type: "POST",
						url: "/wx/red_envelope_action",
						async: true,
						timeout: 15000,
						data: {phone_num:num,hb_id:"001"},
						dataType: "json",
						complete: function(xhr,textStatus)
						{
							if(xhr.status==200){
								var retJson = JSON.parse(xhr.responseText);
								if(retJson['ret'] == 0){
									$("#txt_image").attr("src","images/txt2.png");
									$("#title_1").html("恭喜你已获得");
									$("#title_2").html(retJson['money']+"元水果券");
									$("#title_3").html("7日内有效");
									$("#title_4").html("抵用券已放入U掌柜"+num+"账户中").show();
									$("#title_5").html("");
									$("#buttons_1").hide();
									$("#buttons_2").show();
								}else if(retJson['ret'] == -4){
									$("#already_have").show();
								}else if(retJson['ret'] == -3){
									$("#title_1").html("很抱歉");
									$("#title_2").html("红包已过期");
									$("#title_3").html("");
									$("#title_4").html("");	
									$("#buttons_1").hide();
									$("#buttons_2").show();									
								}else if(retJson['ret'] == -5){
									$("#quan_back").addClass("quan_ed");
									$("#title_1").html("很抱歉");
									$("#title_2").html("红包已领完");
									$("#title_3").html("");
									$("#title_4").html("");	
									$("#buttons_1").hide();
									$("#buttons_2").show();									
								}else if(retJson['ret'] == -2 || retJson['ret'] == -1){
									alert(retJson['msg']);	
								}
							}
							else{
								alert("网络异常，请稍后再试。("+xhr.status+")");
							}
						}
					});
				}else{
					alert('请输入11位手机号！');
					$("#phone_number").val("");
					$("#phone_number").focus();
					return false;
				}
			}else{
				alert('请输入手机号码！'); /* 首位不为1 */
				$("#phone_number").focus();
				return false;
			}
		}else{
			alert('手机号只能为数字！');
			$("#phone_number").val("");
			$("#phone_number").focus();
			return false;
		}
	}else{
		alert('请填写手机号！');
		$("#phone_number").focus();
		return false;
	}
	return false;
}


(function() {
	var currUrl = window.location.href.replace(window.location.hash, '');
	var title1 = '你的江湖好友U掌柜送了200元红包，快试试手气！';
	var title2 = 'U掌柜200万中秋红包任性发，只为结交江湖好友！';
	var img_url = 'http://wx.urfresh.cn/static/hb/images/hb.jpg';
	var hb_url = currUrl;
	$.ajax({
		type: "POST",
		url: "/wx/signature",
		async: true,
		timeout: 15000,
		data: {currUrl:currUrl},
		dataType: "json",
		complete: function(xhr,textStatus)
		{
			if(xhr.status==200){
				var retJson = JSON.parse(xhr.responseText);

				//alert(xhr.responseText);

			        wx.config({
			        	debug     : false,
			                appId     : retJson['appid'],
			                timestamp : retJson['timestamp'],
			                nonceStr  : retJson['nonceStr'],
			                signature : retJson['sign'],
			                jsApiList : [
			                    // 所有要调用的 API 都要加到这个列表中
			                    'checkJsApi',
			                    'onMenuShareTimeline',
			                    'onMenuShareAppMessage',
			                    'getNetworkType',
			                    'closeWindow',
			                ],
			                success: function (res) {
			                },
			                fail: function(res) {
			                },
			                complete: function(res) {
			                }
			        });

			        // 分享给朋友
			        wx.onMenuShareAppMessage({
			                title: title1,
			                desc: title2,
			                link: hb_url,
			                imgUrl: img_url,
			                trigger: function (res) {
			                },
			                success: function (res) {
			                },
			                cancel: function (res) {
			                },
			                fail:function (res) {
			                }
			        });
			 
			        // 分享到朋友圈
			        wx.onMenuShareTimeline({
			                title: title1,
			                link: hb_url,
			                imgUrl: img_url,
			                trigger: function (res) {
			                },
			                success: function (res) {
			                },
			                cancel: function (res) {
			                },
			                fail:function (res) {
			                }
			        });

			}
		}
	});

	//$("#title_2").html('here');
})();

