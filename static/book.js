$(document).ready(function() {
    tmp = null;
    $(".available").on("click", function() {
        $(this).addClass("reserved").removeClass("available")
        seatNumber = $(this).text()

        if (tmp) {
            tmp.removeClass("reserved").addClass("available")
        }

        // keep track of which seat selected
        tmp = $(this)

        $("#book-seat").val(seatNumber)
    })
})