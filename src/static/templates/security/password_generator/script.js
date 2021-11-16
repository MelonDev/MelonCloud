function myFunction() {
  /* Get the text field */
  var copyText = document.getElementById("password");

  /* Select the text field */
  copyText.select();
  copyText.setSelectionRange(0, 99999); /* For mobile devices */

  /* Copy the text inside the text field */
  navigator.clipboard.writeText(copyText.value);

  /* Alert the copied text */
  alert("Copied the text: " + copyText.value);
}

function copyToClipboard() {
  var copyText = document.getElementById("password");

  var dummy = document.createElement("input");

  // Add it to the document
  document.body.appendChild(dummy);

  // Set value of input
  dummy.value = copyText.value;

  /* Select the text field */
  dummy.select();
  dummy.setSelectionRange(0, 99999); /* For mobile devices */

  /* Copy the text inside the text field */
  document.execCommand("copy");

  // Remove it as its not needed anymore
  document.body.removeChild(dummy);

  /* Alert the copied text */
  alert("Copied the text: " + copyText.value);
}