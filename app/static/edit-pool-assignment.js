$( function() {
	$( "#sortable" ).sortable({
		connectWith: ".connectedSortable"
	}).disableSelection();
} );

var form;

form.onsubmit = function(e) {
	e.preventDefault();
	var data = {};
	$("#sortable").each(function(i) {
		data[i] = this.sortable('toArray');
	});
	var xhr = new XMLHttpRequest();
	xhr.open(form.method, form.action, true);
	xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
	xhr.send(JSON.stringify(data));
};

function randomizeInPools() {
	
};

function randomizeAllPools() {
	
};