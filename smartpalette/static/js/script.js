$(document).ready(function(){

    //Upload image modal -- Saves selected variables and ¿Image Data?
   $('#image-info').click(function() {
      var image_data = readFile();
      var color_number = $('#paletteNumberSelect').val();
   });


   //Grab username and password inputs -- Create account modal
   $('#create-account').click(function() {
      var username = $('#new_username').val();
      var password = $('#new_password').val();
   });


    //Grab username and password inputs -- Login modal
   $('#login-account').click(function() {
       var username = $('#username').val();
       var password = $('#password').val();
   });



});


//Loads image to display
//Need to store image data
function readFile() {
    var reader = new FileReader();
    reader.onload = function(){
        var output = document.getElementById('output');
        output.src = reader.result;
    };
    reader.readAsDataURL(event.target.files[0]);
};


