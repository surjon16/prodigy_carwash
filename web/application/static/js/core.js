
$.ajaxSetup({
    headers: {
        'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
    }
});

var setSideBar = function(element) {
    $('[id^="menu-"]').removeClass('active');
    $(element).addClass('active');
}
var setSideBarTitle = function(element, _title) {
    $(element+"-title").text(_title);
}

var Controller = {
    GET: function (_url, _data) {
        return $.ajax({
            url: _url,
            type: 'GET',
            data: _data,
            dataType: 'json',
            cache: false,
            complete: function () {}
        });
    },
    POST: function (_url, _data) {
        return $.ajax({
            url: _url,
            type: 'POST',
            data: _data,
            dataType: 'json',
            cache: false,
            complete: function () {}
        });
    }
}