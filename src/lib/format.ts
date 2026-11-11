/**
 * Zahlenformat der Website: Punkt als Tausendertrennzeichen, Komma als
 * Dezimaltrennzeichen — 8.383.809 ha, 4.064 Flächen, 52,5 TWh.
 *
 * Bewusst `de-DE` und nicht `de-AT`: beide schreiben das Dezimalkomma, aber
 * `de-AT` gruppiert nach CLDR mit einem schmalen geschützten Leerzeichen.
 * Dadurch stand auf der Startseite "8 383 809 ha" neben "1.200 Metern" im
 * Fließtext — zwei Schreibweisen derselben Sache auf einer Seite. Der
 * gesamte redaktionelle Text schreibt Punkte, also tun es die berechneten
 * Zahlen jetzt auch.
 */
const CACHE = new Map<number, Intl.NumberFormat>();

export function fmtNumber(n: number, maximumFractionDigits = 0): string {
	let f = CACHE.get(maximumFractionDigits);
	if (!f) {
		f = new Intl.NumberFormat('de-DE', { maximumFractionDigits });
		CACHE.set(maximumFractionDigits, f);
	}
	return f.format(n);
}
