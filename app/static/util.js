var plan_pattern = /^(\d+(\.\d+)?){1}(,\s*\d+(\.\d+)?){0,}$/;
var parameter_pattern = /^(\d+(\.\d+)?){1}$/;

var validate_plan_inputs = function() {
	if (!plan_pattern.test($("#plan").val())) {
		$("#plan_span").text("invalid input format").show().fadeOut(3000);
		return false;
	} else
		return true;
}

var remove_trailing_char = function(str, c) {
	if (str.endsWith(c))
		return str.slice(0, str.length - 1);
	else
		return str;
}

var validate_parameter_inputs = function(parameter_ids) {
  var r = true;
	var tests = parameter_ids.map(function(id) {
		var test = parameter_pattern.test($("#" + id).val());
		if (test == false)
			$("#" + id + "_span").text("invalid input format").show().fadeOut(3000);
		return test;
	});

	return (tests.indexOf(false) == -1);
}
