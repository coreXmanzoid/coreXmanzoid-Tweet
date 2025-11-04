var post_info = {
    post_id: [],
    likes: [],
    shares: [],
    retweets: []
}


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

// Control foryou and following active link
$(".div2 a").click(function () {
    $(".div2 a").removeClass("active-a");
    $(this).addClass("active-a");
});
// Like button functionality
$(".like").click(function (e) {
    e.preventDefault();
    var $btn = $(this);
    var $icon = $btn.find("i");
    var wasLiked = $icon.hasClass("bi-heart-fill");

    // toggle heart icon
    $btn.toggleClass("text-warning");
    $icon.toggleClass("bi-heart bi-heart-fill");

    // get the text node that holds the count (if any)
    var textNode = $btn.contents().filter(function () { return this.nodeType === 3; }).first();
    var count = 0;

    if (textNode.length) {
        var txt = textNode[0].nodeValue.trim();
        var m = txt.match(/\d+/);
        count = m ? parseInt(m[0], 10) : 0;
        count = Math.max(0, count + (wasLiked ? -1 : 1));
        textNode[0].nodeValue = " " + count;
    } else {
        // no count present yet -> create one
        count = wasLiked ? 0 : 1;
        $btn.append(" " + count);
    }
});
// share button functionality
$(".share").click(function (e) {
    e.preventDefault();
    var $btn = $(this);
    var wasshare = $btn.hasClass("text-warning");
    $btn.toggleClass("text-warning");

    var $post = $btn.closest(".post");
    var text = $post.find(".post-content").text().trim();

    navigator.clipboard.writeText(text).then(() => alert("Post copied to clipboard!"))

    var textNode = $btn.contents().filter(function () {
        return this.nodeType === 3;
    }).first();

    var count = 0;
    if (textNode.length) {
        var txt = textNode[0].nodeValue.trim();
        var m = txt.match(/\d+/);
        count = m ? parseInt(m[0], 10) : 0;
        count = Math.max(0, count + (wasshare ? -1 : 1));
        textNode[0].nodeValue = " " + count;
    } else {
        count = wasshare ? 0 : 1;
        $btn.append(" " + count);
    }
});

// retweet button functionality
$(".retweet").click(function (e) {
    e.preventDefault();
    var $btn = $(this);
    var $icon = $btn.find("i");

    var wasshare = $btn.hasClass("text-warning");
    $btn.toggleClass("text-warning");
    // rotate icon a full cycle
    $icon.removeClass('rotate');
    void $icon[0].offsetWidth; // force reflow
    $icon.addClass('rotate');

    // get the text node that holds the count (if any)
    var textNode = $btn.contents().filter(function () { return this.nodeType === 3; }).first();
    var count = 0;

    if (textNode.length) {
        var txt = textNode[0].nodeValue.trim();
        var m = txt.match(/\d+/);
        count = m ? parseInt(m[0], 10) : 0;
        count = Math.max(0, count + (wasshare ? -1 : 1));
        textNode[0].nodeValue = " " + count;
    } else {
        // no count present yet -> create one
        count = wasshare ? 0 : 1;
        $btn.append(" " + count);
    }

});

// Display relative time for posts
const current_time = new Date(time_now);
$(".post-heading small").each(function () {
    const post_time_str = $(this).text();  // Example: "2025-10-30T13:55:00"
    const post_time = new Date(post_time_str);
    const diffMs = current_time - post_time;
    const diffMins = Math.floor(diffMs / 60000);

    let display = "";

    if (diffMins < 1) {
        display = "Just now";
    } else if (diffMins < 60) {
        display = diffMins + " min ago";
    } else if (diffMins < 1440) {
        display = Math.floor(diffMins / 60) + "h ago";
    } else if (diffMins < 43200) {
        display = Math.floor(diffMins / 1440) + "d ago";
    } else if (diffMins < 525600) {
        display = Math.floor(diffMins / 43200) + "m ago";
    } else {
        display = Math.floor(diffMins / 525600) + "y ago";
    }

    $(this).text(display);
});

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
    $(".div4 input").val(JSON.stringify(post_info));
    post_info = {
        post_id: [],
        likes: [],
        shares: [],
        retweets: []
    };
});


$(".post-button").click(function () {
    $("textarea").focus();
});

$(".explore-button").click(function () {
    $(".search input").focus();
});


$(".full-post").hide();

$(".post").dblclick(function () {
    var $post = $(this);
    var post_id = $post.find('.post-heading h5').attr("class");
    var active_post = $post.hasClass("active-post");

    $(".post").removeClass("active-post");

    if (!active_post) {
        $post.addClass("active-post");
        $(".explore-tab").hide();

        // Get user name
        const userName = $post.find('.post-heading h5').clone().children().remove().end().text().trim();
        // Get username (@username inside span)
        const userHandle = $post.find('.post-heading h5 span').text().trim().replace(/^@/, '');
        // Get timestamp
        const timestamp = $post.find('.post-heading small').text().trim();
        const like = $post.find('.like').text().trim();
        const shares = $post.find('.share').text().trim();
        const comment = $post.find('.comment').text().trim();
        const retweet = $post.find('.retweet').text().trim();
        const content = $post.find('.post-content p').text().trim();

        // Fill in post data dynamically
        $(".commmentpost-action .likes span").text(like);
        $(".commmentpost-action .comments span").text(comment);
        $(".commmentpost-action .retweets span").text(retweet);
        $(".commmentpost-action .shares span").text(shares);

        // Fixed invalid selector $(".4") — use .full-post or specific container
        $(".full-post .post-heading h5").html(`${userName}<br><span>@${userHandle}</span>`);
        $(".full-post .post-heading small").text(timestamp);
        $(".full-post .post-content p").text(content);

        $(".full-post").show();
        $('.all-comments').load('/comments/' + post_id);
    } else {
        $post.removeClass("active-post");
        $(".explore-tab").show();
        $(".full-post").hide();
    }
});
