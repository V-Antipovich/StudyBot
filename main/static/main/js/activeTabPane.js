$(function($){
	var storage = document.cookie.match(/nav-tabs=(.+?);/);


	if (storage && storage[1] !== "#") {
		$('.nav-tabs a[href="' + storage[1] + '"]').tab('show');
	}

	$('ul.nav li').on('click', function() {
		var id = $(this).find('a').attr('href');
		document.cookie = 'nav-tabs=' + id;
	});
});