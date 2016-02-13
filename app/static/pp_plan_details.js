var main = function() {
  var res = performance_timeline(plan_since_initial_p, model_parms);
  var p_development = res[0];
  var response_development = res[1];
  var strain_development = res[2];
  // slice off the prequel plan
  p_development = p_development.slice(-plan_loads.length);
  response_development = response_development.slice(-plan_loads.length);
  strain_development = strain_development.slice(-plan_loads.length);

  // scale perf and load values
  var fac = 1/perf_scale_factor;
  p_development = p_development.map(function(x) { return x * fac; });
  fac = 1/load_scale_factor;
  plan_loads = plan_loads.map(function(x) { return x * fac;});

  var planperfplot = $.jqplot('perf_and_plan_plot', [p_development, response_development, strain_development, plan_loads], {
    series: [
      { label: 'modeled performance', },
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

  $('#de_button').click(function() {
    var element = document.getElementById("plan_note");
    element.innerHTML = german_note;
  });
}

$(document).ready(main);
