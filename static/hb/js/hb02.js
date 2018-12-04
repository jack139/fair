
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
						url: "/wx/red_envelope_1017",
						async: true,
						timeout: 15000,
						data: {phone_num:num,hb_id:"002"},
						dataType: "json",
						complete: function(xhr,textStatus)
						{
							if(xhr.status==200){
								var retJson = JSON.parse(xhr.responseText);
								if(retJson['ret'] == 0){
									$("#quan_back").addClass("Oct_quan1");
									$("#pic_background").show();
									$("#txt_image").attr("src","images/txt2.png");
									$("#title_1").html("恭喜你已获得");
									$("#title_2").html(retJson['money']+"元水果券");
									//$("#title_3").html("7日内有效");
									//$("#title_4").html("抵用券已放入U掌柜"+num+"账户中").show();
									//$("#title_5").html("");
									$("#buttons_1").hide();
									$("#buttons_2").show();
								}else if(retJson['ret'] == -4){
									$("#quan_back").addClass("Oct_quan1");
									$("#pic_background").show();
									$("#title_1").html("很抱歉");
									$("#title_2").html("您已领过该红包");
									//$("#title_3").html("");
									//$("#title_4").html("");	
									$("#buttons_1").hide();
									$("#buttons_2").show();	
								}else if(retJson['ret'] == -3){
									$("#quan_back").addClass("Oct_quan1");
									//$("#pic_background").show();
									$("#title_1").html("很抱歉");
									$("#title_2").html("红包已过期");
									//$("#title_3").html("");
									//$("#title_4").html("");
									$("#guoqi_txt").show();	
									$("#buttons_1").hide();
									$("#buttons_3").show();
									
								}else if(retJson['ret'] == -5){
									$("#quan_back").addClass("Oct_quan1");
									$("#pic_background").show();
									$("#title_1").html("很抱歉");
									$("#title_2").html("红包已领完");
									//$("#title_3").html("");
									//$("#title_4").html("");	
									$("#buttons_1").hide();
									$("#buttons_3").show();	
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
	var title1 = '你的好友U掌柜送你水果大礼包，快来拆！';
	var title2 = 'U掌柜1000万大红包，只为你的一口鲜。';
	var title3 = '人在江湖飘，哪能没红包？大掌柜@我，1000万请你吃水果';
	var img_url = 'http://wx.urfresh.cn/static/hb/images/hb.png';
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

			        wx.ready(function () {

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
				                title: title3,
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
				});
			}
		}
	});

	//$("#title_2").html('here');
})();

