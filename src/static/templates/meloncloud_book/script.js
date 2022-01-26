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

function callAPI(){
	var step  = document.getElementById("password").value;
	console.log(step);

	//window.location.href = "/pwg_v2?step=" + step + "&length=" + length + action;
}