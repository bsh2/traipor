var pp_parms2 = new Map();
pp_parms2['strainpot'] = 0.0;
pp_parms2['responsepot'] = 0.0;
pp_parms2['perfpot'] = 0.0;
pp_parms2['straindelay'] = 6.8;
pp_parms2['responsedelay'] = 6.3;
pp_parms2['overflowdelay'] = 0.0;

var w = [0.05, 0.05, 0.05, 0.0, 0.05, 0.05, 0.0,
         0.05, 0.05, 0.05, 0.0, 0.05, 0.00, 0.0];

function pp_test() {
	alert(after_plan(w, pp_parms2));
	alert(performance_timeline(w, pp_parms2));
}

function performance_timeline(w, params) {
	var sp = params['strainpot'];
	var rp = params['responsepot'];
	var pp = params['perfpot'];
	var ds = params['straindelay'];
	var dr = params['responsedelay'];
	var dso = params['overflowdelay'];
	var sr, rr, or;
	var response_pots = [w.length];
	var strain_pots = [w.length];
	var perf_pots = [w.length];

	for (var i = 0; i < w.length; i++) {
		sp = sp + w[i];
		rp = rp + w[i];

		sr = calc_strainrate(sp, pp, ds);
		rr = calc_responserate(rp, pp, dr);
		if (dso !== 0)
			or = calc_overflowrate(sp, dso);
		else
			or = 0.0;

		sp = sp - sr -or;
		rp = rp - rr;
		pp = pp + rr - sr - or;
		pp = Math.max(0, pp);
		response_pots[i] = rp;
		strain_pots[i] = sp;
		perf_pots[i] = pp;
	}

	return [perf_pots, response_pots, strain_pots];
}

function after_plan(w, params) {
	var e = performance_timeline(w, params);
	var r = e[0];
	return r[w.length -1];
}

function calc_strainrate(strainpot, perfpot, straindelay) {
	return Math.min(Math.min(1, strainpot), Math.max(0, perfpot)) / straindelay;
}

function calc_responserate(responsepot, perfpot, responsedelay) {
	return Math.min(Math.min(1, responsepot), Math.min(1, 1 - perfpot)) / responsedelay;
}

function calc_overflowrate(strainpot, overflowdelay) {
	return Math.max(0, strainpot - 1) / overflowdelay;
}
