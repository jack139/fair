function doFirst()
{

(function () {
	var input = $("#images")[0], 
		formdata = false;

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
  		$("#btn")[0].style.display = "none";
	}
	
 	input.addEventListener("change", function (evt) {
 		$("#response")[0].innerHTML = "Uploading . . ."
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
						if (retJson["ret"]==0)
							$("#response")[0].innerHTML = "保存为 " + retJson["image"]; 
						else
							$("#response")[0].innerHTML = "上传失败！"; 
					}
					else{
						$("#response")[0].innerHTML = "网络异常！("+xhr.status+")";
					}
				}
			});
		}
	}, false);
}());

}