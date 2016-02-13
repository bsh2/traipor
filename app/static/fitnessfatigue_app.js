var main = function() {

  $('#calc_button').click(function() {
    $("#plan").val($("#plan").val().trim());
    $("#plan").val(remove_trailing_char($("#plan").val(), ","));
    var parameter_ids = ["initial_p", "k_1", "tau_1", "k_2", "tau_2"];
    var val1 = validate_parameter_inputs(parameter_ids);
    var val2 = validate_plan_inputs();
    if (!val1 || !val2)
      return false;

    var ff_parms = new Map();
    ff_parms['initial_p'] = Number($("#initial_p").val());
    ff_parms['k_1'] = Number($("#k_1").val());
    ff_parms['tau_1'] = Number($("#tau_1").val());
    ff_parms['k_2'] = Number($("#k_2").val());
    ff_parms['tau_2'] = Number($("#tau_2").val());

    var plan_loads = $('#plan').val().trim();
    plan_loads = plan_loads.split(',').map(Number);

    var pe = after_plan(plan_loads, ff_parms);
    var res = performance_timeline(plan_loads, ff_parms);
    var p_development = res[0];
    var fit_development = res[1];
    var fat_development = res[2];
    $('#afterplanperformance').text('performance after plan: ' + pe);

    var planperfplot = $.jqplot('perf_and_plan_plot', [p_development, fit_development, fat_development, plan_loads], {
      series: [
        { label: 'modeled performance' },
        { label: 'modeled fitness',
          yaxis: 'y3axis' },
        { label: 'modeled fatigue',
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
        y3axis: { label: "modeled fitness and fatigue",
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
