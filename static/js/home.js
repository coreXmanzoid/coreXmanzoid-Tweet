// ---------------------------------------------------------------------------
// Keyed AbortController map — one controller slot per logical action.
// Calling abortAndRenew(key) cancels any in-flight request for that key and
// returns a fresh AbortController whose signal can be forwarded to fetch().
// jQuery $.ajax does NOT natively support AbortSignal, so we adapt via the
// `xhr` factory option (see ajaxWithAbort helper below).
// ---------------------------------------------------------------------------
const controllers = {};

/**
 * Aborts any active request for `key`, then creates and stores a new
 * AbortController for that key.
 * @param {string} key - Logical action identifier.
 * @returns {AbortController}
 */
function abortAndRenew(key) {
    if (controllers[key]) {
        controllers[key].abort(); // cancel previous in-flight request
    }
    controllers[key] = new AbortController();
    return controllers[key];
}

/**
 * Thin wrapper around $.ajax that wires an AbortSignal into jQuery's XHR
 * factory so that calling controller.abort() actually cancels the request.
 *
 * @param {string}         key     - Controller map key (matches abortAndRenew).
 * @param {Object}         options - Standard $.ajax options (url, method, …).
 * @returns {jqXHR}
 */
function ajaxWithAbort(key, options) {
    const controller = abortAndRenew(key);
    const signal = controller.signal;

    // Capture any caller-supplied xhr factory so we can chain it.
    const callerXhr = options.xhr;

    return $.ajax({
        ...options,
        // jQuery lets us supply the raw XHR object; we hook abort() here.
        xhr: function () {
            const xhr = callerXhr ? callerXhr() : $.ajaxSettings.xhr();
            // Mirror AbortController cancellation onto the native XHR.
            signal.addEventListener("abort", () => xhr.abort());
            return xhr;
        },
        // Wrap error handler to silently swallow aborted requests.
        error: function (jqXHR, textStatus, errorThrown) {
            if (textStatus === "abort") {
                // Request was intentionally cancelled — not a real error.
                return;
            }
            // Delegate to any caller-supplied error handler, otherwise log.
            if (typeof options.error === "function") {
                options.error(jqXHR, textStatus, errorThrown);
            } else {
                console.error("Ajax error [" + key + "]:", textStatus, errorThrown);
            }
        }
    });
}

// ---------------------------------------------------------------------------
// Reusable helper: inject HTML response (with embedded <script> execution)
// into a jQuery target element.
// ---------------------------------------------------------------------------
function injectHtmlResponse($target, response) {
    const dummy = $("<div>").html(response);
    const scripts = dummy.find("script");
    dummy.find("script").remove();
    $target.html(dummy.html());
    scripts.each(function () {
        const code = $(this).text();
        if (code.trim() !== "") {
            eval(code); // eslint-disable-line no-eval
        }
    });
}

// ---------------------------------------------------------------------------
// fetch accounts for explore accounts section
// ---------------------------------------------------------------------------
exploreAccounts("/exploreAccounts/0/random");

function exploreAccounts(url) {
    $(".explore-accounts").html('<div class="loader-wrapper"><span class="loader"></span></div>');

    // Abort any previous exploreAccounts request before starting a new one.
    ajaxWithAbort("exploreAccounts", {
        url: url,
        method: "GET",
        success: function (response) {
            injectHtmlResponse($(".explore-accounts"), response);
        }
        // error is handled by ajaxWithAbort (aborts silenced, others logged)
    });
}

// ---------------------------------------------------------------------------
// fetch accounts for search textbox typed input
// (each keystroke cancels the previous search request)
// ---------------------------------------------------------------------------
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

// ---------------------------------------------------------------------------
// Show posts
// (rapid tab / filter switches cancel the previous showPosts request)
// ---------------------------------------------------------------------------
function showPosts(state, id) {
    $(".div3").html('<div class="page-loader page-loader--posts"><span class="loader1"></span></div>');

    // Abort any pending showPosts request before issuing a new one.
    ajaxWithAbort("showPosts", {
        url: "/showPosts/" + state + "/" + id,
        method: "GET",
        success: function (response) {
            injectHtmlResponse($(".div3"), response);
        }
    });
}

// ---------------------------------------------------------------------------
// Email verification button
// (only one verification request should ever be in-flight at a time)
// ---------------------------------------------------------------------------
$(".verification-box button").click(function () {
    userId = $(".div1").attr("class").split(" ")[1];
    const button = $("#verifyBtn");
    button.prop("disabled", true);
    button.html(`
            <span class="btn-loader"></span>
            Sending...
        `);

    // Abort any prior verification request (e.g. double-click guard).
    ajaxWithAbort("emailVerification", {
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
                <strong id="verification-status" class="verification-tag">
                    Verification email sent! Please check your inbox.
                </strong>
            `);
                }
            } else {
                alert("Failed to send verification email. Please try again.");
            }
        }
    });
});

// ---------------------------------------------------------------------------
// Show posts.html on initial load
// ---------------------------------------------------------------------------
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

// ---------------------------------------------------------------------------
// Mark all notifications as read after the tab loads
// ---------------------------------------------------------------------------
function markAsRead() {
    userId = $(".notifications").data("userid");

    // Abort any pending markAsRead call (e.g. rapid tab re-opens).
    ajaxWithAbort("markAsRead", {
        url: `/notifications/mark_read/${userId}`,
        success: function (response) {
            user_id = $(".div1").attr("class").split(" ")[1];
            checkForNotifications(user_id);
            console.log("Notifications marked as read:", response);
        },
        error: function (err) {
            console.error("Error marking notifications as read:", err);
        }
    });
}

// ---------------------------------------------------------------------------
// Notification tab — load + render notifications
// (re-clicking the bell cancels any unfinished previous load)
// ---------------------------------------------------------------------------
$(".notifications-button").click(function () {
    $(".full-post").hide();
    $(".notifications-tab").show();
    $(".explore-tab").hide();
    $(".ai-bar").hide();
    $(".notifications-tab").html('<div class="loader-wrapper"><span class="loader"></span></div>');
    $(".notifications-tab").load("/notifications");

    // Abort any in-flight notifications fetch before starting a new one.
    ajaxWithAbort("loadNotifications", {
        url: "/notifications",
        method: "GET",
        success: function (response) {
            injectHtmlResponse($(".notifications-tab"), response);
            markAsRead();
        }
    });
});

// ---------------------------------------------------------------------------
// AI button — no fetch here; kept as-is
// ---------------------------------------------------------------------------
$(".ai-button").click(function () {
    $(".full-post").hide();
    $(".div2").hide();
    $(".div3").html('<div class="loader-wrapper"><span class="loader"></span></div>');
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

// ---------------------------------------------------------------------------
// Fetching liked posts
// ---------------------------------------------------------------------------
$(".likes-button").click(function () {
    var user_id = $(".div1").attr("class").split(" ")[1];
    showPosts(3, user_id);
    exploreAccounts("/exploreAccounts/0/random");
    $(".div2").hide();
    $(".full-post").hide();
    $(".ai-bar").hide();
    $(".explore-tab").show();
    $(".notifications-tab").hide();
});

// ---------------------------------------------------------------------------
// Show profile
// (clicking another profile while one is loading cancels the first request)
// ---------------------------------------------------------------------------
function showProfile(user_id) {
    $(".div2").html('<div class="page-loader page-loader--profile"><span class="loader2"></span></div>');

    // Abort any in-flight profile request.
    ajaxWithAbort("showProfile", {
        url: "/profile/" + user_id,
        method: "GET",
        success: function (response) {
            injectHtmlResponse($(".div2"), response);
            $(".full-post").hide();
            $(".ai-bar").hide();
            $(".explore-tab").show();
            $(".notifications-tab").hide();
            showPosts(1, user_id);
        }
    });
}

$(".profile-link").click(function () {
    user_id = $(".div1").attr("class").split(" ")[1];
    showProfile(user_id);
});

// ---------------------------------------------------------------------------
// Back to home
// ---------------------------------------------------------------------------
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
}
$(".home-link").click(Backtohome);

// Show posts based on "For You" / "Following" tabs
$(document).on("click", ".top-pages h6", function (e) {
    e.preventDefault();
    e.stopPropagation();

    $(".top-pages h6").removeClass("active-a");
    $(this).addClass("active-a");

    var state = parseInt($(this).data("state"));
    var user_id = $(this).data("userid");
    showPosts(state, user_id);
    return false;
});

// ---------------------------------------------------------------------------
// Show full post method
// ---------------------------------------------------------------------------
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
        // reload specific part of page without refreshing entire page
        $(".coreXmanzoid").load("/comments/" + post_id);
    } else {
        $post.removeClass("active-post");
        $(".explore-tab").show();
        $(".full-post").hide();
    }
}

// ---------------------------------------------------------------------------
// Send notification helper (fire-and-forget; no abort needed)
// ---------------------------------------------------------------------------
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

// ---------------------------------------------------------------------------
// newPost.html script
// ---------------------------------------------------------------------------

// Control for-you and following active link
$(".div2 a").click(function () {
    $(".div2 a").removeClass("active-a");
    $(this).addClass("active-a");
});

function prependPost(content, userId) {
    let profileImg = $("#dropdownUser2 img").attr("src");
    let username = $("#dropdownUser2 strong").data("username");
    let name = $("#dropdownUser2 strong").text().trim();
    let tempId = "temp-" + Date.now();
    let timestamp = new Date().toISOString();
    let postHTML = `
    <div class="post info p-1" data-postid="${tempId}">
        <div class="post-heading">
            <img src="${profileImg}" alt="" width="40" height="40" class="rounded-circle me-2">
            <h5 class="${userId}">${name}<br /><span>@${username}</span></h5>
            <small class="post-time" data-timestamp="${timestamp}">Just now</small>
            <div class="edit-post ms-auto me-2" title="Edit Post">
                Posting...
            </div>
        </div>
        <div class="post-content">
            <p class="content" data-mentions='[]'></p>
            <p class="hashtag"></p>
        </div>

        <div class="post-actions">
            <a class="comment"><i class="bi bi-chat-heart"></i> 0</a>
            <a class="retweet"><i class="bi bi-repeat"></i> 0</a>
            <a class="like"><i class="bi bi-heart"></i> 0</a>
            <a class="share"><i class="bi bi-share"></i> 0</a>
        </div>
        <hr>
    </div>
    `;

    $(".div3").prepend(postHTML);
    $(".div3 .post").first().find(".post-content .content").text(content);
    return tempId;
}

// ---------------------------------------------------------------------------
// Submit post
// (duplicate submissions are blocked by the disabled button, but we also
// abort any prior in-flight submit request for safety)
// ---------------------------------------------------------------------------
$(".submit button").on("click", function () {
    var content = $("textarea[name='post-input']").val();
    var userId = $(this).data("userid");
    var tempPostId;

    $("textarea").val("");
    $(".progress-circle-indicator").css("stroke-dashoffset", 0);
    $(".progress-circle-indicator").attr("stroke", "#3b82f6");
    $(".submit button").prop("disabled", true);

    tempPostId = prependPost(content, userId);

    // Abort any previous submitPost request (e.g. rapid double-submit).
    ajaxWithAbort("submitPost", {
        url: "/managePosts/1",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({ content: content, user_id: userId }),
        success: function (response) {
            if (response.status === "success") {
                var $newPost = $('.div3 .post[data-postid="' + tempPostId + '"]');
                $newPost.attr("data-postid", response.post_id);
                $newPost.find(".post-content .hashtag").text(response.hashtags);
                $newPost.find(".post-content .content").attr("data-mentions", JSON.stringify(response.mentions));
                $newPost.find(".post-time").attr("data-timestamp", response.timestamp).text("Just now");
                $newPost.find(".edit-post").attr("title", "Edit Post").html(`<svg style="width: 22px; cursor:pointer" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640">
                    <path
                        d="M505 122.9L517.1 135C526.5 144.4 526.5 159.6 517.1 168.9L488 198.1L441.9 152L471 122.9C480.4 113.5 495.6 113.5 504.9 122.9zM273.8 320.2L408 185.9L454.1 232L319.8 366.2C316.9 369.1 313.3 371.2 309.4 372.3L250.9 389L267.6 330.5C268.7 326.6 270.8 323 273.7 320.1zM437.1 89L239.8 286.2C231.1 294.9 224.8 305.6 221.5 317.3L192.9 417.3C190.5 425.7 192.8 434.7 199 440.9C205.2 447.1 214.2 449.4 222.6 447L322.6 418.4C334.4 415 345.1 408.7 353.7 400.1L551 202.9C579.1 174.8 579.1 129.2 551 101.1L538.9 89C510.8 60.9 465.2 60.9 437.1 89zM152 128C103.4 128 64 167.4 64 216L64 488C64 536.6 103.4 576 152 576L424 576C472.6 576 512 536.6 512 488L512 376C512 362.7 501.3 352 488 352C474.7 352 464 362.7 464 376L464 488C464 510.1 446.1 528 424 528L152 528C129.9 528 112 510.1 112 488L112 216C112 193.9 129.9 176 152 176L264 176C277.3 176 288 165.3 288 152C288 138.7 277.3 128 264 128L152 128z" />
                    </svg>`
                );
                $(".submit button").prop("disabled", true);

                sendNotification({
                    title: "New Post",
                    type: "new_post",
                    identifier: response.post_id,
                    senderId: userId,
                    message: response.username + " has just posted a new tweet.",
                    state: 2,
                    Push: "true"
                }).done(function (res) {
                    console.log("Notification saved:", res);
                }).fail(function (err) {
                    console.error("Failed to send notification:", err);
                });

                // Mention notifications — fire-and-forget, no abort needed.
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
        error: function (jqXHR, textStatus) {
            // ajaxWithAbort already silences "abort"; only real errors reach here.
            alert("An error occurred. Please try again.");
        }
    });
});

// Control textarea input characters and progress circle
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

// ---------------------------------------------------------------------------
// Check for unread notifications on page load (and after marking as read)
// (rapid successive calls cancel the previous one)
// ---------------------------------------------------------------------------
user_id = $(".div1").attr("class").split(" ")[1];
checkForNotifications(user_id);

function checkForNotifications(id) {
    // Abort any pending check before issuing a new one.
    ajaxWithAbort("checkNotifications", {
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
