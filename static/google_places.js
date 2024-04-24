
    var google_api_key = "{{google_api_key|safe}}";

    document.addEventListener("DOMContentLoaded", function() {
        const googleAPIKey = google_api_key;

        const script = document.createElement("script");
        script.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyAvPU31yECwIIMNsiv8YKZiZB9WGWFLQE4&libraries=places&callback=initAutoComplete`;
        document.head.appendChild(script);
    });

    let autocomplete;

    function initAutoComplete() {
        autocomplete = new google.maps.places.Autocomplete(
            document.getElementById('id-google-address'),
            {
                types: 'geocode|address|establishment',
                componentRestrictions: { 'country': ['uk'] },
            });

        autocomplete.addListener('place_changed', onPlaceChanged);
    }

    function onPlaceChanged() {
    var place = autocomplete.getPlace();

    if (!place.geometry) {
        document.getElementById('id-google-address').placeholder = "*Begin typing address";
    } else {
        // Extract and fill address components
        var num = '';
        var addy = '';
        for (var i = 0; i < place.address_components.length; i++) {
            for (var j = 0; j < place.address_components[i].types.length; j++) {
                if (place.address_components[i].types[j] == "street_number") {
                    num = place.address_components[i].long_name;
                }
                if (place.address_components[i].types[j] == "route") {
                    addy = place.address_components[i].long_name;
                }
                if (place.address_components[i].types[j] == "postal_town") {
                    $('#id_town').val(place.address_components[i].long_name);
                }
                if (place.address_components[i].types[j] == "postal_code") {
                    $('#id_post_code').val(place.address_components[i].long_name);
                }
            }
        }

        $('#id_address').val(num + " " + addy);

        // Set the value of the location field
        $('#id_location').val(place.formatted_address);

        // Find all hidden inputs & ignore csrf token
        var x = $("input:hidden");
        for (let i = 0; i < x.length; i++) {
            if (x[i].name != "csrfmiddlewaretoken") {
                x[i].type = "text";
                x.eq(x).attr("class", 'hidden-el');
            }
        }

        // Fade in the completed form
        $('.hidden-el').fadeIn();

        // Enable submit button
        $('#profile-btn').removeAttr("disabled");
    }
}
