var emailFound = false;
var usernameFound = false;
var passwordValid = true;

$("input[name = 'username']").on("keydown", function (event) {
    var username = $("input[name = 'username']").val() + event.key;
    var usernames = data["usernames"];
    usernameFound = false;
    usernames.forEach(function (value, index) {
        if (username == value) {
            $("input[name = 'username']").after("<small class='ur' style='color: red;'><br/>*Username already exists<br/></small>");
            usernameFound = true;
        }
    });
    if (usernameFound == false) {
        $('.ur').remove();
    }
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

isEmailValid();

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

$(".submitbutton").click(function () {
    confirm("We will send you an OTP on your email. Make sure to entered a correct Email.");
});

if (data.page == "confirmEmail") {
    $("input[name='OTP1']").focus();
}

$(".confirm-email-form input").on("keydown", function (event) {
    var index = $(this).index(".confirm-email-form input");
    if (event.key >= 0 && event.key <= 9) {
        event.preventDefault();
        $(this).val(event.key);

        if (index < $('.confirm-email-form input').length - 1) {
            $(".confirm-email-form input").eq(index + 1).focus();
        } else if (event.key == "Backspace") {
            event.preventDefault();
            $(this).val("");
            if (index > 0) {
                $(".confirm-email-form input").eq(index - 1).focus();
            }
        }
    }
});