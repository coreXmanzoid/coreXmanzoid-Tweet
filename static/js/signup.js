$('#Showpassword').click(function(){
    if (this.value == "0"){
        $('#userPassword').attr('type', 'text');
        this.value = "1";
    }else if(this.value == "1"){
        $('#userPassword').attr('type', 'password');
        this.value = "0";        
    }
});
$("#userPassword").on("keyup", function() {
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
    if(password.length >= 8){
        $(".submitbutton").prop("disabled", false);
    }else{
        $(".submitbutton").prop("disabled", true);
    }
    $('#passwordStrength').text("Password Strength: " + strengthText);
});

$(".submitbutton").click(function(){
    confirm("We will send you an OTP on your email. Make sure to entered a correct Email.");
});
if (data.page == "signup") {
    
    $('.signup-form').show();
    $('.confirm-email-form').hide();
}

if (data.page == "confirmEmail"){
    $('.confirm-email-form').show();
    $('.signup-form').hide();
}