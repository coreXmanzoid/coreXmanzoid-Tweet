const mobileControllers = {};
let mobileCurrentUserId = 0;

function abortAndRenew(key) {
    if (mobileControllers[key]) {
        mobileControllers[key].abort();
    }

    mobileControllers[key] = new AbortController();
    return mobileControllers[key];
}

function ajaxWithAbort(key, options) {
    const controller = abortAndRenew(key);
    const signal = controller.signal;
    const callerXhr = options.xhr;

    return $.ajax($.extend({}, options, {
        xhr: function () {
            const xhr = callerXhr ? callerXhr() : $.ajaxSettings.xhr();
            signal.addEventListener("abort", function () {
                xhr.abort();
            });
            return xhr;
        },
        error: function (jqXHR, textStatus, errorThrown) {
            if (textStatus === "abort") {
                return;
            }

            if (typeof options.error === "function") {
                options.error(jqXHR, textStatus, errorThrown);
                return;
            }

            console.error("Ajax error [" + key + "]:", textStatus, errorThrown);
        }
    }));
}

function getCurrentUserId() {
    const fromBody = $("body").data("current-user-id");
    const fromComposer = $(".submit button").data("userid");
    const fromNotifications = $(".notifications").data("userid");
    const fromProfile = $(".info").data("user-id");
    const foundUserId = parseInt(fromComposer || fromNotifications || fromProfile || fromBody || 0, 10);

    if (fromComposer || !mobileCurrentUserId) {
        mobileCurrentUserId = foundUserId || mobileCurrentUserId;
    }

    return mobileCurrentUserId || foundUserId;
}

function getTextNode($element) {
    let textNode = $element.contents().filter(function () {
        return this.nodeType === 3;
    }).first();

    if (!textNode.length) {
        $element.append(" 0");
        textNode = $element.contents().filter(function () {
            return this.nodeType === 3;
        }).first();
    }

    return textNode;
}

function setActionCount($element, count) {
    const $count = $element.find("span").first();

    if ($count.length) {
        $count.text(count);
        return;
    }

    const textNode = getTextNode($element);
    textNode[0].nodeValue = " " + count;
}

function formatRelativeTime(timestamp) {
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) {
        return "";
    }

    const diffMins = Math.max(0, Math.floor((new Date() - date) / 60000));

    if (diffMins < 1) {
        return "Just now";
    }
    if (diffMins < 60) {
        return diffMins === 1 ? "1 min ago" : diffMins + " mins ago";
    }
    if (diffMins < 1440) {
        const hours = Math.floor(diffMins / 60);
        return hours === 1 ? "1 hour ago" : hours + " hours ago";
    }
    if (diffMins < 10080) {
        const days = Math.floor(diffMins / 1440);
        return days === 1 ? "1 day ago" : days + " days ago";
    }
    if (diffMins < 43200) {
        const weeks = Math.floor(diffMins / 10080);
        return weeks === 1 ? "1 week ago" : weeks + " weeks ago";
    }

    const months = Math.floor(diffMins / 43200);
    return months === 1 ? "1 month ago" : months + " months ago";
}

function formatCompactRelativeTime(timestamp) {
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) {
        return "";
    }

    const diffMins = Math.max(0, Math.floor((new Date() - date) / 60000));

    if (diffMins < 1) {
        return "0s";
    }
    if (diffMins < 60) {
        return diffMins + "m";
    }
    if (diffMins < 1440) {
        return Math.floor(diffMins / 60) + "h";
    }
    if (diffMins < 10080) {
        return Math.floor(diffMins / 1440) + "d";
    }
    if (diffMins < 43200) {
        return Math.floor(diffMins / 10080) + "w";
    }

    return Math.floor(diffMins / 43200) + "mo";
}

function parseMentions(value) {
    if (!value) {
        return [];
    }

    try {
        const parsed = JSON.parse(value);
        return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
        return [];
    }
}

function renderMentions(selector) {
    document.querySelectorAll(selector).forEach(function (el) {
        const mentions = parseMentions(el.dataset.mentions);
        let text = el.innerText;

        mentions.forEach(function (mention) {
            const username = mention.username.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
            const regex = new RegExp("@" + username + "\\b", "g");
            text = text.replace(regex, '<span class="mention">@' + mention.username + "</span>");
        });

        el.innerHTML = text;
    });
}

function initializeDynamicContent($root) {
    $root.find(".profile-tab").hide();

    $root.find("textarea[name='post-input']").each(function () {
        updateComposerState($(this));
    });

    if ($root.find(".notifications, #notifications-permission").length) {
        const permissionWarning = document.getElementById("notifications-permission");
        if (permissionWarning) {
            if (!("Notification" in window) || Notification.permission !== "granted") {
                $root.find(".notifications").hide();
            } else {
                $root.find("#notifications-permission").remove();
                $root.find(".notifications").show();
            }
        }
    }

    $root.find(".post-time").each(function () {
        const display = formatRelativeTime($(this).data("timestamp"));
        if (display) {
            $(this).text(display);
        }
    });

    $root.find(".notification-message span").each(function () {
        const display = formatCompactRelativeTime($(this).data("timestamp"));
        if (display) {
            $(this).text(display);
        }
    });

    renderMentions(".post-content .content, .comment-content .content");
    $root.find(".ProfileOptions h6").removeClass("active-a").first().addClass("active-a");
}

function injectHtmlResponse($target, response) {
    const dummy = $("<div>").html(response);
    dummy.find("script").remove();
    $target.html(dummy.html());

    initializeDynamicContent($target);
}

function loadFragment(key, $target, url, loaderHtml) {
    $target.html(loaderHtml);

    return ajaxWithAbort(key, {
        url: url,
        method: "GET",
        success: function (response) {
            injectHtmlResponse($target, response);
        }
    });
}

function setActiveTab(label) {
    $(".navigation .list").removeClass("active");
    $(".navigation .list").filter(function () {
        return $(this).find(".text").text().trim().toLowerCase() === label.toLowerCase();
    }).addClass("active");
}

function setAccountsRowVisible(visible) {
    $(".accounts-row").prop("hidden", !visible).toggle(visible);
}

function setMoreMenuVisible(visible) {
    $(".more-menu-overlay").prop("hidden", !visible);
}

function toggleMoreMenu() {
    const isHidden = $(".more-menu-overlay").prop("hidden");
    setActiveTab("More");
    setMoreMenuVisible(isHidden);
}

function resetOverlay() {
    $(".fullpost-overlay").prop("hidden", true);
    $(".fullpost-box").empty();
    $("body").css("overflow", "");
}

function updateComposerState($textarea) {
    const inputLength = $textarea.val().length;
    const maxLength = 180;
    const progress = (inputLength / maxLength) * 100;
    const circumference = 2 * Math.PI * 22;
    const offset = (progress / 100) * circumference;
    const $container = $textarea.closest(".post-section, .container, body");

    $container.find(".progress-circle-indicator").css("stroke-dashoffset", offset);

    if (progress >= 100) {
        $container.find(".progress-circle-indicator").attr("stroke", "red");
    } else if (progress >= 80) {
        $container.find(".progress-circle-indicator").attr("stroke", "orange");
    } else {
        $container.find(".progress-circle-indicator").attr("stroke", "#3b82f6");
    }

    $container.find(".submit button").prop("disabled", !(inputLength > 0 && inputLength <= maxLength));
}

function showPosts(state, id) {
    loadFragment(
        "mobilePosts",
        $("#feed-post"),
        "/showPosts/" + state + "/" + id,
        '<div class="loader-wrapper"><span class="loader"></span></div>'
    );
}

function showComposer() {
    resetOverlay();
    setActiveTab("Home");
    return loadFragment(
        "mobileComposer",
        $(".post-section"),
        "/profile/0",
        '<div class="loader-wrapper"><span class="loader"></span></div>'
    ).done(function () {
        const userId = $(".submit button").data("userid");
        if (userId) {
            mobileCurrentUserId = parseInt(userId, 10);
            checkForNotifications(mobileCurrentUserId);
        }
    });
}

function showProfile(userId) {
    resetOverlay();
    setActiveTab("Profile");
    setMoreMenuVisible(false);
    setAccountsRowVisible(false);
    loadFragment(
        "mobileProfile",
        $(".post-section"),
        "/profile/" + userId,
        '<div class="loader-wrapper"><span class="loader"></span></div>'
    );
    showPosts(1, userId);
}

function showHome() {
    setMoreMenuVisible(false);
    setAccountsRowVisible(true);
    showComposer();
    showPosts(0, 0);
}

function showLikedPosts() {
    resetOverlay();
    setMoreMenuVisible(false);
    setActiveTab("More");
    setAccountsRowVisible(false);
    $(".post-section").html('<div class="mobile-more-title"><h4>Liked post</h4></div>');
    showPosts(3, getCurrentUserId());
}

function exploreAccounts(url) {
    $("#feed-post").html('<div class="loader-wrapper"><span class="loader"></span></div>');

    ajaxWithAbort("mobileExploreAccounts", {
        url: url,
        method: "GET",
        success: function (response) {
            injectHtmlResponse($("#feed-post"), response);
        }
    });
}

function showSearch() {
    resetOverlay();
    setActiveTab("Search");
    setMoreMenuVisible(false);
    setAccountsRowVisible(false);
    $(".post-section").html(
        '<div class="search">' +
        '<i class="bi bi-search"></i>' +
        '<input type="text" placeholder="Search By Name" autocomplete="off">' +
        "</div>"
    );
    exploreAccounts("/exploreAccounts/0/random");
    $(".search input").trigger("focus");
}

function showNotifications() {
    resetOverlay();
    setActiveTab("Search");
    setMoreMenuVisible(false);
    setAccountsRowVisible(false);
    $("#feed-post").empty();
    loadFragment(
        "mobileNotifications",
        $(".post-section"),
        "/notifications",
        '<div class="loader-wrapper"><span class="loader"></span></div>'
    ).done(function () {
        markAsRead();
    });
}

function showAi() {
    resetOverlay();
    setActiveTab("AI");
    setMoreMenuVisible(false);
    setAccountsRowVisible(false);
    $("#feed-post").empty();
    $(".post-section").html(
        '<div class="Manzoid-container">' +
        '<div class="main-content">' +
        '<div class="ai-header"><img src="/static/assets/logo.png" alt=""> Manzoid AI</div>' +
        '<div id="chat-box" class="chat-box">' +
        "<div class=\"message ai\">Hi, It's Manzoid AI. Ask me anything!</div>" +
        "</div>" +
        '<div class="chat-input">' +
        '<input type="text" id="user-input" autocomplete="off" maxlength="100" placeholder="write a motivation tweet...">' +
        '<button type="button" id="send-ai-message">Send</button>' +
        "</div>" +
        "</div>" +
        "</div>"
    );
}

function markAsRead() {
    const userId = $(".notifications").data("userid") || getCurrentUserId();

    if (!userId) {
        return;
    }

    ajaxWithAbort("mobileMarkAsRead", {
        url: "/notifications/mark_read/" + userId,
        success: function () {
            checkForNotifications(userId);
        }
    });
}

function checkForNotifications(id) {
    if (!id) {
        return;
    }

    ajaxWithAbort("mobileCheckNotifications", {
        url: "/check-notifications/" + id,
        method: "GET",
        success: function (response) {
            const $icon = $("#notification-icon");
            $icon.find(".notification-dot").remove();

            if (response.unread_count > 0) {
                $icon.css("position", "relative").append(
                    '<span class="notification-dot translate-middle badge rounded-circle p-1"></span>'
                );
            }
        }
    });
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

function prependPost(content, userId) {
    const profileImg = $(".newPost img").attr("src") || "/static/assets/default-profile.jpg";
    const tempId = "temp-" + Date.now();
    const timestamp = new Date().toISOString();
    const postHtml =
        '<div class="post info p-1" data-postid="' + tempId + '">' +
        '<div class="post-heading">' +
        '<img src="' + profileImg + '" alt="" width="40" height="40" class="rounded-circle me-2">' +
        '<h5 data-userid="' + userId + '">Posting<br><span>@you</span></h5>' +
        '<small class="post-time" data-timestamp="' + timestamp + '">Just now</small>' +
        '<div class="edit-post ms-auto me-2" title="Edit Post">Posting...</div>' +
        "</div>" +
        '<div class="post-content"><p class="content" data-mentions="[]"></p><p class="hashtag"></p></div>' +
        '<div class="post-actions">' +
        '<a class="comment"><i class="bi bi-chat-heart"></i> 0</a>' +
        '<a class="retweet"><i class="bi bi-repeat"></i> 0</a>' +
        '<a class="like"><i class="bi bi-heart"></i> 0</a>' +
        '<a class="share"><i class="bi bi-share"></i> 0</a>' +
        "</div><hr></div>";

    $("#feed-post").prepend(postHtml);
    $("#feed-post .post").first().find(".post-content .content").text(content);
    initializeDynamicContent($("#feed-post"));
    return tempId;
}

function uploadProfileImage(input, url) {
    const file = input.files[0];
    if (!file) {
        return;
    }

    const formData = new FormData();
    formData.append("profile", file);

    $.ajax({
        url: url,
        type: "POST",
        data: formData,
        contentType: false,
        processData: false,
        success: function (res) {
            if (res.image_url) {
                $(input).closest(".profile-pic-wrapper").find(".profile-pic").attr("src", res.image_url);
                $(".newPost img").attr("src", res.image_url);
            }
        },
        error: function (err) {
            console.error(err.responseJSON || err);
        }
    });
}

function appendNewComment(name, username, content, profileImageUrl, userId) {
    const commentId = "new-" + Date.now();
    const commentHtml =
        '<div class="post-top">' +
        '<div class="post-heading">' +
        '<img src="' + profileImageUrl + '" alt="" width="30" height="30" class="rounded-circle me-2">' +
        '<h5 data-userid="' + userId + '">' + name + " <br><span>@" + username + "</span></h5>" +
        "</div>" +
        '<div class="post-actions comment-actions" data-commentId="' + commentId + '">' +
        '<a class="like-comment"><i class="bi bi-heart"></i> 0</a>' +
        "</div></div>" +
        '<div class="post-content comment-content"><p class="content" data-mentions="[]"></p></div><hr>';

    $(".all-comments .no-data").remove();
    $(".all-comments").prepend(commentHtml);
    $(".all-comments .comment-content .content").first().text(content);
    return $(".all-comments .post-top").first();
}

function submitComment() {
    const postId = $(".fullpost-box .post-detail").data("postid");
    const postUserId = $(".fullpost-box .post-detail .post-heading h5").data("userid");
    const postContent = $(".my-comment input").val().trim();
    const currentUserName = $("#submitComment").data("current_user_name");
    const currentUserUsername = $("#submitComment").data("current_user_username");
    const currentUserProfileImage = $(".my-comment img").attr("src");
    const currentUserId = getCurrentUserId();
    let comments = (parseInt($(".comments span").text(), 10) || 0) + 1;

    if (!postContent || !postId) {
        return;
    }

    $(".my-comment input").val("");
    $("#submitComment").prop("disabled", true);

    const $newComment = appendNewComment(
        currentUserName,
        currentUserUsername,
        postContent,
        currentUserProfileImage,
        currentUserId
    );

    $.ajax({
        url: "/comments/" + postId,
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({
            content: postContent,
            state: 1
        }),
        success: function (response) {
            comments = response.comments_count || comments;
            $(".comments span").text(comments);
            $('.post[data-postid="' + postId + '"] .comment').each(function () {
                setActionCount($(this), comments);
            });
            $newComment.next(".comment-content").find(".content").attr("data-mentions", JSON.stringify(response.mentions || []));
            initializeDynamicContent($(".fullpost-box"));

            sendNotification({
                recipientId: postUserId,
                title: "New Comment",
                type: "new_comment",
                identifier: postId,
                message: currentUserName + " commented on your post.",
                state: 3
            });

            $.ajax({
                url: "/send-mention-notifications",
                method: "POST",
                data: JSON.stringify({
                    post_id: response.comment_id,
                    state: "comment"
                }),
                headers: { "Content-Type": "application/json" }
            });
        },
        error: function () {
            $newComment.next(".comment-content").next("hr").remove();
            $newComment.next(".comment-content").remove();
            $newComment.remove();
            $(".comments span").text(Math.max(comments - 1, 0));
            alert("Failed to submit comment. Please try again.");
        },
        complete: function () {
            $("#submitComment").prop("disabled", false);
        }
    });
}

function showFullPost(e) {
    if (e) {
        e.preventDefault();
    }

    const $post = $(this).closest(".post");
    const postId = $post.data("postid");

    if (!postId || String(postId).indexOf("temp-") === 0) {
        return;
    }

    $(".post").removeClass("active-post");
    $post.addClass("active-post");
    $(".fullpost-overlay").prop("hidden", false);
    $("body").css("overflow", "hidden");

    loadFragment(
        "mobileComments",
        $(".fullpost-box"),
        "/comments/" + postId,
        '<div class="loader-wrapper"><span class="loader"></span></div>'
    );
}

function addMessage(text, sender) {
    const $chatBox = $("#chat-box");
    const $msg = $("<div></div>").addClass("message " + sender).text(text);

    $chatBox.append($msg);
    $chatBox.scrollTop($chatBox[0].scrollHeight);
}

function sendMessage() {
    const $input = $("#user-input");
    const text = $input.val().trim();
    const userId = getCurrentUserId();

    if (!text || !userId) {
        return;
    }

    addMessage(text, "user");
    $input.val("");

    const $typing = $('<div class="message ai typing-indicator"><span></span><span></span><span></span></div>');
    $("#chat-box").append($typing);

    $.ajax({
        url: "/Manzoid-AI",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({
            message: text,
            user_id: userId
        }),
        success: function (data) {
            $typing.remove();
            addMessage(data.reply || "AI service error.", "ai");
        },
        error: function () {
            $typing.remove();
            addMessage("Network error.", "ai");
        }
    });
}

$(function () {
    showHome();

    $(document).on("click", ".navigation .list a", function (e) {
        e.preventDefault();
        const label = $(this).find(".text").text().trim();

        if (label === "Home") {
            showHome();
        } else if (label === "Search") {
            showSearch();
        } else if (label === "More") {
            toggleMoreMenu();
        } else if (label === "AI") {
            showAi();
        } else if (label === "Profile") {
            showProfile(getCurrentUserId());
        }
    });

    $(document).on("click", function (e) {
        if (!$(e.target).closest(".more-menu-overlay, .navigation .list").length) {
            setMoreMenuVisible(false);
        }
    });

    $(document).on("click", ".more-menu-overlay", function (e) {
        e.stopPropagation();
    });

    $(document).on("click", ".more-menu-item[data-more-action='liked']", function () {
        showLikedPosts();
    });

    $(document).on("click", ".more-menu-item[data-more-action='switch']", function () {
        if (confirm("Are you sure you want to switch accounts? Unsaved changes will be lost.")) {
            window.location.href = "/logout/2";
        } else {
            setMoreMenuVisible(false);
        }
    });

    $("#notification-icon").on("click", showNotifications);

    $(document).on("click", "#verifyBtn", function () {
        const userId = getCurrentUserId();
        const $button = $(this);

        $button.prop("disabled", true);
        $button.html('<span class="btn-loader"></span>Sending...');

        ajaxWithAbort("mobileEmailVerification", {
            url: "/email-verification",
            method: "POST",
            data: JSON.stringify({ user_id: userId }),
            contentType: "application/json",
            success: function (response) {
                if (response.status === "success") {
                    $button.html('<span class="btn-loader"></span>Verification in progress...');
                    if ($("#verification-status").length === 0) {
                        $button.after('<strong id="verification-status" class="verification-tag">Verification email sent! Please check your inbox.</strong>');
                    }
                } else {
                    $button.prop("disabled", false).text("Send Verification Email");
                    alert("Failed to send verification email. Please try again.");
                }
            },
            error: function () {
                $button.prop("disabled", false).text("Send Verification Email");
            }
        });
    });

    $(document).on("click", ".notification-header .bi-arrow-left, .backtohome", function (e) {
        e.preventDefault();
        showHome();
    });

    $(document).on("input", ".search input", function () {
        const query = $(this).val().trim();
        exploreAccounts(query ? "/exploreAccounts/0/" + encodeURIComponent(query) : "/exploreAccounts/0/random");
    });

    $(document).on("click", ".top-pages h6", function (e) {
        e.preventDefault();
        $(".top-pages h6").removeClass("active-a");
        $(this).addClass("active-a");
        showPosts(parseInt($(this).data("state"), 10), $(this).data("userid"));
    });

    $(document).on("input", "textarea[name='post-input']", function () {
        updateComposerState($(this));
    });

    $(document).on("click", ".submit button", function () {
        const $button = $(this);
        const $textarea = $("textarea[name='post-input']");
        const content = $textarea.val().trim();
        const userId = $button.data("userid");

        if (!content) {
            updateComposerState($textarea);
            return;
        }

        $textarea.val("");
        updateComposerState($textarea);
        $button.prop("disabled", true);

        const tempPostId = prependPost(content, userId);

        ajaxWithAbort("mobileSubmitPost", {
            url: "/managePosts/1",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ content: content, user_id: userId }),
            success: function (response) {
                if (response.status !== "success") {
                    $('#feed-post .post[data-postid="' + tempPostId + '"]').remove();
                    alert("Failed to post. Please try again.");
                    return;
                }

                const $newPost = $('#feed-post .post[data-postid="' + tempPostId + '"]');
                $newPost.attr("data-postid", response.post_id);
                $newPost.find(".post-content .hashtag").text(response.hashtags);
                $newPost.find(".post-content .content").attr("data-mentions", JSON.stringify(response.mentions || []));
                $newPost.find(".post-time").attr("data-timestamp", response.timestamp).text("Just now");
                $newPost.find(".edit-post").remove();
                initializeDynamicContent($("#feed-post"));

                sendNotification({
                    title: "New Post",
                    type: "new_post",
                    identifier: response.post_id,
                    senderId: userId,
                    message: response.username + " has just posted a new tweet.",
                    state: 2,
                    Push: "true"
                });

                $.ajax({
                    url: "/send-mention-notifications",
                    method: "POST",
                    data: JSON.stringify({
                        post_id: response.post_id,
                        state: "post"
                    }),
                    headers: { "Content-Type": "application/json" }
                });
            },
            error: function () {
                $('#feed-post .post[data-postid="' + tempPostId + '"]').remove();
                alert("An error occurred. Please try again.");
            }
        });
    });

    $(document).on("click", ".ProfileOptions h6", function () {
        $(".ProfileOptions h6").removeClass("active-a");
        $(this).addClass("active-a");

        const option = $(this).text().trim();
        const userId = $(".ProfileOptions").attr("class").split(" ")[1] || getCurrentUserId();

        if (option === "Posts") {
            showPosts(1, userId);
        } else if (option === "Likes") {
            showPosts(3, userId);
        } else if (option === "Reposts") {
            showPosts(4, userId);
        }
    });

    $(document).on("click", ".post-heading h5", function () {
        const profileId = $(this).data("userid") || $(this).data("accountid");
        if (profileId) {
            showProfile(profileId);
        }
    });

    $(document).on("click", ".accounts-row .account", function () {
        const profileId = $(this).data("accountid");
        if (profileId) {
            showProfile(profileId);
        }
    });

    $(document).on("click", ".full-account .follow button", function (e) {
        e.preventDefault();
        e.stopPropagation();

        const $button = $(this);
        const accountId = $button.closest(".full-account").find("h5").data("accountid");
        const isFollowing = $button.text().trim() === "Following";

        $button.text(isFollowing ? "Follow" : "Following");

        $.ajax({
            url: "/follows/" + accountId + "/" + (isFollowing ? "2" : "1"),
            type: "POST",
            success: function (response) {
                if (!isFollowing) {
                    sendNotification({
                        recipientId: accountId,
                        title: "New Follower",
                        type: "new_follower",
                        identifier: response.follower_id,
                        message: response.follower_name + " started following you.",
                        Push: "true",
                        state: 3
                    });
                }
            },
            error: function () {
                $button.text(isFollowing ? "Following" : "Follow");
            }
        });
    });

    $(document).on("click", ".profile-pic-wrapper", function () {
        $(this).find("#profileInput").trigger("click");
    });

    $(document).on("change", "#profileInput", function () {
        const userId = $(this).closest(".info").data("user-id");
        if (confirm("Are you sure you want to update your profile picture?")) {
            uploadProfileImage(this, "/update-profile/" + userId);
        } else {
            this.value = "";
        }
    });

    $(document).on("click", ".followers", function () {
        showSearch();
        exploreAccounts("/exploreAccounts/" + $(this).attr("class").split(" ")[1] + "/followers");
    });

    $(document).on("click", ".following", function () {
        showSearch();
        exploreAccounts("/exploreAccounts/" + $(this).attr("class").split(" ")[1] + "/following");
    });

    $(document).on("dblclick", ".post", showFullPost);
    $(document).on("click", ".comment", showFullPost);
    $(document).on("click", ".back-post > i", resetOverlay);
    $(document).on("click", "#submitComment", submitComment);
    $(document).on("keydown", ".my-comment input", function (e) {
        if (e.key === "Enter") {
            e.preventDefault();
            submitComment();
        }
    });

    $(document).on("click", ".like, .likes", function (e) {
        e.preventDefault();

        const $btn = $(this);
        if ($btn.data("loading")) {
            return;
        }

        $btn.data("loading", true);
        const $icon = $btn.find("i");
        const postId = $btn.closest(".post, .post-detail").data("postid");
        const wasLiked = $btn.hasClass("text-warning") || $icon.hasClass("bi-heart-fill");
        const textNode = $btn.find("span").length ? null : getTextNode($btn);
        const count = parseInt($btn.find("span").text() || textNode.text().trim(), 10) || 0;

        $btn.toggleClass("text-warning", !wasLiked);
        $icon.toggleClass("bi-heart-fill", !wasLiked).toggleClass("bi-heart", wasLiked);
        setActionCount($btn, wasLiked ? count - 1 : count + 1);

        $.ajax({
            url: "/PostAction/1",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ post_id: postId, like: !wasLiked }),
            success: function (res) {
                setActionCount($btn, res.likes);
            },
            error: function () {
                $btn.toggleClass("text-warning", wasLiked);
                $icon.toggleClass("bi-heart-fill", wasLiked).toggleClass("bi-heart", !wasLiked);
                setActionCount($btn, count);
            },
            complete: function () {
                $btn.data("loading", false);
            }
        });
    });

    $(document).on("click", ".retweet, .retweets", function (e) {
        e.preventDefault();

        const $btn = $(this);
        if ($btn.data("loading")) {
            return;
        }

        $btn.data("loading", true);
        const $icon = $btn.find("i");
        const postId = $btn.closest(".post, .post-detail").data("postid");
        const wasReposted = $btn.hasClass("text-warning");
        const textNode = $btn.find("span").length ? null : getTextNode($btn);
        const count = parseInt($btn.find("span").text() || textNode.text().trim(), 10) || 0;

        $btn.toggleClass("text-warning", !wasReposted);
        setActionCount($btn, wasReposted ? count - 1 : count + 1);
        $icon.removeClass("rotate");
        void $icon[0].offsetWidth;
        $icon.addClass("rotate");

        $.ajax({
            url: "/PostAction/2",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ post_id: postId, repost: !wasReposted }),
            success: function (res) {
                setActionCount($btn, res.reposts);
            },
            error: function () {
                $btn.toggleClass("text-warning", wasReposted);
                setActionCount($btn, count);
            },
            complete: function () {
                $btn.data("loading", false);
            }
        });
    });

    $(document).on("click", ".share, .shares", function (e) {
        e.preventDefault();

        const $btn = $(this);
        const postId = $btn.closest(".post, .post-detail").data("postid");
        const text = $btn.closest(".post, .post-detail").find(".post-content .content").first().text().trim();
        const shareData = {
            title: "ChatFlick Post",
            text: text || "Check out this post on ChatFlick",
            url: "https://ChatFlick.pythonanywhere.com"
        };

        let shareDone;

        if (navigator.share) {
            shareDone = navigator.share(shareData);
        } else if (navigator.clipboard && window.isSecureContext) {
            shareDone = navigator.clipboard.writeText(shareData.text + "\n" + shareData.url).then(function () {
                alert("Post copied to clipboard!");
            });
        } else {
            shareDone = Promise.reject(new Error("Sharing is not available"));
        }

        shareDone.then(function () {
            $.ajax({
                url: "/PostAction/4",
                method: "POST",
                contentType: "application/json",
                data: JSON.stringify({ post_id: postId }),
                success: function (res) {
                    if (typeof res.shares === "number") {
                        setActionCount($btn, res.shares);
                    }
                }
            });
        }).catch(function (err) {
            if (!err || err.name !== "AbortError") {
                console.error("Share failed:", err);
            }
        });
    });

    $(document).on("click", ".like-comment", function (e) {
        e.preventDefault();

        const $btn = $(this);
        const $icon = $btn.find("i");
        const textNode = getTextNode($btn);
        const likes = parseInt(textNode.text().trim(), 10) || 0;
        const wasLiked = $icon.hasClass("bi-heart-fill");
        const postId = $btn.closest(".comment-actions").data("commentid");

        $btn.toggleClass("text-warning", !wasLiked);
        $icon.toggleClass("bi-heart-fill", !wasLiked).toggleClass("bi-heart", wasLiked);
        textNode[0].nodeValue = " " + (wasLiked ? likes - 1 : likes + 1);

        $.ajax({
            url: "/PostAction/3",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ post_id: postId, like: !wasLiked }),
            success: function (res) {
                textNode[0].nodeValue = " " + res.likes;
            },
            error: function () {
                $btn.toggleClass("text-warning", wasLiked);
                $icon.toggleClass("bi-heart-fill", wasLiked).toggleClass("bi-heart", !wasLiked);
                textNode[0].nodeValue = " " + likes;
            }
        });
    });

    $(document).on("click", "#send-ai-message", sendMessage);
    $(document).on("keydown", "#user-input", function (e) {
        if (e.key === "Enter") {
            e.preventDefault();
            sendMessage();
        }
    });
});
