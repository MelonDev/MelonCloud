function myFunction() {
  var copyText = document.getElementById("password");
  copyText.select();
  copyText.setSelectionRange(0, 99999); /* For mobile devices */
  navigator.clipboard.writeText(copyText.value);
  alert("Copied the text: " + copyText.value);
}

function copyToClipboard() {
  var copyText = document.getElementById("password");
  var dummy = document.createElement("input");
  document.body.appendChild(dummy);
  dummy.value = copyText.value;
  dummy.select();
  dummy.setSelectionRange(0, 99999);
  document.execCommand("copy");
  document.body.removeChild(dummy);
  alert("Copied the text: " + copyText.value);
}

function logout() {
    var path = "/meloncloud-book/logout";
    console.log(path);
	window.location.href = path;
}

function callAPI(total_page,id){
	var page  = document.getElementById("select-page").value;
	var limit  = document.getElementById("select-limit").value;
	var artist  = document.getElementById("select-artist").value;
	var language  = document.getElementById("select-language").value;

	if(total_page != null && id != null){
	if(id == -2){
	    page = 1;
	}
	else if(id == -1){
	page = page - 1;
	}
	else if(id == -3){
	    page = page + 1;
	}
	else if(id == -4){
	page = total_page.toString();
	}
	else {
	page = id.toString();
	}
}
	var path = "?";

		if(limit == "-1"){
			path = path+"&infinite="+true;
		}else {
		        if(page == ""){
				path = path+"page=1&limit="+limit;
		        }else {
		        				path =  path+"page="+page+"&limit="+limit;

		        }

		}
		if(artist != "null"){
			path = path+"&artist="+artist;
		}
	if(language != "null"){
			path = path+"&language="+language;
		}



	//window.location.href = "/pwg_v2?step=" + step + "&length=" + length + action;
	window.location.href = "/meloncloud-book"+path;
}

