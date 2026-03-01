$(".reset-password-form input").on("input", function() {
    var email = $(".reset-password-form input[name='email']").val();
    if (email.trim() !== "") {
        $(".reset-password-form .submitbutton").prop("disabled", false);
    } else {
        $(".reset-password-form .submitbutton").prop("disabled", true);
    }
});
$(".reset-password-form button").on("click", function(e) {
    e.preventDefault();
    var email = $(".reset-password-form input[name='email']").val();
    $(".reset-password-form .submitbutton").prop("disabled", true);
    $(".reset-password-form input[name='email']").prop("disabled", true);
    
    $.ajax({
        type: "POST",
        url: "/reset-password",
        data: JSON.stringify({ 'email': email }),
        headers: { "Content-Type": "application/json" },
        success: function(response) {
            if (response.status === "success") {
                window.location.href = "/reset-password";
                $(".reset-password-form input[name='email']").val(email);
                $(".reset-password-form input[name='email']").prop("disabled", true);
            } else {
                alert("Error: " + response.message);
            }
        },
        error: function() {
            alert("An error occurred while sending the reset email. Please try again.");
        }
    });
});

$(".new-password-form button").on("click", function(e) {
    e.preventDefault();
    var newPassword = $(".new-password-form input[name='newPassword']").val();
    var confirmNewPassword = $(".new-password-form input[name='confirmNewPassword']").val();
    $.ajax({
        type: "POST",
        url: window.location.pathname,
        data: JSON.stringify({ 'newPassword': newPassword, 'confirmNewPassword': confirmNewPassword }),
        headers: { "Content-Type": "application/json" },
        success: function(response) {
            if (response.status === "success") {
                window.location.href = "/login";
            } else {
                alert("Error: " + response.message);
            }
        },
        error: function() {
            alert("An error occurred while resetting the password. Please try again.");
        }
    });
});

$("input[name='newPassword'], input[name='confirmNewPassword']").on("keyup", function () {
    var password = $("input[name='newPassword']").val();
    var confirmNewPassword = $("input[name='confirmNewPassword']").val();
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
    if (!passwordValid || password !== confirmNewPassword) {
        $(".submitbutton").prop("disabled", true);
    } else {
        $(".submitbutton").prop("disabled", false);
    }
    $('#newpasswordStrength').text("Password Strength: " + strengthText);
});
