function myFunction() {
  var copyText = document.getElementById("password");
  copyText.select();
  copyText.setSelectionRange(0, 99999); /* For mobile devices */
  navigator.clipboard.writeText(copyText.value);
  alert("Copied the text: " + copyText.value);
}

function openP(){
	alert("Copied the text");
}

function openPage(name){
	window.location.href = "/"+name;
}