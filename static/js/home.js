// fetch accounts for explore accounts section
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

// Show posts
function showPosts(state, id) {
    $.ajax({
        url: "/showPosts/" + state + "/" + id,
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

$(".verification-box button").click(function () {
    userId = $(".div1").attr("class").split(" ")[1];
    const button = $("#verifyBtn");
    button.prop("disabled", true);
    button.html(`
            <span class="btn-loader"></span>
            Sending...
        `);
    $.ajax({
        url: "/email-verification",
        method: "POST",
        data: JSON.stringify({ user_id: userId }),
        contentType: "application/json",
        success: function (response) {

            if (response.status === "success") {
                button.html(`
                    <span class="btn-loader"></span>
                    Verification in progress...
                `);
                if ($("#verification-status").length === 0) {
                    button.after(`
                <small id="verification-status" class="verification-tag">
                    Verification email sent! Please check your inbox.
                </small>
            `);
                }

            } else {

                alert("Failed to send verification email. Please try again.");
            }
        }
    });
});

// Show posts.html
$(".div3").load("/showPosts/0/0");
// Refresh button functionality
$(".div4 button").click(function (e) {
    $(".ai-bar").hide();
    $(".notifications-tab").hide();
    $(".full-post").hide();
    $(".explore-tab").show();
    $(".div3").load("/showPosts/0/0");
});

// switch account functionality
$(".switch-account-link").click(function () {
    confirmSwitch = confirm("Are you sure you want to switch accounts? Unsaved changes will be lost.");
    if (confirmSwitch) {
        window.location.href = "/logout/2";
    } else {
        Backtohome();
    }
});

// Notification tab functionality
$(".notifications-button").click(function () {
    $(".notifications-tab").load("/notifications");
    $.ajax({
        url: "/notifications",
        method: "GET",
        success: function (response) {
            $(".full-post").hide();
            $(".notifications-tab").show();
            $(".explore-tab").hide();
            $(".ai-bar").hide();
            // Create dummy container to extract HTML + scripts
            let dummy = $("<div>").html(response);
            // Extract script tags
            let scripts = dummy.find("script");
            // Remove scripts from HTML
            dummy.find("script").remove();
            // Insert cleaned HTML into notifications-tab
            $(".notifications-tab").html(dummy.html());
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

$(".ai-button").click(function () {
    $(".full-post").hide();
    $(".div2").hide();
    $(".div3").load("/Manzoid-AI");
    $(".explore-tab").hide();
    $(".ai-bar").show();
    $(".notifications-tab").hide();
});

$(".post-button").click(function () {
    Backtohome();
    $("textarea").focus();
});

$(".explore-button").click(function () {
    $(".full-post").hide();
    $(".ai-bar").hide();
    $(".explore-tab").show();
    $(".search input").focus();
    $(".notifications-tab").hide();
});
// fetching likes posts
$(".likes-button").click(function () {
    var user_id = $(".div1").attr("class").split(" ")[1];
    showPosts(3, user_id);
    exploreAccounts("/exploreAccounts/0/random");
    // $(".div2").load("/profile/0");
    $(".div2").hide();
    $(".full-post").hide();
    $(".ai-bar").hide();
    $(".explore-tab").show();
    $(".notifications-tab").hide();
});

// show profile on clicking profile link
function showProfile(user_id) {
    $.ajax({
        url: "/profile/" + user_id,
        method: "GET",
        success: function (response) {
            // Create dummy container to extract HTML + scripts
            let dummy = $("<div>").html(response);

            // Extract script tags
            let scripts = dummy.find("script");

            // Remove scripts from HTML
            dummy.find("script").remove();

            // Insert cleaned HTML into div3
            $(".div2").html(dummy.html());

            // Execute extracted scripts manually
            scripts.each(function () {
                let code = $(this).text();
                if (code.trim() !== "") {
                    eval(code);
                }
            });
            $(".full-post").hide();
            $(".ai-bar").hide();
            $(".explore-tab").show();
            $(".notifications-tab").hide();
            showPosts(1, user_id);
        }
    })
};
$(".profile-link").click(function () {
    user_id = $(".div1").attr("class").split(" ")[1]
    showProfile(user_id);
});

// show Home on clicking home link & back to home from profile
function Backtohome() {
    $(".div2").load("/profile/0");
    $(".full-post").hide();
    $(".ai-bar").hide();
    $(".notifications-tab").hide();
    $(".explore-tab").show();
    $(".nav a").removeClass("active link-dark");
    $(".nav a").addClass("link-dark");
    $(".home-link").addClass("active");
    $(".home-link").removeClass("link-dark");
    $(".div2").show();
    showPosts(0, 0);
    // requestNotificationPermission();
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
function showFullPost(e) {
    if (e) {
        e.preventDefault();
    }
    var $post = $(this).closest(".post");
    if ($post.length === 0) {
        $post = $(".post.active-post").first();
    }
    if ($post.length === 0) {
        $(".explore-tab").show();
        $(".full-post").hide();
        $(".notifications-tab").hide();
        return;
    }
    var post_id = $post.data("postid");
    var active_post = $post.hasClass("active-post");

    $(".post").removeClass("active-post");

    if (!active_post) {
        $post.addClass("active-post");
        $(".explore-tab").hide();
        $(".ai-bar").hide();
        $(".full-post").show();
        $(".notifications-tab").hide();
        // reload sepecific part of page without refreshing entire page and implementing on specific div
        $('.coreXmanzoid').load('/comments/' + post_id);
    } else {
        $post.removeClass("active-post");
        $(".explore-tab").show();
        $(".full-post").hide();
    }
}

function sendNotification({
    recipientId,
    title,
    identifier,
    message,
    type = "general",
    senderId,
    state,
    Push = "false"
}) {
    return $.ajax({
        url: "/send-notification-route/" + state + "/" + Push,
        type: "POST",
        data: JSON.stringify({
            recipient_id: recipientId,
            title: title,
            identifier: identifier,
            message: message,
            type: type,
            sender_id: senderId
        }),
        contentType: "application/json"
    });
}

// newPost.html script

// Control foryou and following active link
$(".div2 a").click(function () {
    $(".div2 a").removeClass("active-a");
    $(this).addClass("active-a");
});

$(".submit button").on("click", function () {
    var content = $("textarea[name='post-input']").val();
    var userId = $(this).data("userid");
    $.ajax({
        url: "/managePosts/1",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({ content: content, user_id: userId }),
        success: function (response) {
            if (response.status === "success") {
                // Optionally, you can clear the textarea and reset the progress circle
                $("textarea").val("");
                $(".progress-circle-indicator").css("stroke-dashoffset", 0);
                $(".progress-circle-indicator").attr("stroke", "#3b82f6");
                $(".submit button").prop("disabled", true);
                // Prepend the new post to the feed without refreshing
                showPosts(0, 0);
                sendNotification({
                    title: "New Post",
                    type: "new_post",
                    identifier: response.post_id,
                    senderId: userId,
                    message: response.username + " has just posted a new tweet.",
                    state: 2, // send the notification to all followers.
                    Push: "true"
                }).done(function (res) {
                    console.log("Notification saved:", res);
                }).fail(function (err) {
                    console.error("Failed to send notification:", err);
                });

                $.ajax({
                    url: "/send-mention-notifications",
                    method: "POST",
                    data: JSON.stringify({
                        post_id: response.post_id,
                        state: "post"
                    }),
                    headers: { "Content-Type": "application/json" },
                    success: function (res) {
                        console.log("Mention notifications sent:", res);
                    },
                    error: function (err) {
                        console.error("Failed to send mention notifications:", err);
                    }
                });

            } else {
                alert("Failed to post. Please try again.");
            }
        },
        error: function () {
            alert("An error occurred. Please try again.");
        }
    });
});
// Control textarea input characters and progress of circle
$("textarea").on("input", function () {
    var inputLength = $(this).val().length;
    var maxLength = 180;
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
        $(".submit button").prop("disabled", false);
    } else {
        $(".submit button").prop("disabled", true);
    }
});

// see if the user have recieved any notification and show notification tab dot.
user_id = $(".div1").attr("class").split(" ")[1];
checkForNotifications(user_id);
function checkForNotifications(id) {
    $.ajax({
        url: "/check-notifications/" + id,
        method: "GET",
        success: function (response) {

            const $btn = $(".notifications-button");
            const $svg = $btn.find("svg");

            // Wrap SVG only once
            if (!$svg.parent().hasClass("bell-wrapper")) {
                $svg.wrap('<span class="bell-wrapper position-relative d-inline-block"></span>');
            }

            const $wrapper = $btn.find(".bell-wrapper");

            if (response.unread_count > 0) {

                if ($wrapper.find(".notification-dot").length === 0) {
                    $wrapper.append(`
                        <span class="notification-dot 
                                     translate-middle 
                                     badge rounded-circle p-1">
                        </span>
                    `);
                }

            } else {
                $wrapper.find(".notification-dot").remove();
            }
        },
        error: function () {
            console.error("Failed to check notifications");
        }
    });
}