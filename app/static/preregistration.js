function validate() {
    var regex = RegExp('([a-zA-Z]{1,32} [a-zA-z]{1,32}){0,1}');
    var elements = document.getElementById('preregistration').elements;
    for(var i = 0, element; element = elements[i++];) {
        if(element.type === "text" && !element.disabled && !regex.test(element.value)) {
            alert(element.name);
            return false;
        }
    }
    return true;
}
jQuery(document).ready(function () {
    $(':text').attr('disabled', true);
    $('#Foil_A_slider').click(function () {
        $('[id^=Foil_A-fencer]').attr("disabled", !$(this).is(":checked"));
    });
    $('#Foil_B_slider').click(function () {
        $('[id^=Foil_B-fencer]').attr("disabled", !$(this).is(":checked"));
    });
    $('#Epee_A_slider').click(function () {
        $('[id^=Epee_A-fencer]').attr("disabled", !$(this).is(":checked"));
    });
    $('#Epee_B_slider').click(function () {
        $('[id^=Epee_B-fencer]').attr("disabled", !$(this).is(":checked"));
    });
    $('#Saber_A_slider').click(function () {
        $('[id^=Saber_A-fencer]').attr("disabled", !$(this).is(":checked"));
    });
    $('#Saber_B_slider').click(function () {
        $('[id^=Saber_B-fencer]').attr("disabled", !$(this).is(":checked"));
    });
});
