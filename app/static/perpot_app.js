function validate_delay_inputs(delay_value, delay_id) {
	if (delay_value <= 0.0) {
		$('#' + delay_id + '_span').text('must be > 0.0').show().fadeOut(3000);
		return false;
	} else
		return true;
}

var main = function() {

  $('#calc_button').click(function() {
    var parameter_ids = ['sp', 'rp', 'pp', 'ds', 'dr', 'dso', 'load_scale_factor', 'perf_scale_factor'];
    var val1 = validate_parameter_inputs(parameter_ids);
    $("#plan").val($("#plan").val().trim());
    $("#plan").val(remove_trailing_char($("#plan").val(), ","));
    var val2 = validate_plan_inputs();
    if (!val1 || !val2)
      return false;

    var pp_parms = new Map();
    pp_parms['strainpot'] = Number($('#sp').val());
    pp_parms['responsepot'] = Number($('#rp').val());
    pp_parms['perfpot'] = Number($('#pp').val());
    pp_parms['straindelay'] = Number($('#ds').val());
    pp_parms['responsedelay'] = Number($('#dr').val());
    pp_parms['overflowdelay'] = Number($('#dso').val());

    var load_scale_factor = Number($('#load_scale_factor').val());
    var perf_scale_factor = Number($('#perf_scale_factor').val());
    var perf_unscale_factor = 1 / perf_scale_factor;

    val1 = validate_delay_inputs(pp_parms['straindelay'], 'ds');
    val2 = validate_delay_inputs(pp_parms['responsedelay'], 'dr');
    if (!val1 || !val2)
      return false;

    var unscaled_plan_loads = $('#plan').val().trim();
    unscaled_plan_loads = unscaled_plan_loads.split(',').map(Number);
    var plan_loads = unscaled_plan_loads.map(function(x) { return x * load_scale_factor; });

    var pe = after_plan(plan_loads, pp_parms);
    pe = pe * perf_unscale_factor;
    var res = performance_timeline(plan_loads, pp_parms);
    var p_development = res[0];
    p_development = p_development.map(function(x) { return x * perf_unscale_factor; });
    var response_development = res[1];
    var strain_development = res[2];
    $('#afterplanperformance').text('performance after plan: ' + pe);

    var planperfplot = $.jqplot('perf_and_plan_plot', [p_development, response_development, strain_development, unscaled_plan_loads], {
      series: [
        { label: 'modeled performance' },
        { label: 'modeled response',
          yaxis: 'y3axis' },
        { label: 'modeled strain',
          yaxis: 'y3axis' },
        { label: 'training load',
	  yaxis: 'y2axis',      
	  renderer: $.jqplot.BarRenderer,
          rendererOptions: { shadowOffset: 0,
	                     barWidth: 2,
			     barPadding: -2,
                             fillToZero: true }
        }
      ],	    
      axesDefaults: {
        labelRenderer: $.jqplot.CanvasAxisLabelRenderer
      },
      axes: {
        xaxis: { label: "time (in days)",
		 min: 0,
                 autoscale: true },
        yaxis: { label: "modeled performance",
		 min: 0,
                 autoscale: true },
        y2axis: { label: "training load",
		  min: 0,
                  autoscale: true },
        y3axis: { label: "modeled response and strain",
		  min: 0,
                  autoscale: true },
      },
      legend: { show: true,
                location: 'nw' }
    });
    planperfplot.replot();

    return false;
  });
}
  
$(document).ready(main);
