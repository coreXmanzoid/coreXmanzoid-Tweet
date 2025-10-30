$(".nav li a").click(function () {
    $(".nav a").removeClass("active link-dark");
    $(".nav a").addClass("link-dark");
    $(this).addClass("active");
    $(this).removeClass("link-dark");
});
$(".footer-navbar a").click(function () {
    $(".footer-navbar a").removeClass("icons");
    $(this).addClass("icons");
});

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
$(".div2 a").click(function () {
    $(".div2 a").removeClass("active-a");
    $(this).addClass("active-a");
});
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
$(".div2 a").click(function () {
    $(".div2 a").removeClass("active-a");
    $(this).addClass("active-a");
});
$(".like").click(function (e) {
    e.preventDefault();
    var $btn = $(this);
    var $icon = $btn.find("i");
    var wasLiked = $icon.hasClass("bi-heart-fill");

    // toggle heart icon
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