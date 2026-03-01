var emailFound = false;
var passwordValid = true;
var usernameFound = false;
$("input[name = 'username']").on("keydown", function (event) {
    var username = $("input[name = 'username']").val() + event.key;
    $.ajax({
        url: "/signup/1",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({"username": username}),
        success: function (response) {
            if (response.status == 'abondonded') {
                    $("input[name = 'username']").after("<small class='ur' style='color: red;'><br/>*Username already exists<br/></small>");
                    usernameFound = true;
            } else if (response.status == 'success'){
                $('.ur').remove();
                usernameFound = false;
            }
        }
    });
    if (passwordValid == false || emailFound == true || usernameFound == true) {
        $(".submitbutton").prop("disabled", true);
    } else {
        $(".submitbutton").prop("disabled", false);
    }
});


function isEmailValid(){
    var emailAlreadyExist = data["emailAlreadyExist"];
    emailFound = false;
    if (emailAlreadyExist == "true") {
            $("input[name = 'email']").after("<small class='em' style='color: red;'><br/>*Email already taken.<br/></small>");
            emailFound = true;
        }
    
    if (emailFound == false) {
        $('.em').remove();
    }
    if (passwordValid == false || emailFound == true || usernameFound == true) {
        $(".submitbutton").prop("disabled", true);
    } else {
        $(".submitbutton").prop("disabled", false);
    }
}

// isEmailValid();
$("#userPassword").on("keyup", function () {
    var password = $(this).val();
    var strength = 0;
    if (password.length >= 8) strength++;
    if (password.match(/[a-z]+/)) strength++;
    if (password.match(/[A-Z]+/)) strength++;
    if (password.match(/[0-9]+/)) strength++;
    if (password.match(/[\W]+/)) strength++;
    var strengthText = "";
    switch (strength) {
        case 0:
        case 1:
            strengthText = "*Very Weak";
            break;
        case 2:
            strengthText = "*Weak";
            break;
        case 3:
            strengthText = "*Moderate";
            break;
        case 4:
            strengthText = "*Strong";
            break;
        case 5:
            strengthText = "*Very Strong";
            break;
    }
    passwordValid = password.length >= 8;
    if (!passwordValid || emailFound || usernameFound) {
        $(".submitbutton").prop("disabled", true);
    } else {
        $(".submitbutton").prop("disabled", false);
    }
    $('#passwordStrength').text("Password Strength: " + strengthText);
});
