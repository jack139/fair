var image_list=[];

function doFirst()
{

(function () {
	var input = $("#images")[0], formdata = false;

	function showUploadedItem (source) {
  		var list = $("#image-list")[0],
	  		li   = document.createElement("li"),
	  		img  = document.createElement("img");
  		img.src = source;
  		li.appendChild(img);
		list.appendChild(li);
	}   

	if (window.FormData) {
  		formdata = new FormData();
  		$("#btn").hide();
	}
	
 	input.addEventListener("change", function (evt) {
 		$("#response").html("正在上传 . . .");
 		var i = 0, len = this.files.length, img, reader, file;
	
		for ( ; i < len; i++ ) {
			file = this.files[i];
	
			if (!!file.type.match(/image.*/)) {
				if ( window.FileReader ) {
					reader = new FileReader();
					reader.onloadend = function (e) { 
						showUploadedItem(e.target.result, file.fileName);
					};
					reader.readAsDataURL(file);
				}
				if (formdata) {
					formdata.append("images", file);
				}
			}	
		}
	
		if (formdata) {
			$.ajax({
				url: "/plat/image",
				type: "POST",
				data: formdata,
				processData: false,
				contentType: false,
				dataType: "json",
				complete: function(xhr, textStatus){
					if(xhr.status==200){
						var retJson = JSON.parse(xhr.responseText);
						if (retJson["ret"]==0){
							$("#response").html("保存为 " + retJson["image"]);
							//$("#images").hide(); 
							formdata = new FormData();
							image_list = image_list.concat(retJson["image"]);
							$("#form_image").val(image_list);
						}
						else{
							$("#response").html("上传失败！"); 
						}
					}
					else{
						$("#response").html("网络异常！("+xhr.status+")");
					}
				}
			});
		}
	}, false);
}());

}