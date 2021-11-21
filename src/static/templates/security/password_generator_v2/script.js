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

function callAPI(){
	var step  = document.getElementById("input-step").value;
	var length = document.getElementById("input-length").value;
	var collapse = document.getElementById("collapseOne").className;
	var isShow = collapse.includes("show");
	var action = isShow ? "&action=show" : "";

	window.location.href = "/pwg_v2?step=" + step + "&length=" + length + action;
}