var post_info = {
    post_id: [],
    likes: [],
    shares: [],
    retweets: [],
}
exploreAccounts("/exploreAccounts/random");
function exploreAccounts(url) {
    
    // show explore accounts
    $.ajax({
        url: url,
        method: "GET",
        success: function (response) {

            // Create dummy container to extract HTML + scripts
            let dummy = $("<div>").html(response);
            
            // Extract script tags
            let scripts = dummy.find("script");

            // Remove scripts from HTML
            dummy.find("script").remove();

            // Insert cleaned HTML into div3
            $(".explore-accounts").html(dummy.html());

            // Execute extracted scripts manually
            scripts.each(function () {
                let code = $(this).text();
                if (code.trim() !== "") {
                    eval(code);
                }
            });
        }
    });
}

// fetch accounts for search textbox typed input
$(".search input").on("input", function () {
    var query = $(this).val();
    if (query.length > 0) {
        exploreAccounts("/exploreAccounts/" + query);
    }else{
        exploreAccounts("/exploreAccounts/random");
    }

});
// Active sidebar animation
$(".nav li a").click(function () {
    $(".nav a").removeClass("active link-dark");
    $(".nav a").addClass("link-dark");
    $(this).addClass("active");
    $(this).removeClass("link-dark");
});

// Active footer navbar animation
$(".footer-navbar a").click(function () {
    $(".footer-navbar a").removeClass("icons");
    $(this).addClass("icons");
});
// Show posts.html
$(".div3").load("/randomPosts/0/0");
// Refresh button functionality and returning current likes
$(".div4 button").click(function (e) {

    // get the text node that holds the count (if any)

    $(".post-heading h5").each(function () {
        var post_id = Number($(this).attr("class"));
        post_info.post_id.push(post_id);
    });
    $(".like").each(function () {
        var $btn = $(this);
        var textNode = $btn.contents().filter(function () { return this.nodeType === 3; }).first();
        post_info.likes.push(textNode.length ? parseInt(textNode[0].nodeValue.trim().match(/\d+/)[0], 10) : 0);
    });
    $(".share").each(function () {
        var $btn = $(this);
        var textNode = $btn.contents().filter(function () { return this.nodeType === 3; }).first();
        post_info.shares.push(textNode.length ? parseInt(textNode[0].nodeValue.trim().match(/\d+/)[0], 10) : 0);
    });
    $(".retweet").each(function () {
        var $btn = $(this);
        var textNode = $btn.contents().filter(function () { return this.nodeType === 3; }).first();
        post_info.retweets.push(textNode.length ? parseInt(textNode[0].nodeValue.trim().match(/\d+/)[0], 10) : 0);
    });
    $.ajax({
        url: "/randomPosts/0/0",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify(post_info),
        success: function (response) {
            // extract script content
            let dummy = $("<div>").html(response);
            let scripts = dummy.find("script");

            // remove scripts from HTML
            dummy.find("script").remove();

            // insert HTML without scripts
            $(".div3").html(dummy.html());

            // run script code manually
            scripts.each(function () {
                eval($(this).text());
            });
        }
    });

    post_info = {
        post_id: [],
        likes: [],
        shares: [],
        retweets: [],
    };
});

$(".post-button").click(function () {
    $("textarea").focus();
});

$(".explore-button").click(function () {
    $(".full-post").hide();
    $(".explore-tab").show();
    $(".search input").focus();
});

// Initially hide full post section
$(".full-post").hide();


// show profile on clicking profile link
$(".profile-link").click(function () {
    user_id = $(".div1").attr("class").split(" ")[1];
    $(".div2").load("/profile/" + user_id);
    $(".full-post").hide();
    $(".explore-tab").show();
    $.ajax({
        url: "/randomPosts/1/" + user_id,
        method: "GET",
        success: function (response) {

            // Create dummy container to extract HTML + scripts
            let dummy = $("<div>").html(response);

            // Extract script tags
            let scripts = dummy.find("script");

            // Remove scripts from HTML
            dummy.find("script").remove();

            // Insert cleaned HTML into div3
            $(".div3").html(dummy.html());

            // Execute extracted scripts manually
            scripts.each(function () {
                let code = $(this).text();
                if (code.trim() !== "") {
                    eval(code);
                }
            });
        }
    });

});
// show Home on clicking home link
$(".home-link").click(function () {
    $(".div2").load("/profile/0");
    $(".full-post").hide();
    $(".explore-tab").show();
    $.ajax({
        url: "/randomPosts/0/0",
        method: "GET",
        success: function (response) {

            // Create dummy container to extract HTML + scripts
            let dummy = $("<div>").html(response);

            // Extract script tags
            let scripts = dummy.find("script");

            // Remove scripts from HTML
            dummy.find("script").remove();

            // Insert cleaned HTML into div3
            $(".div3").html(dummy.html());

            // Execute extracted scripts manually
            scripts.each(function () {
                let code = $(this).text();
                if (code.trim() !== "") {
                    eval(code);
                }
            });
        }
    });

});

// Control foryou and following active link
$(".div2 a").click(function () {
    $(".div2 a").removeClass("active-a");
    $(this).addClass("active-a");
});

// Control textarea input characters and progress of circle
$("textarea").on("input", function () {
    var inputLength = $(this).val().length;
    var maxLength = 150;
    var progress = (inputLength / maxLength) * 100;

    var circumference = 2 * Math.PI * 22;
    var offset = (progress / 100) * circumference;
    if (progress >= 100) {
        $(".progress-circle-indicator").attr("stroke", "red");
    } else if (progress >= 80) {
        $(".progress-circle-indicator").attr("stroke", "orange");
    } else {
        $(".progress-circle-indicator").attr("stroke", "#3b82f6");
    }
    $(".progress-circle-indicator").css("stroke-dashoffset", offset);

    if (inputLength > 0 && inputLength <= maxLength) {
        $("button[type='submit']").prop("disabled", false);
    } else {
        $("button[type='submit']").prop("disabled", true);
    }
});