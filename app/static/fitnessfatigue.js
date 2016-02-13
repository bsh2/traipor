var ff_parms1 = new Map();
ff_parms1['initial_p'] = 0.1;
ff_parms1['k_1'] = 0.242;
ff_parms1['tau_1'] = 45.2;
ff_parms1['k_2'] = 0.372;
ff_parms1['tau_2'] = 11.3;

var w = [0.05, 0.05, 0.05, 0.0, 0.05, 0.05, 0.0,
         0.05, 0.05, 0.05, 0.0, 0.05, 0.00, 0.0];

function ff_test() {
	alert(after_plan(w, ff_parms1));
	alert(performance_timeline(w, ff_parms1));
}

function performance_timeline(w, params) {
	var perf_line = [w.length];
	var fit_line = [w.length];
	var fat_line = [w.length];
	for(i = 1; i <= w.length; i++) {
		g_val = params['k_1'] * g(i, params['tau_1'], w);
		h_val = params['k_2'] * h(i, params['tau_2'], w);
		var p_val = params['initial_p'] + g_val - h_val;
		perf_line[i-1] = Math.max(p_val, 0.0); 
		fit_line[i-1] = Math.max(g_val, 0.0); 
		fat_line[i-1] = Math.max(h_val, 0.0); 
	}
	return [perf_line, fit_line, fat_line];
}

function after_plan(w, params) {
	return p(w.length, w, params['initial_p'], params['k_1'],
		       params['tau_1'], params['k_2'], params['tau_2']);
}

function p(t, w, initial_p, k_1, tau_1, k_2, tau_2) {
	var p_val = initial_p + k_1 * g(t, tau_1, w) - k_2 * h(t, tau_2, w);
	return(Math.max(p_val, 0.0));
}

function g(n, tau_1, w) {
	var s = 0.0;
	for(i = 1; i <= n-1; i++) {
		s += w[i-1] * Math.exp((-(n-i))/tau_1);
	}
	return s;
}

function h(n, tau_2, w) {
	var s = 0.0;
	for(i = 1; i <= n-1; i++) {
		s += w[i-1] * Math.exp((-(n-i))/tau_2);
	}
	return s;
}
