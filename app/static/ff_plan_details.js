var main = function() {
  var res = performance_timeline(plan_since_initial_p, model_parms);
  var p_development = res[0];
  var fit_development = res[1];
  var fat_development = res[2];
  // slice off the prequel plan
  p_development = p_development.slice(-plan_loads.length);
  fit_development = fit_development.slice(-plan_loads.length);
  fat_development = fat_development.slice(-plan_loads.length);

  var planperfplot = $.jqplot('perf_and_plan_plot', [p_development, fit_development, fat_development, plan_loads], {
    series: [
      { label: 'modeled performance', },
      { label: 'modeled fitness',
	yaxis: 'y3axis',      
      },
      { label: 'modeled fatigue',
        yaxis: 'y3axis',
      },
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
