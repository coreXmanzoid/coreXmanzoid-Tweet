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