var post_info = {
    post_id: [],
    shares: [],
    retweets: [],
}
exploreAccounts("/exploreAccounts/0/random");
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
        exploreAccounts("/exploreAccounts/0/" + query);
    } else {
        exploreAccounts("/exploreAccounts/0/random");
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
// Show posts
function showPosts(state, id) {
    $.ajax({
        url: "/randomPosts/"+ state + "/" + id,
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
}
// Show posts.html
$(".div3").load("/randomPosts/0/0");
// Refresh button functionality and returning current likes
$(".div4 button").click(function (e) {
    
    // get the text node that holds the count (if any)

    $(".info").each(function () {
        var post_id = Number($(this).attr("class").split(' ')[1]);
        post_info.post_id.push(post_id);
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
            showPosts(0, 0);
        }
    });
    
    post_info = {
        post_id: [],
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

$(".likes-button").click(function () {
    var user_id = $(".div1").attr("class").split(" ")[1];
    showPosts(3, user_id);
    exploreAccounts("/exploreAccounts/0/random");
    $(".div2").load("/profile/0");
    $(".full-post").hide();
    $(".explore-tab").show();
});
// Initially hide full post section
$(".full-post").hide();


// show profile on clicking profile link
function showProfile(user_id) {
    $(".div2").load("/profile/" + user_id);
    $(".full-post").hide();
    $(".explore-tab").show();
   showPosts(1, user_id);
};
$(".profile-link").click(function () {
    user_id = $(".div1").attr("class").split(" ")[1]
    showProfile(user_id);
});
// show Home on clicking home link & back to home from profile
function Backtohome() {
    $(".div2").load("/profile/0");
    $(".full-post").hide();
    $(".explore-tab").show();
    $(".nav a").removeClass("active link-dark");
    $(".nav a").addClass("link-dark");
    $(".home-link").addClass("active");
    $(".home-link").removeClass("link-dark");
    showPosts(0, 0);
}
$(".home-link").click(Backtohome);
// show posts based on for you and following tabs
$(document).on("click", ".div2 a", function (e) {
    e.preventDefault();   // STOP navigation
    e.stopPropagation();  // EXTRA safety

    $(".div2 a").removeClass("active-a");
    $(this).addClass("active-a");

    var state = parseInt($(this).data("state"));
    var user_id = $(this).data("userid");
    showPosts(state, user_id);
    return false;
});

// show full post method
function showFullPost() {
    var $post = $(this).closest(".post");
    var post_id = $post.attr("class").split(' ')[1];
    var active_post = $post.hasClass("active-post");

    $(".post").removeClass("active-post");

    if (!active_post) {
        $post.addClass("active-post");
        $(".explore-tab").hide();
        $(".full-post").show();
        // reload sepecific part of page without refreshing entire page and implementing on specific div
        $('.coreXmanzoid').load('/comments/' + post_id + '/nill/0');
    } else {
        $post.removeClass("active-post");
        $(".explore-tab").show();
        $(".full-post").hide();
    }
}

// Control textarea input characters and progress of circle
$("textarea").on("input", function () {
    var inputLength = $(this).val().length;
    var maxLength = 200;
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