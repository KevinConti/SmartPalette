$(document).ready(function () {

    //Upload image modal -- Saves selected variables and ¿Image Data?
    //Initiates preview of palette with options
    $('#image-info').click(function (evt) {
        evt.preventDefault();
        //Get selected palette input
        var color_number = $('#paletteNumberSelect').val();
        var palette_height = ($('#output').height()) / color_number;
        var palette_width = ($('#output').width() - 15);

        //Create new divs to add
        var upload_button = ("<div id='share-button' class= 'upload-button'>Upload</div>");
        var new_image_button = ("<div id='try-again' class= 'upload-button'>Try Again</div>");
        var color_placeholders = ("<div class='palette-block'></div>");

        //Remove contents then add appropriate amount of new palette blocks
        $('#uploadModal .fade-out').remove();
        $('#uploadModal .modal-title').fadeOut(500);
        $('#uploadModal #image-info').remove();
        $('#uploadModal .modal-footer').append(new_image_button).append(upload_button);

        for (i = 0; i < color_number; i++) {
            $('#uploadModal #right-column').fadeIn(1500).append(color_placeholders);
        }

        //Add loop to assign generated colors to display
        //Red assigned for testing
        $('.palette-block').each(function () {
            $(this).css('background-color', 'red');
        })

        $('.palette-block').css('width', palette_width).css('height', palette_height);
        ;

        //Refresh page and restart modal to re-do palette
        $('#try-again').click(function () {
            location.reload();
            $('#uploadModal').modal('show');
        })

        $('#share-button').click(function () {
            // Check login
            // Create div and add to gallery template
        })

    });


    //Grab username and password inputs -- Create account modal
    $('#create-account').click(function () {
        var username = $('#new_username').val();
        var password = $('#new_password').val();
    });


    //Grab username and password inputs -- Login modal
    $('#login-account').click(function () {
        var username = $('#username').val();
        var password = $('#password').val();
    });


});


//Loads image to display
//Need to store image data
function readFile() {
    var reader = new FileReader();
    reader.onload = function () {
        var output = document.getElementById('output');
        output.src = reader.result;
    };
    reader.readAsDataURL(event.target.files[0]);
};


