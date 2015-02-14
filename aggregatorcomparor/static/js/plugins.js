// place any jQuery/helper plugins in here, instead of separate, slower script files.
$(document).ready(function() {

    $("input.name-lookup").typeahead({
        source: function(typeahead, query) {
            $.ajax({
                url: window.location,
                data: {name: query, format: 'json'},
                dataType: 'json',
                success: function(data) {
                    typeahead.process(data);
                }
            })
        },
        selected: function(a, b, c) {
            $("form.name-lookup").submit();
        }
    });
});
